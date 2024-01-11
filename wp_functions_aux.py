#import time
import sys
import re
import datetime
import requests
import dateutil.parser  # pip install python-dateutil

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
    session = requests.Session()
    result = []
    have_data_to_get = True
    PARAMS_1 = PARAMS_0
    while have_data_to_get:
        response = session.get(url=api_url, params=PARAMS_1)
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

def get_wp_pages_content(viet_pages,limit=10000):
    batch_size = 10
    viet_pages_content = []

    viet_pages_not_patrolled = []
    viet_pages_old_patrolled = []
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
    session = requests.Session()
    j = 0
    for vp in viet_pages:
        j += 1
        next_batch.append(vp)
        # if j > 20:
            # break
        if j > limit:
            break
        if len(next_batch) == batch_size or j == len(viet_pages):
            params_batch = REQ_PARAMS
            params_batch['titles'] = '|'.join(next_batch) #.replace("&","%26")
            response = session.get(url=api_url, params=REQ_PARAMS)
            for page in response.json()['query']['pages']:
                # if re.search(r"Постановление", page['title']):
                    # print(page)
                if not 'flagged' in page.keys():
                    viet_pages_not_patrolled.append(page['title'])
                    #print("Not flagged", page['title'])
                elif 'pending_since' in page['flagged'].keys():
                    next_old_patrolled = {
                        "title": page['title'],
                        "date": dateutil.parser.isoparse(page['flagged']['pending_since'])
                    }
                    viet_pages_old_patrolled.append(next_old_patrolled)
                    #print("Old flagged", page['title'], '(since', str(date_patrolled), ')')
                else:
                    pass

                next_page =  {
                    "title": page['title'],
                    "content": page['revisions'][0]['slots']['main']['content']
                }
                viet_pages_content.append(next_page)
            #print("Pages retrieved so far:", len(viet_pages_content))
            # raise Exception("I know Python!")
            next_batch = []
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
    return re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", date_str) or \
      re.search(r"^[0-9]{4}-[0-9]{2}$", date_str) or \
      re.search(r"^[0-9]{4}$", date_str) or \
      re.search(r"^$", date_str)

def get_wp_authentication_status(session):
    """
    Check if given session is authenticated.
    """
    URL = "https://ru.wikipedia.org/w/api.php"
    PARAMS_0 = {
        "action": "query",
        "meta": "userinfo",
        "format": "json"
    }
    if not hasattr(session, 'get'):
        return False
    response = session.get(url=URL, params=PARAMS_0)
    #print(response.json()['query']['userinfo'])
    if response.json()['query']['userinfo']['id']:
        return True
    return False

def get_wp_authenticated_session(login, password):
    """
    Takes login/pass and retursns authenticated sessions
    """
    session = requests.Session()
    URL = "https://ru.wikipedia.org/w/api.php"
    PARAMS_1 = {
        'action': "query",
        'meta':   "tokens",
        'type':   "login",
        'format': "json"
    }
    response = session.get(url=URL, params=PARAMS_1)
    # print(response.json()['query']['tokens'])
    login_token = response.json()['query']['tokens']['logintoken']

    PARAMS_2 = {
        'action':     "login",
        'lgname':     login,
        'lgpassword': password,
        'lgtoken':    login_token,
        'format':     "json"
    }

    response = session.post(url=URL, data=PARAMS_2)
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
    URL = "https://ru.wikipedia.org/w/api.php"
    PARAMS_4 = {
        "action": "query",
        "meta":   "tokens",
        "format": "json"
    }
    response = session.get(url=URL, params=PARAMS_4)
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

    response = session.post(url=URL, data=PARAMS_5)
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
    session = requests.Session()
    result_dict = {}
    result = []
    have_data_to_get = True
    pages_missing = []
    PARAMS_1 = PARAMS_0
    while have_data_to_get:
        cat_len_tot = 0
        #time.sleep(3)
        response = session.get(url=api_url, params=PARAMS_1)
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

def get_disambigs(dis_pages):
    result = {}
    redirects = []
    long_redirects = []
    dis_page_names = []
    for dis_page in dis_pages:
        dis_page_names.append(dis_page.link)
    # dis_page_batch = '|'.join(dis_page_names)
    session = requests.Session()
    URL = "https://ru.wikipedia.org/w/api.php"
    # PARAMS_1 = {
        # 'action': "query",
        # 'formatversion':   2,
        # 'prop':   "categories",
        # 'cllimit': 1000,
        # 'titles': dis_page_batch,
        # 'format': "json"
    # }
    # response = session.get(url=URL, params=PARAMS_1)
    # for mb_page in response.json()['query']['pages']:
    # print(get_wp_categories(dis_page_names))
    for mb_page in get_wp_categories(dis_page_names):
        # if mb_page['title'] == "Ли Тхай То":
            # print(mb_page)
        #if "categories" in mb_page.keys():
        if len(mb_page["categories"]):
            try:
                result[mb_page['title']] = \
                    "Категория:Страницы значений по алфавиту" in mb_page['categories']
            except:
                print(mb_page)
                sys.exit(5)
        else:
            if mb_page['missing']:
                result[mb_page['title']] = False
            else:
                redirects.append(mb_page['title'])
                # print("redirect:", mb_page['title'])
    if not len(redirects):
        # print("no redirects to check,", redirects)
        return result,[]
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
    response2 = session.get(url=URL, params=REQUEST_PARAMS)
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
    # PARAMS_3 = {
        # 'action': "query",
        # 'formatversion':   2,
        # 'prop':   "categories",
        # 'cllimit': 1000,
        # 'titles': '|'.join(redirect_targets),
        # 'format': "json"
    # }
    # response = session.get(url=URL, params=PARAMS_3)
    # #print(mb_page)
    # for mb_page in response.json()['query']['pages']:
    for mb_page in get_wp_categories(redirect_targets):
        #if "categories" in mb_page.keys():
        if len(mb_page["categories"]):
            is_disambig = "Категория:Страницы значений по алфавиту" in mb_page['categories']
        else:
            print("------------skipping faulty page", mb_page['title'])
            is_disambig = False
        result[mb_page['title']] = is_disambig
        for pair in redirect_pairs:
            if pair['to'] == mb_page['title']:
                result[pair['from']] = is_disambig
    return result,long_redirects

def parse_check_template(template_text):
    """
    Parse template text to dict
    """
    template_dict = {}
    mc2 = re.findall(r"\|([\-_ a-zA-Z0-9\n]*)\=([^\|}]*)", template_text)
    for m in mc2:
        template_dict[ m[0].strip() ] = m[1].strip()
    return template_dict
