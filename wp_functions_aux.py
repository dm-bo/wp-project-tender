import sys
import re
import datetime
import time # for sleep
import ast # for str to dict
import dateutil.parser  # pip install python-dateutil
import requests

from config import get_tender_config

script_config = get_tender_config()

def normalize_link(link):
    """
    To fix internal links.
    Removes everything that can interfere link processing:
      #something
      {{nbsp}}
      <noinclude>
    """
    if link == "":
        return ""
    normalized_link = link[0].upper() + link[1:]
    normalized_link = normalized_link.replace(" "," ").replace("  "," ").replace("_"," ").strip()
    normalized_link = re.sub("#.*$","", normalized_link)
    # if not link == normalized_link:
        # print(f"{link} normalized to {normalized_link}")
    return normalized_link

def find_redirect_in_content(content):
    """
    Searches something like
    #Перенаправление [[Ленин, Владимир Ильич]]
    in given text. If no, returns "" (empty string)
    """
    pattern = re.compile(r"#перенаправление\s*\[\[(.*?)\]\]", re.IGNORECASE)
    m = pattern.search(content)
    if m:
        return m.group(1)
    pattern2 = re.compile(r"#REDIRECT\s*\[\[(.*?)\]\]", re.IGNORECASE)
    n = pattern2.search(content)
    if n:
        return n.group(1)
    return ""

def get_wp_page_content(params):
    """
    Returns raw data of bunch of pages.
    Deals with HTTP errors.
    """
    limit = 3
    i = 0
    sleep_timeout = 10
    while i < limit:
        i += 1
        session = requests.Session()
        try:
            response = session.get(
                url=script_config["api_url"],
                params=params,
                headers=script_config["headers"]
            )
        except:
            print(f"Error getting page ({i}), waiting {sleep_timeout} seconds...")
            print("..........")
            time.sleep(sleep_timeout)
            continue
        if response.status_code == 200:
            return response
        if response.status_code == 414:
            print(f"URI too long! ({len(params["titles"])})")
            print(params["titles"])
            sys.exit(414)
        print(f"Got responce {response.status_code}, waiting {sleep_timeout} secs and retry...")
        print("..........")
        time.sleep(sleep_timeout)
    return False

def structure_page_data(page_data):
    flagged_date = "1970-01-01"
    if not 'flagged' in page_data:
        flagged = "never"
    elif 'pending_since' in page_data['flagged']:
        #flagged_date = dateutil.parser.isoparse(page_data['flagged']['pending_since'])
        flagged_date = page_data['flagged']['pending_since']
        flagged = "old"
    else:
        flagged = "current"
    content = ""
    if "revisions" in page_data:
        content = page_data['revisions'][0]['slots']['main']['content']
    categories = []
    if "categories" in page_data:
        for cat in page_data["categories"]:
            categories.append(cat["title"])
    missing = "missing" in page_data
    redirects_to = find_redirect_in_content(content)
    return {
      "title": page_data["title"],
      "content": content,
      "categories": categories,
      "flagged": flagged,
      "flagged_date": flagged_date,
      "redirects_to": redirects_to,
      "missing": missing
    }

def get_wp_content(titles,r):
    """
    Returns structured data of bunch of articles from web.
    Writes structured JSON to Redis cache.
    Knows about missng pages and flagged revisions (not yet).
    Level 1 wrapper for get_wp_page_content.
    Lays between get_wp_pages_content and get_wp_page_content (!)
    """
    #get_wp_page_content(params)
    REQ_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "flagged|revisions|categories",
        "formatversion": 2,
        "rvprop": "content",
        "rvslots": "*",
        "titles": '|'.join(titles) #.replace("&","%26").replace("/","%2F")
    }
    # print(REQ_PARAMS['titles'])
    response = get_wp_page_content(REQ_PARAMS)
    try:
        paginas = response.json()['query']['pages']
    except:
        print(f"!!! Can't get paginas from response! Params: {REQ_PARAMS}")
        print(response)
        print(response.json())
        sys.exit(404)
    # Converting to own-structured JSON and cache it
    structured_pages = []
    for pagina in paginas:
        structured_page = structure_page_data(pagina)
        if len(str(structured_page)) > script_config["LEN_CACHE_NOTICE"]:
            print("<<<".ljust(12) + \
                f"Going to cache data sized {round(len(str(structured_page))/1024,0)}k")
        r.setex(f"page:content:{structured_page['title']}",
            datetime.timedelta(hours=script_config["cache_content_ttl"]),
            value=str(structured_page)
            )
        structured_pages.append(structured_page)
    #return paginas
    return structured_pages

def get_wp_content_cached(titles,r,verbose=True):
    """
    Returns summarized pages (structured JSON) both from cache and web requests.
    Deals with cache. Deals with batch size.
    Level 1 wrapper for get_wp_articles_content. Level 2 wrapper for get_wp_page_content.
    """
    need_web_request = []
    # just for statistics
    j, j_red = 0,0
    for title in titles:
        j = j + 1
        n_title = normalize_link(title)
        # double Redis requests but nobody cares
        red_cached = r.get(f"page:content:{n_title}")
        if not red_cached:
            # print(f"Will request web content for {title}")
            need_web_request.append(n_title)
        elif re.search(r"Проект\:", n_title):
            print(f"Will request web content for {n_title} (cache omitted)")
            need_web_request.append(n_title)
        else:
            j_red = j_red + 1
        if verbose:
            print("web-cache".ljust(12) + "Pages processed so far:", j, f"of {len(titles)},",
                f"web requests planned: {len(need_web_request)},",
                f"cache hits: {j_red} ({round(100*j_red/max(j,1),1)}%",
                f"so far, {round(100*j_red/len(titles),1)}% total)")
    i = 0
    batch_titles = []
    # print("so we have need_web_request:")
    # print(need_web_request)
    for title in need_web_request:
        n_title = normalize_link(title)
        batch_titles.append(n_title)
        i = i + 1
        if i == len(need_web_request) or \
          len(batch_titles) == script_config["API_BATCH_SIZE"] or \
          len('|'.join(batch_titles)) > script_config["URI_LENGTH_REDLINE"]:
            dont_need_this_var = get_wp_content(batch_titles,r)
            if verbose:
                print("web-http".ljust(12) + \
                  f"Page really requested: {i} of planned {len(need_web_request)} " + \
                  f"(batch {len(batch_titles)}, URI len {len('|'.join(batch_titles))})")
            batch_titles = []

    # Now every page must be in cache, so we take everything from cache
    # FIXME not reliable, we need dont_need_this_var
    result = []
    for title in titles:
        normal_title = normalize_link(title)
        red_cached = r.get(f"page:content:{normal_title}")
        if red_cached:
            next_result = ast.literal_eval(red_cached)
            next_result["flagged_date"] = datetime.datetime.fromisoformat(next_result["flagged_date"])
            result.append(next_result)
        else:
            print(f"OMG! OMG! Cunt get cached content for {normal_title}!")
    # Last man's check
    if not len(titles) == len(result):
        print(f"FATAL: argument length ({len(titles)}) doesn't match with result length ({len(result)}) !")
    return result

def print_http_response(response):
    """
    Just to print http response more verbose
    """
    print(response)
    print("Статус-код:", response.status_code)
    print("Заголовки:", response.headers)
    print("Тело ответа:", response.text)
    print("URL:", response.url)
    print("Cookies:", response.cookies)
    print("История редиректов:", response.history)
    print("Cannot get response!")

# gets template name
# returns array of page names
def get_wp_pages_by_template(template, namespace):
    INIT_PARAMS = {
        "action": "query",
        "titles": template,
        "prop": "transcludedin",
        "format": "json",
        "tilimit": 500,
        "tinamespace": namespace
    }
    session = requests.Session()
    result = []
    have_data_to_get = True
    run_params = INIT_PARAMS
    while have_data_to_get:
        response = session.get(url=script_config["api_url"], params=run_params, headers=script_config["headers"])
        try:
            pages_dict = response.json()['query']["pages"]
        except:
            print_http_response(response)
            sys.exit(4)
        transcluded_objs = pages_dict[list(pages_dict)[0]]['transcludedin']
        # res = [ sub['gfg'] for sub in test_list ]
        for ti in transcluded_objs:
            result.append(ti['title'].replace('Обсуждение:',''))
        if 'continue' in response.json().keys():
            print(f"Let's continue getting by template {template}! {len(result)} so far.")
            # print(response.json()['continue'])
            run_params = dict(list(INIT_PARAMS.items()) + list(response.json()['continue'].items()))
            have_data_to_get = True
        else:
            have_data_to_get = False
    return sorted(result)

def get_wp_pages_by_category(category, namespace=1):
    """
    Returns all category members. Deals with API limit.
    Level 1 wrapper for get_wp_page_content.
    """
    PARAMS_0 = {
        "action": "query",
        "cmtitle": category,
        "list": "categorymembers",
        "format": "json",
        "cmlimit": 500
    }
    # session = requests.Session()
    result = []
    have_data_to_get = True
    params_1 = PARAMS_0
    while have_data_to_get:
        response = get_wp_page_content(params_1)
        for page in response.json()['query']['categorymembers']:
            if page['ns'] == namespace or \
              page['ns'] == 14:
                result.append(page['title'].replace('Обсуждение:',''))
        if 'continue' in response.json().keys():
            print(f"Let's continue getting by category {category}! {len(result)} so far.")
            # print(response.json()['continue'])
            params_1 = dict(list(PARAMS_0.items()) + list(response.json()['continue'].items()))
            have_data_to_get = True
        else:
            have_data_to_get = False
    return sorted(result)

def get_wp_pages_by_category_recurse(cats, cat_namespace=1):
    pages = []
    cats_done = {}
    pages_done = {}
    while cats:
        member_cats = []
        member_pages = []
        #next_cat = cats[0]
        next_cat = cats.pop(0)
        members = get_wp_pages_by_category(next_cat, cat_namespace)
        for member in members:
            if not re.search(r"^Категория:Портал:", member) and \
              not re.search(r"^Файл:", member):
                if re.search(r"^Категория:", member):
                    member_cats.append(member)
                else:
                    member_pages.append(member)
        for member in member_cats:
            if not member in cats_done:
                cats.append(member)
                cats_done[member] = True
        for member in member_pages:
            if not member in pages_done:
                pages.append(member)
                pages_done[member] = True
        cats_done[next_cat] = True
        # if len(pages) > 500:
            # break
    print(f"Totals: {len(pages)} pages found, {len(cats_done)} categories processed, " +
        f"{len(cats)} categories left.")
    return pages

def get_wp_pages_content(viet_pages,r,limit=100000):
    viet_pages_content = []
    viet_pages_not_patrolled = []
    viet_pages_old_patrolled = []

    paginas = get_wp_content_cached(viet_pages,r)
    for page in paginas:
        viet_pages_content.append({
            "title": page['title'],
            "content": page['content'],
            "categories": page['categories']
        })
        if page["flagged"] == "never":
            #print(f"{page["title"]} never")
            viet_pages_not_patrolled.append(page['title'])
        elif page["flagged"] == "current":
            #print(f"{page["title"]} current, no do")
            #
            pass
        else:
            #print(f"{page["title"]} old, numbah ten")
            viet_pages_old_patrolled.append({
                "title": page['title'],
                "date": page["flagged_date"]
            })

    # TODO rework patrolled stats
    viet_pages_content = sorted(viet_pages_content, key=lambda d: d['title'])
    viet_pages_not_patrolled = sorted(viet_pages_not_patrolled)
    viet_pages_old_patrolled = sorted(viet_pages_old_patrolled, key=lambda d: d['date'])
    return viet_pages_content, viet_pages_not_patrolled, viet_pages_old_patrolled

class OloloLink():
    def __init__(self, link="", page=""):
        self.link = link
        self.page = page
    def __repr__(self):
        return f'[[{self.link}]] ({self.page})'

def get_wp_internal_links(pages_content):
    """
    Build a big list of internal links (Ololo type) from a big list of pages content.
    """
    # TODO remove obsolete function
    links_ololo = []
    links_ololo_arr = []
    i = 0
    for page in pages_content:
        i += 1
        mc = re.findall(r"\[\[([^\|\]\:]*)[\|\]]", page['content'])
        if mc:
            for m in mc:
                links_ololo.append(OloloLink(m, page['title']))
                links_ololo_arr.append({'link': m, 'page': page['title']})
    return links_ololo

def get_wp_internal_links_flat(pages_content):
    """
    Build a big list of internal links (just links) from a big list of pages content.
    """
    result = []
    for page in pages_content:
        mc = re.findall(r"\[\[([^\|\]\:]*)[\|\]]", page['content'])
        for m in mc:
            result.append(m)
    return result

def get_wp_page_sections(content):
    """
    Get sections list (with content) from page wikitext.
    """
    section_contents = re.split(r"=[=]+[ ]*[^=]*[ ]*=[=]+", content)
    section_names = re.findall(r"(=[=]+)[ ]*([^=]*)[ ]*=[=]+", content)
    sections = [{
        'name': '(head)',
        'level': 1,
        'content': section_contents[0]
    }]
    for i in range(len(section_names)):
        sections.append({
            'name': section_names[i][1].strip(),
            'level': len(section_names[i][0]),
            'content': section_contents[i+1]
        })
    return sections

def get_date_format(date_str):
    """
    Returns if given string is a valid WP date
    """
    return re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}\:[0-9]{2}$", date_str) or \
      re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", date_str) or \
      re.search(r"^[0-9]{4}-[0-9]{2}$", date_str) or \
      re.search(r"^[0-9]{4}$", date_str) or \
      re.search(r"^$", date_str)

def get_wp_authentication_status(session):
    """
    Check if given session is authenticated.
    """
    PARAMS_0 = {
        "action": "query",
        "meta": "userinfo",
        "format": "json"
    }
    if not hasattr(session, 'get'):
        return False
    response = session.get(url=script_config["api_url"], params=PARAMS_0, headers=script_config["headers"])
    #print(response.json()['query']['userinfo'])
    if response.json()['query']['userinfo']['id']:
        return True
    return False

def get_wp_authenticated_session(login, password):
    """
    Takes login/pass and retursns authenticated sessions
    """
    session = requests.Session()
    PARAMS_1 = {
        'action': "query",
        'meta':   "tokens",
        'type':   "login",
        'format': "json"
    }
    response = session.get(url=script_config["api_url"], params=PARAMS_1, headers=script_config["headers"])
    # print(response.json()['query']['tokens'])
    try:
        login_token = response.json()['query']['tokens']['logintoken']
    except:
        print(response)
        print("Статус-код:", response.status_code)
        print("Заголовки:", response.headers)
        print("Тело ответа:", response.text)
        print("URL:", response.url)
        print("Cookies:", response.cookies)
        print("История редиректов:", response.history)
        print("Cannot get session!")
        exit(4)
    PARAMS_2 = {
        'action':     "login",
        'lgname':     login,
        'lgpassword': password,
        'lgtoken':    login_token,
        'format':     "json"
    }

    response = session.post(url=script_config["api_url"], data=PARAMS_2, headers=script_config["headers"])
    # print(response.json())
    if get_wp_authentication_status(session):
        return session
    return False

def set_wp_page_text(session, title, text, summary):
    """
    Replace wikitext of page. Entirely.
    """
    if not get_wp_authentication_status(session):
        print("Session is not authenticated! Aborting.")
        return False
    PARAMS_4 = {
        "action": "query",
        "meta":   "tokens",
        "format": "json"
    }
    response = session.get(url=script_config["api_url"], params=PARAMS_4,
        headers=script_config["headers"])
    csrf_token = response.json()['query']['tokens']['csrftoken']

    # POST request to edit a page
    PARAMS_5 = {
        "action":   "edit",
        "title":    title,
        "token":    csrf_token,
        "text":     text,
        "summary":  summary,
        "nocreate": 1,
        "format":   "json"
    }

    response = session.post(url=script_config["api_url"], data=PARAMS_5,
        headers=script_config["headers"])
    print(response.json())
    if response.json()['edit']['result'] == "Success":
        return True
    print(response.json()['edit'])
    return False

def parse_check_template(template_text,target_page):
    """
    Parse template text to dict
    """
    template_dict = {}
    mc2 = re.findall(r"\|([\-_ a-zA-Z0-9\n]*)\=([^\|}]*)", template_text)
    # just text parsing
    for m in mc2:
        template_dict[ m[0].strip() ] = m[1].strip()

    ### more smart data ###

    # cooldown things
    # last timestamp as datetime
    if 'timestamp' in template_dict.keys():
        template_dict["timestamp_date"] = dateutil.parser.parse(template_dict['timestamp'])
    else:
        template_dict["timestamp_date"] = datetime.datetime.fromtimestamp(0)
    # time_cooldown in days
    # is it okay to use "try" like this?..
    try:
        template_dict["time_cooldown"] = script_config["project"][target_page]["time_cooldown"]
    except KeyError:
        print("No specific time_cooldown found, using a default one.")
        template_dict["time_cooldown"] = script_config["time_cooldown"]
    # cooldown_threshold - when should check next time
    template_dict["cooldown_threshold"] = \
      template_dict["timestamp_date"] + datetime.timedelta(days=template_dict["time_cooldown"])
    # is it old enough
    if datetime.datetime.now() > template_dict["cooldown_threshold"]:
        template_dict["old_enough"] = True
    else:
        template_dict["old_enough"] = False

    # overdated_threshold - how many dates can be wikified
    try:
        template_dict["overdated_threshold"] = \
          script_config["project"][target_page]["overdated_threshold"]
    except KeyError:
        print("No specific overdated_threshold found, using a default one.")
        template_dict["overdated_threshold"] = script_config["overdated_threshold"]
    # TODO remove unnecessary timestamps
    return template_dict

def get_norefs_nolinks_content(viet_page_content):
    result = []
    # has_semi = False
    sections = get_wp_page_sections(viet_page_content)
    for section in sections:
        if not re.search(r"Литература|Примечания|Источники|Ссылки", section['name']):
            result.append("### " + section['name'] + " ###")
            result.append(section['content'])
    full_content = "\n\n".join(result)
    # рабочий вариант
    # почти: нужно (?m) или как-то так
    refs = re.findall(r"<ref[^\>\/]*\>.*?\<\/ref\>", full_content)
    for ref in refs:
        full_content = full_content.replace(ref, "")
    return full_content

def get_justtext_content(viet_page_content, debug=False):
    result = []
    sections = get_wp_page_sections(viet_page_content)
    for section in sections:
        if not re.search(r"Литература|Примечания|Источники|Ссылки|См. также", section['name']):
            result.append("### " + section['name'] + " ###")
            result.append(section['content'])
    full_content = "\n\n".join(result)
    # рабочий вариант, with multiline
    templ_ref = re.compile(r"<ref[^\>\/]*\>[\S\s]*?\<\/ref\>", re.MULTILINE)
    refs = re.findall(templ_ref, full_content)
    for ref in refs:
        full_content = full_content.replace(ref, "")
    # now remove templates, including nested
    templ_regex = re.compile(r"{{[^\{\}]*?}}", re.MULTILINE)
    #j = 0
    while re.findall("{{", full_content) and re.findall("}}", full_content):
        templs = re.findall(templ_regex, full_content)
        #j = j + 1
        #print(str(j) + " templates: " + str(len(templs)))
        if len(templs) == 0:
            #print()
            print("WARNING: cannot process text")
            #exit(1)
            return ""
        for templ in templs:
            full_content = full_content.replace(templ, "")
    if debug:
        return full_content, templs
    return full_content
