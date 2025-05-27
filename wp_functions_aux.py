import re
import datetime
import requests
import time # for sleep
import ast # for str to dict 
import dateutil.parser  # pip install python-dateutil

from config import get_tender_config

script_config = get_tender_config()

def get_wp_page_content(url,params):
    limit = 3
    i = 0
    sleep_timeout = 10
    while i < limit:
        i += 1
        session = requests.Session()
        try:
            response = session.get(url=url, params=params)
        except:
            print(f"Error getting page ({i}), waiting {sleep_timeout} seconds...")
            print("..........")
            time.sleep(sleep_timeout)
            continue
        if response.status_code == 200:
            return response
        else:
            print(f"Got responce {response.status_code}, waiting {sleep_timeout} seconds and retry...")
            print("..........")
            time.sleep(sleep_timeout)
    return False

# gets template name
# returns array of page names
def get_wp_pages_by_template(template, namespace):
    api_url = "http://ru.wikipedia.org/w/api.php"
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
    RUN_PARAMS = INIT_PARAMS
    while have_data_to_get:
        #time.sleep(3)
        response = session.get(url=api_url, params=RUN_PARAMS)
        pages_dict = response.json()['query']["pages"]
        # print(pages_dict, pages_dict)
        #first_set = list(pages_dict)[0]
        transcluded_objs = pages_dict[list(pages_dict)[0]]['transcludedin']
        # res = [ sub['gfg'] for sub in test_list ]
        for ti in transcluded_objs:
            result.append(ti['title'].replace('Обсуждение:',''))
        if 'continue' in response.json().keys():
            print("Let's continue!")
            print(response.json()['continue'])
            RUN_PARAMS = dict(list(INIT_PARAMS.items()) + list(response.json()['continue'].items()))
            have_data_to_get = True
        else:
            have_data_to_get = False
    return sorted(result)

def get_wp_pages_by_category(category, namespace=1):
    api_url = "http://ru.wikipedia.org/w/api.php"
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
    PARAMS_1 = PARAMS_0
    while have_data_to_get:
        # response = session.get(url=api_url, params=PARAMS_1)
        response = get_wp_page_content(api_url, PARAMS_1)
        # print(response.json())
        for page in response.json()['query']['categorymembers']:
            if page['ns'] == namespace or \
              page['ns'] == 14:
                #print(page)
                result.append(page['title'].replace('Обсуждение:',''))
        if 'continue' in response.json().keys():
            print("Let's continue!")
            print(response.json()['continue'])
            PARAMS_1 = dict(list(PARAMS_0.items()) + list(response.json()['continue'].items()))
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
        members_1 = []
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

def parse_page_data(page_data,pages_content,pages_old_pat,pages_not_pat):
    # if re.search(r"Постановление", page['title']):
        # print(page)
    if not 'flagged' in page_data.keys():
        pages_not_pat.append(page_data['title'])
    elif 'pending_since' in page_data['flagged'].keys():
        next_old_patrolled = {
            "title": page_data['title'],
            "date": dateutil.parser.isoparse(page_data['flagged']['pending_since'])
        }
        pages_old_pat.append(next_old_patrolled)
        #print("Old flagged", page['title'], '(since', str(date_patrolled), ')')
    else:
        pass
    # print(page)
    next_page =  {
        "title": page_data['title'],
        "content": page_data['revisions'][0]['slots']['main']['content']
    }
    pages_content.append(next_page)
    return pages_content,pages_old_pat,pages_not_pat

def get_wp_pages_content(viet_pages,r,limit=100000):
    batch_size = 10
    viet_pages_content = []
    viet_pages_not_patrolled = []
    viet_pages_old_patrolled = []

    # Redis
    ttl_hours = 96
    # internal list of pages to get from WP
    next_batch = []
    api_url = "http://ru.wikipedia.org/w/api.php"
    REQ_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "flagged|revisions",
        "formatversion": 2,
        "rvprop": "content",
        "rvslots": "*"
    }
    # session = requests.Session()
    j, j_web, j_red = 0, 0, 0
    for vp in viet_pages:
        j += 1
        #paginas = []
        if re.search(r"Проект\:", vp) or re.search(r"биография", vp):
            red_cached = False
        else:
            red_cached = r.get(f"page:content:{vp}")
        if red_cached:
            # if have Redis cache
            j_red += 1
            pagina1 = ast.literal_eval(red_cached)
            # print(f"  >>> Have redis cache for {vp} {len(pagina1['revisions'][0]['slots']['main']['content'])}")
            viet_pages_content, viet_pages_old_patrolled, viet_pages_not_patrolled = \
                parse_page_data(
                    pagina1,
                    viet_pages_content,
                    viet_pages_old_patrolled,
                    viet_pages_not_patrolled
                )
            
            # print(paginas)
        else:   
            # if no then  do business with HTTP
            j_web += 1
            next_batch.append(vp)
        if j > limit:
            # break if a huge limit is reached (millions)
            break
        if len(next_batch) == batch_size or (j == len(viet_pages) and len(next_batch) > 0):
            params_batch = REQ_PARAMS
            params_batch['titles'] = '|'.join(next_batch) #.replace("&","%26").replace("/","%2F")
            next_batch = []
            print(params_batch['titles'])
            # response = session.get(url=api_url, params=REQ_PARAMS)
            response = get_wp_page_content(api_url, REQ_PARAMS)
            try:
                paginas = response.json()['query']['pages']
            except:
                print("==== Can't get paginas from response! ====")
                print(f"Params: {params}")
                print(response.json())
                print(response.json()['query']['pages'])
                exit(404)
            for page in paginas:
                # check if something wrong
                if not type(paginas) == type([1, 2]):
                    print("WARNING! Type of paginas is not a list!")
                # cache it baby
                if len(str(page)) > 102400:
                    print(f"  <<< Going to cache data sized {round(len(str(page))/1024,0)}k")
                r.setex(f"page:content:{page['title']}", datetime.timedelta(hours=ttl_hours), value=str(page))   
                # add the pages we download
                viet_pages_content, viet_pages_old_patrolled, viet_pages_not_patrolled = \
                    parse_page_data(
                        page,
                        viet_pages_content,
                        viet_pages_old_patrolled,
                        viet_pages_not_patrolled
                    )  
        if j % 10 == 0 or j == 1 or j == len(viet_pages_content):
            print("Pages processed so far:", j, f"of {len(viet_pages)}",
                f"web requests: {j_web},",
                f"cache hits {j_red} ({round(100*j_red/max(len(viet_pages_content),1),1)}% so far, {round(100*j_red/len(viet_pages),1)}% total)")
    # TODO can be moved to the function
    viet_pages_content = sorted(viet_pages_content, key=lambda d: d['title'])
    viet_pages_not_patrolled = sorted(viet_pages_not_patrolled)
    viet_pages_old_patrolled = sorted(viet_pages_old_patrolled, key=lambda d: d['date'])
    if not j_red + j_web == j:
        print("CHECKSUM TILT!")
        exit(61)
    if not j_red + j_web == len(viet_pages_content):
        print("CHECKSUM TILT type 2!")
        exit(62)
    return viet_pages_content, viet_pages_not_patrolled, viet_pages_old_patrolled

class OloloLink():
    def __init__(self, link="", page=""):
        self.link = link
        self.page = page
    def __repr__(self):
        return f'[[{self.link}]] ({self.page})'

def get_wp_internal_links(viet_pages_content):
    """
    Build a big list of internal links from a big list of pages content.
    """
    links_ololo = []
    links_ololo_arr = []
    i = 0
    for page in viet_pages_content:
        #print("matching", page['title'])
        i += 1
        # TODO stuff about eastern name is skipped for now
        # if ($removeEasternNames){
            # # performange issue here
            # $content = $page.content -replace "{{Восточноазиатское имя[^}]{1,20}}}"
        # } else {
            # $content = $page.content
        # }
        mc = re.findall(r"\[\[([^\|\]\:]*)[\|\]]", page['content'])
        if mc:
            #print("Matched")
            for m in mc:
                links_ololo.append(OloloLink(m, page['title']))
                links_ololo_arr.append({'link': m, 'page': page['title']})
        #if divmod(i, 10)[1] == 0:
        #    print("Extracting wikilinks:", i, "/", len(viet_pages_content), "pages processed")
    return links_ololo
    #return links_Ololo_arr

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
    response = session.get(url=script_config["api_url"], params=PARAMS_0)
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
    response = session.get(url=script_config["api_url"], params=PARAMS_1)
    # print(response.json()['query']['tokens'])
    login_token = response.json()['query']['tokens']['logintoken']

    PARAMS_2 = {
        'action':     "login",
        'lgname':     login,
        'lgpassword': password,
        'lgtoken':    login_token,
        'format':     "json"
    }

    response = session.post(url=script_config["api_url"], data=PARAMS_2)
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
    response = session.get(url=script_config["api_url"], params=PARAMS_4)
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

    response = session.post(url=script_config["api_url"], data=PARAMS_5)
    print(response.json())
    if response.json()['edit']['result'] == "Success":
        return True
    print(response.json()['edit'])
    return False

def get_wp_categories(pagenames):
    """
    Get categories for pages.
    Can deal with API limit.
    """
    if not pagenames:
        return[]
    api_url = "http://ru.wikipedia.org/w/api.php"
    pagenames_batch = '|'.join(pagenames)
    # TODO change 500 to MAXLIMIT
    PARAMS_0 = {
        'action': "query",
        'formatversion':   2,
        'prop':   "categories",
        'cllimit': 500,
        'titles': pagenames_batch,
        'format': "json"
    }
    # session = requests.Session()
    result_dict = {}
    result = []
    have_data_to_get = True
    pages_missing = []
    PARAMS_1 = PARAMS_0
    while have_data_to_get:
        cat_len_tot = 0
        #time.sleep(3)
        # response = session.get(url=api_url, params=PARAMS_1)
        response = get_wp_page_content(api_url, PARAMS_1)
        try:
            pages_dict = response.json()['query']["pages"]
        except:
            print("OMG! OMG!")
            print(pagenames_batch, "len:", len(pagenames_batch))
            print(response)
            print(type(response))
            print(response.json())
        #first_set = list(pages_dict)[0]
        #print(pages_dict)
        for page in response.json()['query']["pages"]:
            # print("===", page['title'], "===")
            if not page['title'] in result_dict:
                result_dict[page['title']] = []
            if 'categories' in page.keys():
                for cat in page['categories']:
                    # print(cat['title'])
                    result_dict[page['title']].append(cat['title'])
                cat_len = len(page['categories'])
                cat_len_tot = cat_len_tot + cat_len
                # print("Len:", cat_len, ", total:", cat_len_tot)
            if 'missing' in page.keys():
                #print("Missing page:", page['title'])
                pages_missing.append(page['title'])
            #print(result_dict)
        if 'continue' in response.json().keys():
            print("Let's continue cats!")
            print(response.json()['continue'])
            PARAMS_1 = dict(list(PARAMS_0.items()) + list(response.json()['continue'].items()))
            have_data_to_get = True
        else:
            have_data_to_get = False
    for i_p, key_p in enumerate(result_dict):
        page_cats = {
            "title": key_p,
            "categories": result_dict[key_p],
            "missing": key_p in pages_missing
        }
        result.append(page_cats)
    return result

# def get_redirect_target_web(page_name):
    # # Получаем целевую страницу для редиректа
    # get_target = {
        # "action": "query",
        # "format": "json",
        # "titles": page_name,
        # "redirects": "1"
    # }
    # res = requests.get(script_config["api_url"], params=get_target).json()

    # try:
        # redirects = res.get("query", {}).get("redirects", [])
        # if redirects:
            # #target_title = redirects[0]["to"]
            # return redirects[0]["to"]
            # # r.set(f"wiki:redirect:{page_name}", target_title)
            # # count += 1
    # except Exception as e:
        # print(f"Ошибка: {e}")

# def get_redirect_target(page_name,r):
    # cached_redirect = r.get(f"page:isredirect:{page_name}")
    # if cached_redirect:
        # print(f"  <<< Have cached isredirect for {page_name}")
        # cached_redirect_target = r.get(f"page:redirect:{page_name}")
        # if cached_redirect_target:
            # print(f"  <<< GOOD! Have cached redirect target for {page_name}")
            # return cached_redirect_target
        # redirect_target = get_redirect_target_web(page_name)
        # r.setex(f"page:redirect:{redirect_target}", datetime.timedelta(hours=ttl_hours), value=1)
    # else:
        # return page_name

def get_disambigs(dis_pages,r):
    print("get_disambigs invoked! ===")
    result = {}
    redirects = []
    long_redirects = []
    dis_page_names = []
    session = requests.Session()
    # Redis fun
    ttl_hours = 336
    for dis_page in dis_pages:
        # instantly omit trash links
        if re.search(r"\[", dis_page.link) or \
           re.search(r"\]", dis_page.link):
            print(f"Skipping trash link: {dis_page.link}")
            continue
        # Redis fun
        # 4 - no page, 1 - ordinary, 2 - disambig, 3 - redirect
        # FIXME WTF! Why it's here?
        red_cached = r.get(f"page:status:{dis_page.link}") 
        if red_cached:
            # print(f"  >>> Have cached {dis_page.link} : {red_cached}")
            if red_cached == "4":
                ##print(f"{dis_page.link} is a redlilnk")
                result[dis_page.link] = False
            elif red_cached == "1":
                ##print(f"{dis_page.link} is an ordinary page")
                result[dis_page.link] = False
            elif red_cached == "2":
                ##print(f"{dis_page.link} is a disambig! (!)")
                result[dis_page.link] = True
            elif red_cached == "3":
                ##print(f"{dis_page.link} is a redirect")
                redirects.append(dis_page.link)
        else:
            # print(f"  XXX Have no cached {dis_page.link}")
            dis_page_names.append(dis_page.link)
    # dis_page_batch = '|'.join(dis_page_names)

    # Get target of link: ordinary page, redirect, or redlink
    for mb_page in get_wp_categories(dis_page_names):
        # print(f"checkin {mb_page['title']} ... ===")
        # if mb_page['title'] == "Ли Тхай То":
            # print(mb_page)
        #if "categories" in mb_page.keys():
        if len(mb_page["categories"]):
            is_disambig = "Категория:Страницы значений по алфавиту" in mb_page['categories']
            result[mb_page['title']] = is_disambig
            # Redis fun
            if is_disambig:
                # print(f"  <<< Caching {mb_page['title']} as a disambig (2)")
                r.setex(f"page:status:{mb_page['title']}", datetime.timedelta(hours=ttl_hours), value=2)
            else:
                # print(f"  <<< Caching {mb_page['title']} as an ordinary page (1)")
                r.setex(f"page:status:{mb_page['title']}", datetime.timedelta(hours=ttl_hours), value=1)
        else:
            # Check if it is a redirect or just a red link
            if mb_page['missing']:
                # Red lisk is obviously not a disambig
                result[mb_page['title']] = False
                # Redis fun
                print(f"  <<< Caching {mb_page['title']} as a redlink (4)")
                r.setex(f"page:status:{mb_page['title']}", datetime.timedelta(hours=ttl_hours), value=4)
            else:
                # If it's a redirect, then check it later
                redirects.append(mb_page['title'])
    # If there are no redirects, then just return disambig status for pages
    if not len(redirects):
        # print("no redirects to check,", redirects)
        return result,[]
    # If there are redirects, then check them
    print("Invoke redirect checker for", len(redirects), "pages")
    # Resolve redirects
    redirect_targets = []
    redirect_pairs = []
    REQUEST_PARAMS = {
        'action': "query",
        'formatversion':   2,
        'redirects': 1,
        'titles': '|'.join(redirects),
        'format': "json"
    }
    ##print(REQUEST_PARAMS)
    response2 = session.get(url=script_config["api_url"], params=REQUEST_PARAMS)
    if not "redirects" in response2.json()['query']:
        print("Cannot find redirects!")
        print(response2.json()['query'])
    ##print("Resolving redirects:")
    ##print(response2.json()['query']['redirects'])
    for redirect in response2.json()['query']['redirects']:
        try:
            rd = redirect['from']
            redirect_target = redirect['to']
        except KeyError:
            print("======== KeyError while resolving redirect ==========!!!")
            # print(response.json())
            # print("==================")
            print(response2.json())
            print(dis_page_names)
            print("^^^^^^ Skipping this, go to next redir.")
            exit(2)
            continue
        # TODO apply Redis here
        redirect_targets.append(redirect_target)
        redirect_pair = {
            'from': rd,
            'to': redirect_target
        }
        redirect_pairs.append(redirect_pair)
        #print(rd, "redirects to", redirect_target)
        if re.search(r"\(.*\)", rd) and \
          not re.search(r"\(.*\)", redirect_target) and \
          len(rd) > len(redirect_target):
            #print("^^^^^^ That was a bad redirect! ^^^^^^^")
            long_redirects.append(rd)
            #print("Now long redirs is", long_redirects)

    for mb_page in get_wp_categories(redirect_targets):
        #if "categories" in mb_page.keys():
        if len(mb_page["categories"]):
            is_disambig = "Категория:Страницы значений по алфавиту" in mb_page['categories']
            # Redis fun
            if is_disambig:
                print(f"  <<< Caching {mb_page['title']} as a disambig (2)")
                r.setex(f"page:status:{mb_page['title']}", datetime.timedelta(hours=ttl_hours), value=2)
            else:
                # print(f"  <<< Caching {mb_page['title']} as an ordinary page (1)")
                r.setex(f"page:status:{mb_page['title']}", datetime.timedelta(hours=ttl_hours), value=1)
        else:
            print("------------skipping faulty page", mb_page['title'])
            is_disambig = False
        result[mb_page['title']] = is_disambig
        ##print(f"now lets find {mb_page['title']} in redirect_pairs")
        ##print(redirect_pairs)
        for pair in redirect_pairs:
            if pair['to'] == mb_page['title']:
                result[pair['from']] = is_disambig
                ##print(f"We shoudld AFTER-REDIR overwrite {pair['from']} to {is_disambig}")
                # Redis fun
                if is_disambig:
                    print(f"  <<< AFTER-REDIR: Caching {pair['from']} as a disambig (2)")
                    r.setex(f"page:status:{pair['from']}", datetime.timedelta(hours=ttl_hours), value=2)
                else:
                    # print(f"  <<< AFTER-REDIR: Caching {pair['from']} as an ordinary page (1)")
                    r.setex(f"page:status:{pair['from']}", datetime.timedelta(hours=ttl_hours), value=1)
    return result,long_redirects

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
