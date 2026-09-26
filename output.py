
import datetime

from jinja2 import Environment, FileSystemLoader

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

def build_working_page(running_config,checks,bot_template):
    """
    Builds content of a new working page: check reults, statistics, etc.
    Returns wikitext.
    """
    # this is important
    bot_template['timestamp'] = datetime.datetime.now()

    environment = Environment(loader=FileSystemLoader("templates/"),
        trim_blocks=True,
        lstrip_blocks=True)
    template = environment.get_template("index.wp")

    content = template.render(
        prologue = running_config['prologue'],
        epilogue = running_config['epilogue'],
        checks = checks,
        template_options = concatenate_template_options(bot_template)
    )

    return content
