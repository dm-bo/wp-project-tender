import requests
import re
import datetime
import dateutil.parser  # pip install python-dateutil

# gets template name
# returns array of page names
def get_wp_pages_by_template(template, namespace):
    API_URL = "http://ru.wikipedia.org/w/api.php"
    PARAMS_0 = {
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
    PARAMS_1 = PARAMS_0
    while have_data_to_get:
        response = session.get(url=API_URL, params=PARAMS_1)
        pages_dict = response.json()['query']["pages"]
        #first_set = list(pages_dict)[0]
        transcluded_objs = pages_dict[list(pages_dict)[0]]['transcludedin']
        # res = [ sub['gfg'] for sub in test_list ]
        for ti in transcluded_objs:
            result.append(ti['title'].replace('Обсуждение:',''))
        if 'continue' in response.json().keys():
            print("Let's continue!")
            print(response.json()['continue'])
            PARAMS_1 = dict(list(PARAMS_0.items()) + list(response.json()['continue'].items()))
            have_data_to_get = True
        else:
            have_data_to_get = False
    return sorted(result)

# TODO sort unpatrolled by name
# TODO sort not latest by date
def get_wp_pages_content(viet_pages):
    time_start = datetime.datetime.now()
    batch_size = 10
    viet_pages_content = []

    viet_pages_not_patrolled = []
    viet_pages_old_patrolled = []
    next_batch = []
    API_URL = "http://ru.wikipedia.org/w/api.php"
    PARAMS_0 = {
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
        if len(next_batch) == batch_size or j == len(viet_pages):
            print("It's time to request", len(next_batch), "pages (j is", j, "of", len(viet_pages),")")
            PARAMS_batch = PARAMS_0
            PARAMS_batch['titles'] = '|'.join(next_batch).replace("&","%26")
            #PARAMS_batch['titles'] = 'Олонец'
            response = session.get(url=API_URL, params=PARAMS_0)
            response_json = response.json()['query']['pages']
            for page in response.json()['query']['pages']:

                # patrolling
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
            print("Pages retrieved so far:", len(viet_pages_content))
            # raise Exception("I know Python!")
            next_batch = []
    viet_pages_content = sorted(viet_pages_content, key=lambda d: d['title'])
    viet_pages_not_patrolled = sorted(viet_pages_not_patrolled)
    viet_pages_old_patrolled = sorted(viet_pages_old_patrolled, key=lambda d: d['date'])
    return viet_pages_content, viet_pages_not_patrolled, viet_pages_old_patrolled

class OloloLink(object):
    def __init__(self, link="", page=""):
        self.link = link
        self.page = page
    def __repr__(self):
        return '[[{}]] ({})>'.format(self.link, self.page)

def get_wp_internal_links(viet_pages_content):
    links_Ololo = []
    links_Ololo_arr = []
    i = 0
    start_Ololo = datetime.datetime.now()
    for page in viet_pages_content:
        print("matching", page['title'])
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
                links_Ololo.append(OloloLink(m, page['title']))
                links_Ololo_arr.append({'link': m, 'page': page['title']})
        if divmod(i, 10)[1] == 0:
            print("Extracting wikilinks:", i, "/", len(viet_pages_content), "pages processed")

    spent_Ololo = datetime.datetime.now() - start_Ololo
    print(links_Ololo, "extracted in", spent_Ololo)
    return links_Ololo_arr

def get_flagged_status(page):
    return ""


# AA OOO
#from itertools import groupby
# AA OOO
# print([list(g[1]) for g in groupby(sorted(links_Ololo, key=link), link)])

# Sort list of objects?
#newlist = sorted(list_to_be_sorted, key=lambda d: d['name']) 


###### POSH #######

# $vietPagesContent = $vietPagesContent | sort -Property title
# $stopTimeBatched = (Get-Date) - $startTimeBatched
# "$($vietPagesContent.Count) pages got their content in $([Math]::Round($stopTimeBatched.TotalSeconds)) seconds." | Append-Log
# $vietPagesContent | where {$_.Content -like ""} | % { "WARNING: no content for $($_.Title)" | Append-Log }
