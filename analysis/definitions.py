# @dataclass
# class CheckDefinition:
    # name: str
    # title: str
    # descr: str
    # func: Callable
    # kwargs: dict = field(default_factory=dict)
    # nowiki: bool = False
    # is_enabled_by_default: bool = True

from dataclasses import dataclass, field
from typing import Callable, Any

class Check():
    """
    The check result that contains check names and description, affected pages,
    options for listing on the resulting page and counting in stats
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name="", title="", descr="", pages=None, total=0, nowiki=False,
      supress_listing=False, supress_stat=False):
        if pages is None:
            pages = []
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
        return f'{self.name} ({self.counter} pages found, {self.percent}%)'

@dataclass
class CheckDefinition:
    name: str
    title: str
    descr: str
    func: Callable
    kwargs: dict[str, Any] = field(default_factory=dict)
    runtime_kwargs: dict[str, str] = field(default_factory=dict)
    nowiki: bool = False
    supress_stat: bool = False
    is_enabled_by_default: bool = True

    def run(self, pages, total, runtime):
        kwargs = dict(self.kwargs)

        kwargs.update({
            arg_name: runtime[runtime_name]
            for arg_name, runtime_name in self.runtime_kwargs.items()
        })

        return Check(
            name=self.name,
            title=self.title,
            descr=self.descr,
            pages=self.func(pages, **kwargs),
            total=total,
            nowiki=self.nowiki,
            supress_stat=self.supress_stat,
        )

class ProblemPage():
    def __init__(self, title="", counter=None, samples=[], note=""):
        self.title = title
        self.note = note
        self.counter = counter
        self.samples = samples
    def __repr__(self):
        return f"[[{self.title}]] ({self.counter} hits, {self.samples} samples)"
