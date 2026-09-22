"""
Script/bot to search for issues in the Wikipedia project
For details, please see https://ru.wikipedia.org/wiki/Участник:KlientosBot
"""

import sys
import datetime
# for projects shuffling
import random
import re

import copy

from jinja2 import Environment, FileSystemLoader

from wp_functions_aux import get_wp_pages_by_template, get_wp_pages_by_category_recurse
from wp_functions_aux import get_wp_authenticated_session, set_wp_page_text
from wp_functions_aux import get_wp_content_cached
from wp_functions_aux import parse_check_template, build_running_config
from wp_functions_aux import get_wp_internal_links_flat
# for fun
from wp_functions_aux import get_wp_pages_by_category

from get_all_redirects_2 import ensure_redirects_cache

# from wp_functions_check import *

from wp_auth_data import get_auth_data
from config import get_redis_client, get_tender_config

from analysis.checks import CHECKS
from analysis.runner import run_checks

# TODO check Template:Чистить| (problem)
# TODO check if no {{references}} but has <ref> or {{sfn}}
# TODO MAYBE check Template:уточнить (problem)

class Check():
    """
    The check result that contains check names and description, affected pages,
    options for listing on the resulting page and counting in stats
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name="", title="", descr="", pages=[], total=0, nowiki=False,
      supress_listing=False, supress_stat=False):
        self.name = name
        self.title = title
        self.descr = descr
        self.percent = 100*len(pages)/total # or 0
        self.counter = len(pages)
        self.pages = pages
        self.nowiki = nowiki
        self.supress_listing = supress_listing
        self.supress_stat = supress_stat
    def __repr__(self):
        return f'{self.name} ({self.counter} pages found)'

def concatenate_template_options(check_template_new):
    """
    Builds wikitext of wiki template options
    e. g. "|opt1=val1|opt2=val2".
    Arg: parsed template (dict)
    """
    template_options = ""
    for key, value in check_template_new.items():
        template_options = template_options + f"|{key}={value} "
    return template_options

def get_checks_enabled(running_config):

    return None

def extract_raw_check_template(content):
    """
    Returns raw wikitext of check template
    extracted from page wikitext
    """
    mc1 = re.findall(r"{{User:Klientos(?:Bot)?/project-tender[ \n]*\|[^}]*}}",
        content)

    if mc1:
        return mc1[0]
    return None

def get_target_pages(running_config,red_con):
    viet_pages = []
    for crit in running_config['criteria'].replace(', ',',').split(','):
        criteria = crit.strip()
        print("Working on criteria", criteria)
        if re.search(r"^Шаблон:", criteria):
            print("Search by template", criteria)
            viet_pages = viet_pages + get_wp_pages_by_template(criteria, 1)
        elif re.search(r"^Категория:Статьи проекта", criteria):
            print("Search by project category", criteria)
            viet_pages = viet_pages + get_wp_pages_by_category_recurse([ criteria ], 1)
        elif re.search(r"^Категория:", criteria):
            print("Search by category", criteria)
            viet_pages = viet_pages + get_wp_pages_by_category_recurse([ criteria ], 0)
        else:
            print("Unknown search criteria!")
            continue

    # Loading exceptions list
    exclude_pages = get_excluded_pages(running_config,red_con)
    print("exclude_pages", exclude_pages)

    print("Total pages found:", len(viet_pages))
    viet_pages = list(set(viet_pages) - set(exclude_pages))
    print("After omitting some pages:", len(viet_pages))

    return viet_pages

def get_excluded_pages(running_config,red_con):
    if 'except_pages' in running_config.keys():
        # TODO 'except_pages' -> 'exceptions_page'
        if running_config['except_pages'] == '':
            return []

        ex_page = get_wp_content_cached([running_config['except_pages']],red_con)
        return get_wp_internal_links_flat(ex_page)
    return []

def main():
    moment_start = datetime.datetime.now()
    auth_data = get_auth_data()
    session = get_wp_authenticated_session(auth_data["wp_login"], auth_data["wp_passw"])

    # Script config
    script_config = get_tender_config()

    # Redis
    red_con = get_redis_client()

    # Namespace 104 = project discussions
    result_pages = get_wp_pages_by_template("User:KlientosBot/project-tender", 104)
    random.shuffle(result_pages)
    print("Pages by template randomized =", result_pages)

    result_pages_static = None
    #result_pages_static = ["Проект:Холокост/Недостатки статей"]
    #result_pages_static = ["Проект:Мифология/Недостатки статей"]
    #result_pages_static = ["Проект:Православие/Недостатки статей/Православное богословие"]
    #result_pages_static = ['Проект:Вьетнам/Недостатки статей']
    #result_pages_static = ['Проект:Карелия/Недостатки статей']
    #result_pages_static = ["Проект:Киберспорт/Недостатки_статей"]
    if result_pages_static:
        print()
        print("NOTICE: запускаем со статичным набором страниц.")
        print()
        print("Было:",result_pages)
        result_pages = result_pages_static
        print("Стало:",result_pages)

    # DISAMBIGS CACHING
    # FIXME to config
    REDIRECTS_KEY = "wiki:ru:redirects"
    REDIRECTS_TTL = 3 * 24 * 3600
    RELOAD_THRESHOLD = 3 * 3600
    ttl = red_con.ttl(script_config["REDIS_DISAMB_SET"])
    if ttl >= script_config["REDIS_SET_RELOAD_THRESHOLD"]:
        print(f"Disambig cache is still warm ({round(ttl/3600, 1)} hours)")
    else:
        disambs = get_wp_pages_by_category("Категория:Страницы значений по алфавиту", namespace=0)
        red_con.delete(script_config["REDIS_DISAMB_SET"])
        red_con.sadd(script_config["REDIS_DISAMB_SET"], *disambs)
        red_con.expire(script_config["REDIS_DISAMB_SET"], REDIRECTS_TTL)
        print("Got some disambigs:", len(disambs))

    # REDIRECTS CACHING
    ensure_redirects_cache(red_con)

    ### iterate over found projects ###
    for post_results_page in result_pages:
        print("\nWorking on", post_results_page)

        raw_check_template = extract_raw_check_template(
            get_wp_content_cached([post_results_page],red_con)[0]['content'])
        if raw_check_template:
            check_template = parse_check_template(raw_check_template)
            #print(check_template)
            running_config = build_running_config(post_results_page, check_template, script_config)
            print("Running-config built as", running_config)

            # Check if it is time to refresh
            if running_config["timestamp_date"] + datetime.timedelta(days=running_config["time_cooldown"]) \
              > datetime.datetime.now():
                print("Not old enough, skipping")
                continue
            check_template_new = copy.deepcopy(check_template)
            #print("check_template_new 1", check_template_new)

            # remove obsolete options; temporary code
            check_template_new.pop('old_enough', None)
            check_template_new.pop('cooldown_threshold', None)

            check_template_new['timestamp'] = datetime.datetime.now()
            #print("check_template_new 2", check_template_new)
            
            # TODO what means timestamp vs. timestamp_date ?
        else:
            print("No bot template found! Exiting.")
            sys.exit(46)

        checks_enabled = get_checks_enabled(running_config)

        # get target page names
        viet_pages = get_target_pages(running_config,red_con)
        # ... and tagret pages content
        pages_content2 = get_wp_content_cached(viet_pages,red_con)

        area = re.findall(r"\:([^\/\:]*)\/", post_results_page)[0]
        area = re.findall(r"\:(.*)", post_results_page)[0].replace("/","_")
        # FIXME to very custom config
        OUTPUT_FILE = f"C:/Users/Dm/Desktop/wp/badlinks-{area}.py.txt"

        print("Updating page ", post_results_page)

        # TODO make empty stub check?..
        #checks.append(Check(
        checks = [
            Check(
            name="Total",
            title="Всего",
            pages=viet_pages,
            total=len(viet_pages),
            supress_listing=True)
        ]

        ### Checks ###

        checks_enabled_ng = {
            check.name: check.is_enabled_by_default
            for check in CHECKS
        }

        # enable_checks by template
        if 'enable_checks' in running_config.keys():
            enabled_checks = running_config['enable_checks'].replace(' ','').split(',')
            for ec in enabled_checks:
                # temporary dirty hack
                if ec == "Disambigs":
                    print(f"ALARMA! 'Disambigs' on page {post_results_page} (plez replace with 'BadLinks')")
                    exit(98)
                checks_enabled_ng[ec] = True
        # disable_checks by template
        if 'disable_checks' in running_config.keys():
            disable_checks = running_config['disable_checks'].replace(' ','').split(',')
            for dc in disable_checks:
                # temporary dirty hack
                if dc == "Disambigs":
                    print(f"ALARMA! 'Disambigs' on page {post_results_page} (plez replace with 'BadLinks')")
                    exit(98)
                checks_enabled_ng[dc] = False

        # Deal with check groups (somewhat legacy)
        check_groups = {}
        check_groups["CiteDecorations"] = {
            "DirectWebarchive",
            "TemplateRegexp Citation",
            "TemplateRegexp Cite press release",
            "TemplateRegexp Wayback",
            "TemplateRegexp webarchive",
            "TemplateRegexp Архивировано",
            "TemplateRegexp Проверено",
            "TemplateRegexp ISBN",
            "IconTemplates",
            "RefTemplates",
        }
        check_groups["Experimental"] = {
            "TemplateRegexp h",
            "BadDelimiters",
        }
        for key, value in check_groups.items():
            print(f"Should we enable {key}?")
            if key in checks_enabled_ng.keys():
                print(f"checks_enabled_ng[{key}] is set to ({checks_enabled_ng[key]})!")
                for chk in check_groups[key]:
                    checks_enabled_ng[chk] = checks_enabled_ng[key]

        # Consider ability to overwrite in script config
        #print("checks_enabled_ng:", checks_enabled_ng)
        #exit(99)

        #checks = run_checks(
        checks += run_checks(
            checks=CHECKS,
            checks_enabled=checks_enabled_ng,
            pages=pages_content2,
            total=len(viet_pages),
            red_con=red_con,
            running_config=running_config,
            script_config=script_config,
        )

        ### Rendering ###

        environment = Environment(loader=FileSystemLoader("templates/"),
                          trim_blocks=True,
                          lstrip_blocks=True)
        template = environment.get_template("index.wp")

        content = template.render(
            prologue = running_config['prologue'],
            epilogue = running_config['epilogue'],
            checks = checks,
            template_options = concatenate_template_options(check_template_new)
        )

        ### Publishing ###

        # Local file
        # This goes before the web. If web posting fails, we'll be able to debug using this

        with open(OUTPUT_FILE, mode="w", encoding="utf-8") as message:
            message.write(content)
            print(f"... wrote {OUTPUT_FILE}")

        # Web
        #sys.exit(7)
        if set_wp_page_text(session, post_results_page, content, script_config["WP_COMMIT_NOTE"]):
            print("Updated.")
        else:
            print("Cannot update page.")

        ### Stats ###
        print(datetime.datetime.now()-moment_start)

if __name__ == "__main__":
    main()
