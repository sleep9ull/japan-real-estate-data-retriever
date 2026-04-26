from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class SiteConfig:
    source: str
    display_name: str
    base_url: str
    workflow_reference: str


SITES: Dict[str, SiteConfig] = {
    "suumo": SiteConfig(
        source="suumo",
        display_name="SUUMO",
        base_url="https://suumo.jp/",
        workflow_reference="site-suumo.md",
    ),
    "athome": SiteConfig(
        source="athome",
        display_name="at home",
        base_url="https://www.athome.co.jp/",
        workflow_reference="site-athome.md",
    ),
    "homes": SiteConfig(
        source="homes",
        display_name="LIFULL HOME'S",
        base_url="https://www.homes.co.jp/",
        workflow_reference="site-homes.md",
    ),
    "yahoo_japan": SiteConfig(
        source="yahoo_japan",
        display_name="Yahoo! JAPAN 不動産",
        base_url="https://realestate.yahoo.co.jp/",
        workflow_reference="site-yahoo-japan.md",
    ),
}


def site_choices() -> Tuple[str, ...]:
    return tuple(SITES.keys())


def get_site(source: str) -> SiteConfig:
    try:
        return SITES[source]
    except KeyError as exc:
        choices = ", ".join(site_choices())
        raise ValueError(f"Unsupported source {source!r}; expected one of: {choices}") from exc

