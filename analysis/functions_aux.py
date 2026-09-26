import re
import sys

from wp_functions_aux import get_wp_pages_by_category_recurse
from wp_functions_aux import get_wp_pages_by_category
from wp_functions_aux import get_wp_pages_by_template
from wp_functions_aux import get_wp_content_cached, get_wp_internal_links_flat

### Parsers and text processors ###

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

### More complex functions ###

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
    #print("exclude_pages", exclude_pages)

    #print("Total pages found:", len(viet_pages))
    viet_pages = list(set(viet_pages) - set(exclude_pages))
    print("Total pages found, after omitting some pages:", len(viet_pages))

    return viet_pages

def get_excluded_pages(running_config,red_con):
    """
    Get WP page with a list of pages that should not be checked
    """
    if 'except_pages' in running_config.keys():
        # TODO 'except_pages' -> 'exceptions_page'
        if running_config['except_pages'] == '':
            return []

        ex_page = get_wp_content_cached([running_config['except_pages']],red_con)
        return get_wp_internal_links_flat(ex_page)
    return []

### Not the analyzing functions ###

def ensure_disambigs_cache(red_con,script_config):
    """
    Check if disambig cache exists and not too old (to survive until the end of run).
    If not then build it.
    """
    ttl = red_con.ttl(script_config["REDIS_DISAMB_SET"])
    if ttl >= script_config["REDIS_SET_RELOAD_THRESHOLD"]:
        print(f"Disambig cache is still warm ({round(ttl/3600, 1)} hours)")
    else:
        disambs = get_wp_pages_by_category("Категория:Страницы значений по алфавиту", namespace=0)
        red_con.delete(script_config["REDIS_DISAMB_SET"])
        red_con.sadd(script_config["REDIS_DISAMB_SET"], *disambs)
        red_con.expire(script_config["REDIS_DISAMB_SET"], script_config["REDIS_SET_TTL"])
        print("Got some disambigs:", len(disambs))

def get_checks_enabled(running_config,CHECKS):
    """
    Build a dict of all checks with enabled/disabled boolean value.
    Sources for decisions (from lower to higher priority):
    - default value for every check in checks list
    - settings in bot template on working page in WP
    """
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
                print(f"ALARMA! 'Disambigs' on page {running_config["working_page"]}")
                print(f"(plez replace with 'BadLinks')")
                sys.exit(98)
            checks_enabled_ng[ec] = True
    # disable_checks by template
    if 'disable_checks' in running_config.keys():
        disable_checks = running_config['disable_checks'].replace(' ','').split(',')
        for dc in disable_checks:
            # temporary dirty hack
            if dc == "Disambigs":
                print(f"ALARMA! 'Disambigs' on page")
                print(f"(plez replace with 'BadLinks')")
                sys.exit(98)
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
        if key in checks_enabled_ng.keys():
            print(f"checks_enabled_ng[{key}] is set to ({checks_enabled_ng[key]})!")
            for chk in check_groups[key]:
                checks_enabled_ng[chk] = checks_enabled_ng[key]
    return checks_enabled_ng
