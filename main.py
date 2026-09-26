"""
Script/bot to search for issues in the Wikipedia project
For details, please see https://ru.wikipedia.org/wiki/Участник:KlientosBot
"""

import datetime
import random

# from jinja2 import Environment, FileSystemLoader
from output import build_working_page

from wp_functions_aux import get_wp_pages_by_template
from wp_functions_aux import get_wp_authenticated_session, set_wp_page_text
from wp_functions_aux import get_wp_content_cached
from wp_functions_aux import parse_check_template, build_running_config
from wp_functions_aux import overwrite_tmp_file

from get_all_redirects_2 import ensure_redirects_cache

from wp_auth_data import get_auth_data
from config import get_redis_client, get_tender_config

from analysis.checks import CHECKS
from analysis.runner import run_checks
from analysis.functions_aux import (
    extract_raw_check_template,
    get_target_pages,
    ensure_disambigs_cache,
    get_checks_enabled
)

# TODO check Template:Чистить| (problem)
# TODO MAYBE check Template:уточнить (problem)

def main():

    # Script config
    script_config = get_tender_config()

    # Redis
    red_con = get_redis_client()

    # Namespace 104 — project discussions
    result_pages = get_wp_pages_by_template("User:KlientosBot/project-tender", 104)
    random.shuffle(result_pages)
    print("Pages by template randomized =", result_pages)

    #result_pages = ["Проект:Холокост/Недостатки статей"]
    #result_pages = ["Проект:Православие/Недостатки статей/Православное богословие"]
    # result_pages = ['Проект:Вьетнам/Недостатки статей']
    result_pages = ['Проект:Качество/Недостатки избранных списков']

    # DISAMBIGS CACHING
    ensure_disambigs_cache(red_con,script_config)

    # REDIRECTS CACHING
    ensure_redirects_cache(red_con)

    ### iterate over found projects ###
    for working_page in result_pages:
        print("\nWorking on", working_page)

        raw_check_template = extract_raw_check_template(
            get_wp_content_cached([working_page],red_con)[0]['content'])
        # if not raw_check_template:
            # print("No bot template found! Exiting.")
            # exit(46)
        check_template = parse_check_template(raw_check_template)
        running_config = build_running_config(working_page, check_template, script_config)
        print("Running-config built as", running_config)

        # Check if it is time to refresh
        if running_config["next_run_date"] > datetime.datetime.now():
            print("Not old enough, skipping")
            continue

        # remove obsolete options; temporary code
        check_template.pop('old_enough', None)
        check_template.pop('cooldown_threshold', None)
        check_template.pop('timestamp_date', None)

        # get target page names
        viet_pages = get_target_pages(running_config,red_con)
        # ... and tagret pages content
        pages_content2 = get_wp_content_cached(viet_pages,red_con)

        ### Checks ###

        checks_enabled = get_checks_enabled(running_config,CHECKS)

        # TODO remove "total" from arguments
        checks = run_checks(
            checks=CHECKS,
            checks_enabled=checks_enabled,
            pages=pages_content2,
            total=len(viet_pages),
            red_con=red_con,
            running_config=running_config,
            script_config=script_config,
        )

        ### Rendering ###

        content = build_working_page(running_config,checks,check_template)

        ### Publishing ###
        print("\nPublishing", working_page)

        # Local file
        # This goes before the web. If web posting fails, we'll be able to debug using this
        overwrite_tmp_file(running_config, content)

        # Web
        #exit(7)
        session = get_wp_authenticated_session(get_auth_data())
        if set_wp_page_text(session, working_page, content, script_config["WP_COMMIT_NOTE"]):
            print("Updated.")
        else:
            print("Cannot update page.")
        #exit(8)

if __name__ == "__main__":
    main()
