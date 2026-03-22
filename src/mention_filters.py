"""Category mapping for mention-market series."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# MENTION CATEGORY MAPPING
# Maps T7 series names to high-level categories.
# ---------------------------------------------------------------------------

CATEGORY_MAP: dict[str, str] = {}

_SPORTS = [
    "KXNFLMENTION", "KXNBAMENTION", "KXNCAAMENTION", "KXNCAABMENTION",
    "KXFIGHTMENTION", "KXMLBMENTION", "KXNBAFINALSMENTION", "KXMMMENTION",
    "KXSBMENTION", "KXGREENDAYMENTION", "KXSNFMENTION", "KXTNFMENTION",
    "KXCFBMENTION", "KXGAMEDAYMENTION", "KXWOMENTION", "KXLEBRONMENTION",
]

_POLITICIANS = [
    "KXTRUMPMENTION", "KXSECPRESSMENTION", "KXMAMDANIMENTION",
    "KXBIDENMENTION", "KXVANCEMENTION", "KXBERNIEMENTION",
    "KXCONGRESSMENTION", "KXHEGSETHMENTION", "KXNEWSOMMENTION",
    "KXHOCHULMENTION", "KXGOVERNORMENTION", "KXMELANIAMENTION",
    "KXWALZMENTION", "KXHOMANMENTION", "KXDESANTISMENTION",
    "KXKAMALAMENTION", "KXRUBIOMENTION", "KXAOCMENTION",
    "KXPOWELLMENTION", "KXJPOWMENTION", "KXSCHUMERMENTION",
    "KXNYCMAYORDEBATEMENTION", "KXPERSONMENTION",
    "KXLEAVITTSMFMENTION", "KXLEAVITTMENTION", "KXPSAKIMENTION",
    "KXLUTNICKFTNMENTION", "KXBESSENTMTPMENTION",
    "KXSPANBERGERMENTION", "KXGLASERMENTION", "KXNYCMDEBMENTION",
    "KXCUOMOMENTION", "KXCROCKETTMENTION",
]

_ENTERTAINMENT = [
    "KXKIMMELMENTION", "KXLATENIGHTMENTION", "KXSNLMENTION",
    "KXCOLBERTMENTION", "KXMRBEASTMENTION", "KXSOUTHPARKMENTION",
    "KXSWIFTMENTION", "KXOSCARMENTION", "KXAWARDMENTION",
    "KXDWTSMENTION", "KXDOGSHOWMENTION", "KXROGANMENTION",
    "KXCMAMENTION", "KXMAHERMENTION", "KXZIWEMENTION",
    "KXSURVIVORMENTION", "KXCENAMENTION", "KXSHAQMENTION",
    "KXMINAJMENTION", "KXKARDASHIANMENTION", "KXNADALMENTION",
    "KXALTHOFFMENTION", "KXDILLONMENTION", "KXHARTMENTION",
    "KXBARKLEYMENTION", "KXWALESMENTION", "KXARMSTRONGMENTION",
]

_EARNINGS = [
    "KXEARNINGSMENTION",
]

_FINANCE = [
    "KXFEDMENTION", "KXECBMENTION", "KXSCOTUSMENTION",
    "KXJENSENMENTION", "KXDIMONMENTION", "KXALTMANMENTION",
    "KXACKMANMENTION", "KXAMODEIMENTION", "KXBENIOFFMENTION",
    "KXFINKMENTION", "KXKARPMENTION", "KXGRIFFINMENTION",
    "KXZUCKMENTION", "KXWEFMENTION", "KXBTCMENTION",
    "KXWALLERMENTION", "KXMIRANMENTION",
]

_MEDIA_NEWS = [
    "KXFOXNEWSMENTION", "KXNEWSNATIONMENTION", "KXMADDOWMENTION",
    "KXLASTWORDMENTION", "KXFTNMENTION", "KXMTPMENTION",
    "KXTBPNMENTION", "KXACOOPERMENTION", "KXCOOPERMENTION",
    "KXTHEWEEKNIGHTMENTION", "KXBONGINOMENTION", "KXCARLSONMENTION",
    "KXFREYMENTION", "KXTALARICOMENTION", "KXPOLITICSMENTION",
    "KXCULTUREMENTION", "KXVIEWMENTION", "KXZAKARIAMENTION",
]

for _series in _SPORTS:
    CATEGORY_MAP[_series] = "Sports"
for _series in _POLITICIANS:
    CATEGORY_MAP[_series] = "Politicians"
for _series in _ENTERTAINMENT:
    CATEGORY_MAP[_series] = "Entertainment"
for _series in _EARNINGS:
    CATEGORY_MAP[_series] = "Earnings"
for _series in _FINANCE:
    CATEGORY_MAP[_series] = "Finance"
for _series in _MEDIA_NEWS:
    CATEGORY_MAP[_series] = "Media/News"

# The four MAIN categories for the general notebook
MAIN_CATEGORIES = ["Earnings", "Entertainment", "Politicians", "Sports"]

# Additional categories for cross-comparison
ALL_CATEGORIES = ["Earnings", "Entertainment", "Finance", "Media/News", "Politicians", "Sports"]

CATEGORY_COLORS = {
    "Sports": "#1f77b4",
    "Politicians": "#d62728",
    "Entertainment": "#e377c2",
    "Earnings": "#ff7f0e",
    "Finance": "#2ca02c",
    "Media/News": "#bcbd22",
    "Other": "#aaaaaa",
}

# Political subgroup assignment (for political notebook)
POLITICAL_SERIES = [s for s in _POLITICIANS]


def get_category(series: str) -> str:
    """Map a series name to its mention category."""
    return CATEGORY_MAP.get(series, "Other")


def assign_political_subgroup(series: str) -> str:
    """Assign a political mention series to its subgroup."""
    s = series.upper()
    if "TRUMPMENTION" in s:
        return "Group 1: Trump Markets"
    elif "SECPRESSMENTION" in s:
        return "Group 2: Press Briefings"
    elif "MAMDANIMENTION" in s or "NYCMAYORDEBATEMENTION" in s:
        return "Group 3: Mayoral (Zohran Mamdani)"
    else:
        return "Group 4: Niche / One-offs"


# ---------------------------------------------------------------------------
# Aliases for backward compatibility
# ---------------------------------------------------------------------------

def assign_category(series: str) -> str:
    """Alias for get_category."""
    return get_category(series)


def get_political_series() -> list[str]:
    """Return the list of political mention series."""
    return list(POLITICAL_SERIES)
