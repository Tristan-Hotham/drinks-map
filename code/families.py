"""Drink families and their Wikidata anchor classes.

A drink type or product belongs to the first family (in this order) whose anchor class is among its ancestors in
Wikidata's subclass tree (P279), or whose anchor it is. The order matters: Calvados is a brandy before it is a
'drink from apples', sake before 'rice wine', and a whisky liqueur a liqueur only if no spirit type matches first.
"""
FAMS = [
    # key, label, colour (light theme), anchors
    ("wine", "Wine", "#8E1F45", ["Q282", "Q722338", "Q321263", "Q11334094", "Q231088", "Q633625"]),
    ("beer", "Beer", "#E0A106", ["Q44", "Q15075508"]),
    ("cider", "Cider and perry", "#84B135", ["Q167296", "Q2047030", "Q138848108"]),
    ("whisky", "Whisky", "#9C5A22", ["Q281", "Q140460111"]),
    ("gin", "Gin and juniper", "#3FA7C9", ["Q959362"]),
    ("rum", "Rum and cane spirits", "#5C3317", ["Q83376", "Q744729"]),
    ("agave", "Tequila and mezcal", "#3F8F5C", ["Q122195", "Q726413", "Q932877", "Q1389479", "Q7283706"]),
    ("vodka", "Vodka", "#8A97B0", ["Q374", "Q2919495"]),
    ("brandy", "Brandy and fruit spirits", "#C9562E", ["Q146470", "Q284", "Q503252", "Q388502", "Q693078", "Q931946",
                                                        "Q222216", "Q2166541", "Q3268", "Q368610", "Q1930269", "Q1539760", "Q397926"]),
    ("anise", "Anise spirits", "#7155A8", ["Q337687", "Q638290", "Q330880", "Q16976", "Q170210", "Q104178995"]),
    ("asian", "Baijiu, soju and shochu", "#D6333F", ["Q629266", "Q696105", "Q1165352", "Q115607485", "Q1069948"]),
    ("liqueur", "Liqueurs and bitters", "#D86AA0", ["Q178780", "Q753069", "Q778524", "Q192150", "Q1344463", "Q1927744"]),
    ("spirit", "Other spirits", "#55505C", ["Q56139", "Q12673554", "Q1815494", "Q1458114"]),
    ("rice", "Sake and rice drinks", "#3E5FB8", ["Q170219", "Q1142986", "Q2724403", "Q696911"]),
    ("trad", "Traditional drinks", "#1E8C88", ["Q184442", "Q839492", "Q511700", "Q516592", "Q744983", "Q173773", "Q61081",
                                               "Q583731", "Q2736566", "Q2905047", "Q1888644", "Q131168", "Q2720364", "Q4850250", "Q7695264"]),
]
# Spirits are matched before the broad 'liqueur' class, and specific spirit types before 'other spirits'. Order of
# testing (not of display):
TEST = ["asian", "rice", "cider", "trad", "beer", "whisky", "gin", "rum", "agave", "vodka", "anise", "brandy", "liqueur", "wine", "spirit"]
KEY = {f[0]: f for f in FAMS}
SPIRITS = ["whisky", "gin", "rum", "agave", "vodka", "brandy", "anise", "asian", "liqueur", "spirit"]
GROUP = {k: ("spirits" if k in SPIRITS else k) for k in KEY}
GROUPS = [("wine", "Wine", "#8E1F45"), ("beer", "Beer", "#E0A106"), ("cider", "Cider and perry", "#84B135"),
          ("spirits", "Spirits", "#B8452A"), ("rice", "Sake and rice drinks", "#3E5FB8"), ("trad", "Traditional drinks", "#1E8C88")]
# excluded: mixed drinks and words that are not drinks of a place
EXCLUDE = {"Q134768", "Q4353992", "Q3492867", "Q8193047", "Q4713330", "Q11286607", "Q3930973", "Q1571448",
           "Q66363580", "Q492554", "Q1418227", "Q17118943", "Q1415683", "Q902582",
           "Q140248574", "Q18534542", "Q7257246"}  # (last three: hard seltzer brands, restaurant and pub chains)


def family(anc, q=None):
    """anc: set of ancestor QIDs (including the item's own classes)."""
    s = set(anc) | ({q} if q else set())
    if s & EXCLUDE:
        return None
    for k in TEST:
        if s & set(KEY[k][3]):
            return k
    return "other"
