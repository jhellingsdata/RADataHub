"""Build the MSA tier table and the 2013-LAD -> Strategic Authority crosswalk.

Tier assignments as at 15 September 2026. Sources are recorded per row so the
table can be audited against the underlying government documents.

Strategic Authority outer boundaries are unions of 2013 local authority
districts, so the 2013 LAD layer is a valid base for dissolving even where
constituent councils have since been reorganised (e.g. Cumberland and
Westmorland and Furness, created 2023, are unions of the six 2013 Cumbria
districts).
"""

import json
import re
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Authority table
# ---------------------------------------------------------------------------

EST = "Established Mayoral"
MAY = "Mayoral"
FND = "Foundation"
PLN = "Planned"

authorities = [
    # short_name, official_name, tier, mayor_in_post, mayor, party, established, tier_change, instrument, source
    ("Greater London", "Greater London Authority", EST, True,
     "Sadiq Khan", "Labour", "2000-07-03", None,
     "Greater London Authority Act 1999", "NAO HC 263"),
    ("Greater Manchester", "Greater Manchester Combined Authority", EST, True,
     "Bev Craig", "Labour Co-op", "2011-04-01", None,
     "SI 2011/908", "NAO HC 263"),
    ("West Midlands", "West Midlands Combined Authority", EST, True,
     "Richard Parker", "Labour", "2016-06-17", None,
     "SI 2016/653", "NAO HC 263"),
    ("Liverpool City Region", "Liverpool City Region Combined Authority", EST, True,
     "Steve Rotheram", "Labour", "2014-04-01", None,
     "SI 2014/865", "NAO HC 263"),
    ("North East", "North East Mayoral Strategic Authority", EST, True,
     "Kim McGuinness", "Labour Co-op", "2024-05-07", "2026-05-18 (renamed NEMSA)",
     "SI 2024/402", "NAO HC 263"),
    ("South Yorkshire", "South Yorkshire Mayoral Combined Authority", EST, True,
     "Oliver Coppard", "Labour", "2014-04-01", None,
     "SI 2014/863", "NAO HC 263"),
    ("West Yorkshire", "West Yorkshire Combined Authority", EST, True,
     "Tracy Brabin", "Labour Co-op", "2014-04-01", None,
     "SI 2014/864", "NAO HC 263"),
    ("Cambridgeshire & Peterborough", "Cambridgeshire and Peterborough Combined Authority", EST, True,
     "Paul Bristow", "Conservative", "2017-03-03", "2026-07-31",
     "SI 2017/251", "Rewiring the State Cabinet Statement, 31 Jul 2026"),
    ("East Midlands", "East Midlands Combined County Authority", EST, True,
     "Claire Ward", "Labour", "2024-02-28", "2026-07-31",
     "SI 2024/232", "Rewiring the State Cabinet Statement, 31 Jul 2026"),
    ("West of England", "West of England Combined Authority", EST, True,
     "Helen Godwin", "Labour", "2017-02-09", "2026-07-31",
     "SI 2017/126", "Rewiring the State Cabinet Statement, 31 Jul 2026"),
    ("York & North Yorkshire", "York and North Yorkshire Combined Authority", EST, True,
     "David Skaith", "Labour Co-op", "2023-12-20", "2026-07-31",
     "SI 2023/1432", "YNYCA press release 31 Jul 2026; Rewiring the State"),

    ("Tees Valley", "Tees Valley Combined Authority", MAY, True,
     "Ben Houchen", "Conservative", "2016-04-01", None,
     "SI 2016/449", "NAO HC 263"),
    ("Hull & East Yorkshire", "Hull and East Yorkshire Combined Authority", MAY, True,
     "Luke Campbell", "Reform UK", "2025-02-05", None,
     "SI 2025/113", "NAO HC 263"),
    ("Greater Lincolnshire", "Greater Lincolnshire Combined County Authority", MAY, True,
     "Andrea Jenkyns", "Reform UK", "2025-02-05", None,
     "SI 2025/117", "NAO HC 263"),
    ("Cheshire & Warrington", "Cheshire and Warrington Combined Authority", MAY, False,
     None, None, "2026-02-24", None,
     "SI 2026/159", "SI 2026/159; inaugural election May 2027"),
    ("Cumbria", "Cumbria Combined Authority", MAY, False,
     None, None, "2026-02-24", None,
     "SI 2026/158", "SI 2026/158; inaugural election May 2027"),
    ("Sussex & Brighton", "Sussex and Brighton Combined County Authority", MAY, False,
     None, None, "2026-03-26", None,
     "SI 2026/362", "SI 2026/362; inaugural election May 2028"),
    ("Hampshire & the Solent", "Hampshire and the Solent Combined County Authority", MAY, False,
     None, None, "2026-06-04", None,
     "SI 2026/595", "SI 2026/595; inaugural election May 2028"),

    ("Devon & Torbay", "Devon and Torbay Combined County Authority", FND, False,
     None, None, "2025-02-05", "2026 Act (Foundation SA)",
     "SI 2025/115", "NAO HC 263"),
    ("Lancashire", "Lancashire Combined County Authority", FND, False,
     None, None, "2025-02-05", "2026 Act (Foundation SA)",
     "SI 2025/118", "NAO HC 263"),

    ("Greater Essex", "Greater Essex Combined County Authority (planned)", PLN, False,
     None, None, None, None,
     "not yet made", "Mayoral election deferred to May 2028"),
    ("Norfolk & Suffolk", "Norfolk and Suffolk Combined County Authority (planned)", PLN, False,
     None, None, None, None,
     "not yet made", "Mayoral election deferred to May 2028"),
]

cols = ["short_name", "official_name", "tier", "mayor_in_post", "mayor", "party",
        "date_established", "tier_change_date", "instrument", "status_source"]
tiers = pd.DataFrame(authorities, columns=cols)

# ---------------------------------------------------------------------------
# 1b. Election dates, and explicit gap-marks in place of blank mayor cells
# ---------------------------------------------------------------------------

# Next scheduled mayoral election. For authorities without a mayor this is the
# inaugural contest. Foundation authorities have no mayoral office, so there is
# nothing scheduled.
NEXT_ELECTION = {
    "Greater London": "May 2028",
    "Greater Manchester": "May 2028",
    "West Midlands": "May 2028",
    "Liverpool City Region": "May 2028",
    "North East": "May 2028",
    "South Yorkshire": "May 2028",
    "West Yorkshire": "May 2028",
    "Cambridgeshire & Peterborough": "May 2029",
    "East Midlands": "May 2028",
    "West of England": "May 2029",
    "York & North Yorkshire": "May 2028",
    "Tees Valley": "May 2028",
    "Hull & East Yorkshire": "May 2029",
    "Greater Lincolnshire": "May 2029",
    "Cheshire & Warrington": "May 2027",
    "Cumbria": "May 2027",
    "Sussex & Brighton": "May 2028",
    "Hampshire & the Solent": "May 2028",
    "Devon & Torbay": "None scheduled",
    "Lancashire": "None scheduled",
    "Greater Essex": "May 2028",
    "Norfolk & Suffolk": "May 2028",
}

missing_election = sorted(set(tiers.short_name) - set(NEXT_ELECTION))
assert not missing_election, f"no election date for: {missing_election}"

tiers["next_election"] = tiers.short_name.map(NEXT_ELECTION)


def mayor_state(row):
    """Three distinct absences, kept apart because they are different facts.

    A vacant office pending a first election is not the same as a tier with no
    mayoral office, and neither is the same as an area where the authority
    itself does not yet exist. Collapsing them into a blank cell would lose
    information a reader needs, so each is marked explicitly.
    """
    if row.mayor_in_post:
        return "In post"
    if row.tier == PLN:
        return "Authority not yet established"
    if row.tier == FND:
        return "No mayoral office at Foundation tier"
    return "Office vacant, first election not yet held"


tiers["mayor_status"] = tiers.apply(mayor_state, axis=1)

# Display field: the name where there is one, otherwise the reason there is not
_display = {
    "Authority not yet established": lambda r: f"Authority not yet established (election {r.next_election})",
    "No mayoral office at Foundation tier": lambda r: "No mayoral office (Foundation tier)",
    "Office vacant, first election not yet held": lambda r: f"First election not yet held ({r.next_election})",
}
tiers["mayor"] = tiers.apply(
    lambda r: r.mayor if r.mayor_in_post else _display[r.mayor_status](r), axis=1)
tiers["party"] = tiers.party.where(tiers.mayor_in_post, "Not applicable")

assert tiers[["mayor", "party", "mayor_status", "next_election"]].notna().all().all(), \
    "blank cells remain in the mayor block"

# ---------------------------------------------------------------------------
# 1c. Date formatting
# ---------------------------------------------------------------------------

# Dates are held as ISO in the source list above, because ISO is what sorts
# correctly and what the workbook expects. The display columns are dd/mm/yyyy.
# Both are kept: dd/mm/yyyy strings sort alphabetically, not chronologically,
# so anything downstream that orders by date needs the ISO column.

_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(.*)$")


def to_ddmmyyyy(value):
    """Reformat a leading ISO date, preserving any trailing note. Values that
    are not dates at all (e.g. "2026 Act (Foundation SA)") pass through
    untouched rather than being coerced into a date they do not assert."""
    if not isinstance(value, str):
        return value
    m = _ISO.match(value)
    if not m:
        return value
    y, mo, d, note = m.groups()
    return f"{d}/{mo}/{y}{note}"


tiers["date_established_iso"] = tiers.date_established.fillna("Not yet established")
tiers["tier_change_date_iso"] = tiers.tier_change_date
tiers["date_established"] = tiers.date_established.map(to_ddmmyyyy)
tiers["tier_change_date"] = tiers.tier_change_date.map(to_ddmmyyyy)

# Same treatment for the date columns, so no blank reaches a map tooltip
tiers["date_established"] = tiers.date_established.fillna("Not yet established")
_no_change = "No change since establishment"
tiers["tier_change_date"] = [
    "Not applicable" if t == PLN else (d if isinstance(d, str) else _no_change)
    for t, d in zip(tiers.tier, tiers.tier_change_date)]
tiers["tier_change_date_iso"] = [
    "Not applicable" if t == PLN else (d if isinstance(d, str) else _no_change)
    for t, d in zip(tiers.tier, tiers.tier_change_date_iso)]

# Every established authority must carry a real dd/mm/yyyy date
_bad = tiers.loc[
    (tiers.tier != PLN) & ~tiers.date_established.str.match(r"^\d{2}/\d{2}/\d{4}$"),
    ["short_name", "date_established"]]
assert _bad.empty, f"malformed establishment dates:\n{_bad}"

assert tiers.notna().all().all(), "blank cells remain in the authority table"

tiers = tiers[["short_name", "official_name", "tier", "mayor_in_post", "mayor",
               "mayor_status", "party", "next_election", "date_established",
               "date_established_iso", "tier_change_date", "tier_change_date_iso",
               "instrument", "status_source"]]

# ---------------------------------------------------------------------------
# 2. Crosswalk: 2013 LAD -> Strategic Authority
# ---------------------------------------------------------------------------

crosswalk = {
    "Greater London": [
        "City of London", "Barking and Dagenham", "Barnet", "Bexley", "Brent",
        "Bromley", "Camden", "Croydon", "Ealing", "Enfield", "Greenwich",
        "Hackney", "Hammersmith and Fulham", "Haringey", "Harrow", "Havering",
        "Hillingdon", "Hounslow", "Islington", "Kensington and Chelsea",
        "Kingston upon Thames", "Lambeth", "Lewisham", "Merton", "Newham",
        "Redbridge", "Richmond upon Thames", "Southwark", "Sutton",
        "Tower Hamlets", "Waltham Forest", "Wandsworth", "Westminster"],
    "Greater Manchester": [
        "Bolton", "Bury", "Manchester", "Oldham", "Rochdale", "Salford",
        "Stockport", "Tameside", "Trafford", "Wigan"],
    "West Midlands": [
        "Birmingham", "Coventry", "Dudley", "Sandwell", "Solihull", "Walsall",
        "Wolverhampton"],
    "Liverpool City Region": [
        "Halton", "Knowsley", "Liverpool", "Sefton", "St. Helens", "Wirral"],
    "North East": [
        "County Durham", "Gateshead", "Newcastle upon Tyne", "North Tyneside",
        "Northumberland", "South Tyneside", "Sunderland"],
    "South Yorkshire": ["Barnsley", "Doncaster", "Rotherham", "Sheffield"],
    "West Yorkshire": ["Bradford", "Calderdale", "Kirklees", "Leeds", "Wakefield"],
    "Cambridgeshire & Peterborough": [
        "Cambridge", "East Cambridgeshire", "Fenland", "Huntingdonshire",
        "Peterborough", "South Cambridgeshire"],
    "East Midlands": [
        "Derby", "Amber Valley", "Bolsover", "Chesterfield", "Derbyshire Dales",
        "Erewash", "High Peak", "North East Derbyshire", "South Derbyshire",
        "Nottingham", "Ashfield", "Bassetlaw", "Broxtowe", "Gedling",
        "Mansfield", "Newark and Sherwood", "Rushcliffe"],
    "West of England": [
        "Bath and North East Somerset", "Bristol, City of", "South Gloucestershire"],
    "York & North Yorkshire": [
        "York", "Craven", "Hambleton", "Harrogate", "Richmondshire", "Ryedale",
        "Scarborough", "Selby"],
    "Tees Valley": [
        "Darlington", "Hartlepool", "Middlesbrough", "Redcar and Cleveland",
        "Stockton-on-Tees"],
    "Hull & East Yorkshire": [
        "Kingston upon Hull, City of", "East Riding of Yorkshire"],
    "Greater Lincolnshire": [
        "Boston", "East Lindsey", "Lincoln", "North Kesteven", "South Holland",
        "South Kesteven", "West Lindsey", "North Lincolnshire",
        "North East Lincolnshire"],
    "Cheshire & Warrington": [
        "Cheshire East", "Cheshire West and Chester", "Warrington"],
    "Cumbria": [
        "Allerdale", "Carlisle", "Copeland", "Barrow-in-Furness", "Eden",
        "South Lakeland"],
    "Sussex & Brighton": [
        "Brighton and Hove", "Eastbourne", "Hastings", "Lewes", "Rother",
        "Wealden", "Adur", "Arun", "Chichester", "Crawley", "Horsham",
        "Mid Sussex", "Worthing"],
    "Hampshire & the Solent": [
        "Basingstoke and Deane", "East Hampshire", "Eastleigh", "Fareham",
        "Gosport", "Hart", "Havant", "New Forest", "Rushmoor", "Test Valley",
        "Winchester", "Isle of Wight", "Portsmouth", "Southampton"],
    "Devon & Torbay": [
        "East Devon", "Exeter", "Mid Devon", "North Devon", "South Hams",
        "Teignbridge", "Torridge", "West Devon", "Torbay"],
    "Lancashire": [
        "Burnley", "Chorley", "Fylde", "Hyndburn", "Lancaster", "Pendle",
        "Preston", "Ribble Valley", "Rossendale", "South Ribble",
        "West Lancashire", "Wyre", "Blackburn with Darwen", "Blackpool"],
    "Greater Essex": [
        "Basildon", "Braintree", "Brentwood", "Castle Point", "Chelmsford",
        "Colchester", "Epping Forest", "Harlow", "Maldon", "Rochford",
        "Tendring", "Uttlesford", "Southend-on-Sea", "Thurrock"],
    "Norfolk & Suffolk": [
        "Breckland", "Broadland", "Great Yarmouth", "King's Lynn and West Norfolk",
        "North Norfolk", "Norwich", "South Norfolk", "Babergh", "Forest Heath",
        "Ipswich", "Mid Suffolk", "St Edmundsbury", "Suffolk Coastal", "Waveney"],
}

xwalk = pd.DataFrame(
    [(lad, sa) for sa, lads in crosswalk.items() for lad in lads],
    columns=["lad13nm", "short_name"])

# ---------------------------------------------------------------------------
# 3. Validation against the boundary layer
# ---------------------------------------------------------------------------

geo = json.load(open("geo/eng_lad.json"))
lad_names = {f["properties"]["LAD13NM"] for f in geo["features"]}

unmatched = sorted(set(xwalk.lad13nm) - lad_names)
dupes = xwalk.lad13nm[xwalk.lad13nm.duplicated()].tolist()
orphan_sa = sorted(set(tiers.short_name) - set(xwalk.short_name))
orphan_xw = sorted(set(xwalk.short_name) - set(tiers.short_name))

print(f"LADs in boundary layer      : {len(lad_names)}")
print(f"LADs assigned to an SA      : {len(xwalk)}")
print(f"LADs with no SA             : {len(lad_names) - len(xwalk)}")
print(f"Authorities in tier table   : {len(tiers)}")
print()
print(f"FAIL unmatched LAD names    : {unmatched or 'none'}")
print(f"FAIL duplicate LAD assigns  : {dupes or 'none'}")
print(f"FAIL SA missing crosswalk   : {orphan_sa or 'none'}")
print(f"FAIL crosswalk missing SA   : {orphan_xw or 'none'}")
assert not (unmatched or dupes or orphan_sa or orphan_xw), "crosswalk validation failed"
print()
print(tiers.groupby("tier", sort=False).size().to_string())

tiers.to_csv("msa_tiers.csv", index=False)
xwalk.to_csv("msa_lad_crosswalk.csv", index=False)
print("\nwrote msa_tiers.csv, msa_lad_crosswalk.csv")
