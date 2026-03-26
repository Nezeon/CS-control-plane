"""
Shared customer alias map for matching abbreviations to canonical customer names.

Used by both Fathom sync (meeting title matching) and Jira sync (ticket summary matching).
All keys and values are lowercased. Values must match `customers.name` exactly (case-insensitive).
"""

# Canonical alias map: abbreviation → full customer name (lowercased)
CUSTOMER_ALIASES: dict[str, str] = {
    # Mubadala Capital
    "mubcap": "mubadala capital",
    "mubadala cap": "mubadala capital",
    "muc": "mubadala capital",
    # Al Raedah Finance
    "alraedahfinance": "al raedah finance",
    "alraedah finance": "al raedah finance",
    "alraedah": "al raedah finance",
    # GPH (maps to Phase 1 by default)
    "gph_makka": "the general presidency for the affairs of the grand mosque and the prophet's mosque (gph) - phase 1",
    "gph/ksgaa": "the general presidency for the affairs of the grand mosque and the prophet's mosque (gph) - phase 1",
    "gph": "the general presidency for the affairs of the grand mosque and the prophet's mosque (gph) - phase 1",
    # KSGAA
    "ksgaa(saudi)": "king salman global academy of arabic language (ksgaa)",
    "ksgaa": "king salman global academy of arabic language (ksgaa)",
    # Goosehead
    "goosehead/dms": "goosehead insurance",
    "goosehead/internal": "goosehead insurance",
    # JES (Jeraisy Electronic Services)
    "jes/deg": "jeraisy electronic services",
    "jes": "jeraisy electronic services",
    # Vision Bank
    "visionbank/internal lab": "vision bank",
    "visionbank": "vision bank",
    # Bracket-style aliases from Jira summaries
    "[dms]": "direct marketing solutions (dms)",
    "[libra solutions]": "libra solutions",
    "[ooredoo]": "ooredoo",
    "[tencent]": "tencent america",
    # Abbreviation aliases for formal names
    "pdo": "petroleum development oman (pdo)",
    "difc": "dubai international financial centre (difc)",
    "bnpb": "badan nasional penanggulangan bencana (bnpb)",
    "modon": "saudi authority for industrial cities and technology zones (modon)",
    "mof": "ministry of finance (mof)",
    "oia": "oman investment authority (oia)",
    "eskanbank": "eskan bank b.s.c",
    "eskan bank": "eskan bank b.s.c",
    "dms": "direct marketing solutions (dms)",
    "itmonkey": "it monkey, south africa",
    "it monkey": "it monkey, south africa",
    "connexpay": "connexpay",
}
