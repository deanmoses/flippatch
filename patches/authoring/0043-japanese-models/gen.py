"""Emit 0043-japanese-new-makers.yaml and 0044-japanese-gapfill-models.yaml.

Early-Japanese makers and machines from the eremeka catalog (thetastates.com /
earlyarcadesjapan.blogspot.com, seeded 0041). flipcommons already imported every
game IPDB carries (reconciled separately — see README); these two patches add the
records IPDB lacks, attributed flipcommons-catalog (we derive the structured
maker/model/year/theme fields from the eremeka research) with a cite to the eremeka
page (blog post where one exists, else the tag listing).

0043 — eight new makers (manufacturer + corporate-entity + their absent models),
       plus reassigning two orphaned models (Beat & Spark, Jumbo Kick — IPDB lists
       them "Unknown Manufacturer", so flipcommons holds them with no maker) to the
       new Nihon Tenbo entity and dating them.
0044 — gap-fill titles under makers flipcommons already has (Sankyo, Komaya,
       Universal, Nihon Gorakuki, Nihon Jidou Hanbaiki).

Japanese names follow the existing convention name = "English (日本語)". Themes map
eremeka `theme ~ ...` tags onto flipcommons Theme slugs (THEME_MAP, for audit);
per-model theme lists are curated below. Approximate eremeka years (~) are asserted
with the uncertainty in the note. Collision-safe slugs are used where the English
title already exists for an unrelated maker.

Run from the backend:
  cd flipcommons/backend && \
    uv run python ../../pindata/patches/authoring/0043-japanese-models/gen.py
"""

import os
import re
import sys
from pathlib import Path

import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import patchkit as pk  # noqa: E402
from apps.catalog.models import (  # noqa: E402
    CorporateEntity,
    Location,
    MachineModel,
    Manufacturer,
    Theme,
    Title,
)

OUT = HERE.parent.parent  # .../patches/

LISTING = (
    "https://thetastates.com/eremeka/eremekaDisplay.php"
    "?mentionOnly=1&search=yes&tag=yokomono+~+flipper+pinball"
)
BLOG = "https://earlyarcadesjapan.blogspot.com"

# eremeka `theme ~ ...` tag -> flipcommons Theme slugs. Audit record of the mapping
# judgment; per-model theme lists below are the curated result (noise tags dropped).
THEME_MAP = {
    "theme ~ USA kitsch": ["america"],
    "theme ~ adult oriented": ["adult"],
    "theme ~ animals ~ cats": ["cats"],
    "theme ~ animals ~ dinosaurs": ["dinosaurs"],
    "theme ~ circus/fair/festival": ["circus"],
    "theme ~ fantasy": ["fantasy"],
    "theme ~ god/demon": ["mythology"],
    "theme ~ kaiju & mecha": ["monsters", "robots"],
    "theme ~ licensed property": ["licensed"],
    "theme ~ music & dance": ["music", "dancing"],
    "theme ~ ninjas, samurai": ["japanese-culture"],
    "theme ~ pirates": ["pirates"],
    "theme ~ psychedelic": ["psychedelic"],
    "theme ~ space/UFOs/scifi": ["space", "science-fiction"],
    "theme ~ sports ~ baseball": ["baseball"],
    "theme ~ sports ~ basketball": ["basketball"],
    "theme ~ sports ~ bowling": ["bowling"],
    "theme ~ sports ~ football (american)": ["american-football"],
    "theme ~ sports ~ football (soccer)": ["soccer"],
    "theme ~ sports ~ hockey": ["hockey"],
    "theme ~ sports ~ martial arts": ["martial-arts"],
    "theme ~ sports ~ skiing": ["skiing"],
    "theme ~ sports ~ tennis": ["tennis"],
    "theme ~ vehicles ~ aviation": ["aviation"],
    "theme ~ vehicles ~ boats / water craft": ["boats"],
    "theme ~ vehicles ~ cars": ["cars"],
    # dropped (not themes): gambling*, mechanic ~ videogame, appearance ~ *, players ~ *
}


def emit(
    ref,
    *,
    create=False,
    expect=None,
    note=None,
    cite=None,
    fields=None,
    themes=None,
    location=None,
    aliases=None,
    ce_aliases=None,
    abbreviations=None,
):
    """patchkit.entry plus relationship lines (location / theme / alias / abbreviation) appended."""
    e = pk.entry(ref, create=create, expect=expect, note=note, cite=cite, fields=fields)
    extra = []
    if location:
        extra.append(f"      location: [{', '.join(location)}]")
    if themes:
        extra.append(f"      theme: [{', '.join(themes)}]")
    if aliases:
        extra.append(f"      manufacturer_alias: [{', '.join(aliases)}]")
    if ce_aliases:
        extra.append(f"      corporate_entity_alias: [{', '.join(ce_aliases)}]")
    if abbreviations:
        extra.append(f"      abbreviation: [{', '.join(abbreviations)}]")
    if extra:
        e += "\n" + "\n".join(extra)
    return e


_JP_PAREN = re.compile(r"\(([^()]*)\)")
_CJK = re.compile(r"[぀-ヿ㐀-鿿]")


def jp_name(name):
    """The Japanese name embedded in a model name `English (日本語)`, or None.

    Returns the last parenthesized run that contains a CJK character (kana/kanji),
    so it survives a bracketed note like `Crazy 15 [Mark II] (クレイジー15ゲーム)`.
    """
    for cand in reversed(_JP_PAREN.findall(name)):
        if _CJK.search(cand):
            return cand.strip()
    return None


# --------------------------------------------------------------------------- #
# 0043 — new makers (manufacturer -> corporate-entity -> models) + orphan reassigns
# --------------------------------------------------------------------------- #
# Each maker: mfg/ce slugs+names, ce location (country-level `japan` when HQ is
# unrecoverable), models, and any orphan reassignments (existing models given a maker).

NEW_MAKERS = [
    {
        "mfg": ("nihon-tenbo", "Nihon Tenbo"),
        "ce": ("nihon-tenbo-goraku-sha", "Nihon Tenbo Entertainment Company"),
        "loc": ["japan"],
        "ce_note": 'The eremeka catalog credits 日本展望娯楽社 ("Nihon Tenbo / Japan Outlook Entertainment Company", abbreviated Nitten) with early Japanese flipper games c.1967-1972.',
        "models": [
            {
                "slug": "home-run-nihon-tenbo",
                "game_format": "pinball",
                "technology_generation": "electromechanical",
                "name": "Home Run (ホームランゲーム)",
                "year": 1967,
                "approx": True,
                "themes": ["baseball"],
                "cite": f"{BLOG}/2023/01/home-run-by-japan-outlook-entertainment.html",
                "note": "The eremeka catalog dates this baseball game to approximately 1967 (marked ~) by Nihon Tenbo.",
            },
            {
                "slug": "soccer-ace",
                "game_format": "pinball",
                "technology_generation": "electromechanical",
                "name": "Soccer Ace (サッカーエース)",
                "year": 1969,
                "approx": False,
                "themes": ["soccer"],
                "cite": LISTING,
                "note": 'The eremeka catalog lists "1969 Socker Ace (Soccer Ace) by Nihon Tenbo".',
            },
        ],
        "orphans": [
            {
                "ipdb_id": 6771,
                "slug": "beat-spark",
                "game_format": "pinball",
                "year": 1970,
                "themes": ["soccer"],
                "note": 'The eremeka catalog lists "1970 Beat & Spark [Socker] by Tokyo Corporation & Nihon Tenbo"; flipcommons held it with no maker (IPDB: "Unknown Manufacturer").',
                "cite": LISTING,
            },
            {
                "ipdb_id": 6772,
                "slug": "jumbokick",
                "game_format": "pinball",
                "year": 1970,
                "themes": ["martial-arts"],
                "note": 'The eremeka catalog lists "1970 Jumbo Kick by Tokyo Corporation & Nihon Tenbo"; flipcommons held it with no maker (IPDB: "Unknown Manufacturer").',
                "cite": LISTING,
            },
        ],
    },
    {
        # HQ (Setagaya, Tokyo) is a Denfaminicogamer fact, asserted in 0049.
        "mfg": ("kato", "Kato"),
        "ce": ("kato", "Kato"),
        "loc": [],
        "ce_note": "The eremeka catalog credits カトウ (Kato) with the EM soccer game Soccer 8 c.1967.",
        "models": [
            {
                "slug": "soccer-8",
                "game_format": "pinball",
                "technology_generation": "electromechanical",
                "name": "Soccer 8 (サッカー8)",
                "year": 1967,
                "approx": True,
                "themes": ["soccer"],
                "cite": f"{BLOG}/2024/02/blog-post.html",
                "note": "The eremeka catalog dates this soccer game to approximately 1967 (marked ~) by Kato.",
            },
        ],
    },
    {
        # No verified HQ: the modern 昭和遊園株式会社 (incorporated 1978) can't be shown to be
        # the 1970 Rocket V maker — shared generic name only — so stay country-level.
        "mfg": ("showa-yuen", "Showa Yuen"),
        "ce": ("showa-yuen", "Showa Yuen"),
        "loc": ["japan"],
        "ce_note": "The eremeka catalog credits 昭和遊園 (Showa Yuen) with the space-themed flipper game Rocket V in 1970.",
        "models": [
            {
                "slug": "rocket-v",
                "game_format": "pinball",
                "technology_generation": "electromechanical",
                "name": "Rocket V (ロケットV)",
                "year": 1970,
                "approx": False,
                "themes": ["space", "science-fiction"],
                "cite": LISTING,
                "note": 'The eremeka catalog lists "1970 Rocket V by Showa Yuen".',
            },
        ],
    },
    {
        "mfg": (
            "childrens-amusement-park-facilities",
            "Children's Amusement Park Facilities",
        ),
        "ce": (
            "childrens-amusement-park-facilities",
            "Children's Amusement Park Facilities",
        ),
        "loc": ["japan"],
        "ce_note": 'The eremeka catalog credits 児童遊園設備 ("Children\'s Amusement Park Facilities") with the space-patrol EM game c.1968.',
        "models": [
            {
                "slug": "space-patrol-childrens",
                "game_format": "pinball",
                "technology_generation": "electromechanical",
                "name": "Space Patrol (宇宙パトロール)",
                "year": 1968,
                "approx": True,
                "themes": ["space", "science-fiction"],
                "cite": LISTING,
                "note": "The eremeka catalog dates this to approximately 1968 (marked ~) by Children's Amusement Park Facilities.",
            },
        ],
    },
    {
        # HQ city (Shinagawa) is a Wikipedia fact, not an eremeka one, so its
        # location is asserted in 0049 cited to Wikipedia (which also dates its
        # end) — not here under the eremeka cite.
        "mfg": ("banpresto", "Banpresto"),
        "ce": ("banpresto", "Banpresto Co., Ltd."),
        "loc": [],
        "ce_note": "In the eremeka catalog, Banpresto appears for two prize-dispenser flipper games (1999 and 2002).",
        "models": [
            {
                "slug": "muden-kun",
                "game_format": "miscellaneous",
                "name": "Muden Kun (むでんくん)",
                "year": 1999,
                "approx": False,
                "themes": [],
                "cite": LISTING,
                "note": 'The eremeka catalog lists "1999 Muden Kun [shooting game] by Banpresto", a prize-dispenser flipper game.',
            },
            {
                "slug": "kinnikuman-ii-power-mucho",
                "game_format": "miscellaneous",
                "name": "Kinnikuman II Power Mucho (キン肉マン2世 パワームーチョ)",
                "year": 2002,
                "approx": False,
                "themes": ["licensed"],
                "cite": LISTING,
                "note": 'The eremeka catalog lists "2002 Kinnikuman II Power Mucho by Banpresto", a licensed Kinnikuman prize-dispenser flipper game.',
            },
        ],
    },
    {
        # HQ city (Higashi-Osaka) is a Mynavi fact, asserted in 0049 under the
        # Mynavi cite (which also marks it ongoing), not here under eremeka.
        "mfg": ("tomato-land", "Tomato Land"),
        "ce": ("tomato-land", "Tomato Land Co., Ltd."),
        "loc": [],
        "ce_note": 'In the eremeka catalog, Tomato Land appears for candy-vending "Target Machine" flipper games (2007-2010).',
        "models": [
            {
                "slug": "target-machine-base-ball",
                "game_format": "miscellaneous",
                "name": "Target Machine Base Ball (ターゲットマシン ベースボール)",
                "year": 2007,
                "approx": False,
                "themes": ["baseball"],
                "cite": LISTING,
                "note": 'The eremeka catalog lists "2007 Target Machine Base Ball by Tomato Land", a candy-vending flipper game.',
            },
            {
                "slug": "target-machine-type-1",
                "game_format": "miscellaneous",
                "name": "Target Machine Type 1 (ターゲットマシン タイプ１)",
                "year": 2007,
                "approx": True,
                "themes": [],
                "cite": LISTING,
                "note": "The eremeka catalog dates this Target Machine (Tropical Q) to approximately 2007 (marked ~) by Tomato Land.",
            },
            {
                "slug": "target-machine-pirates",
                "game_format": "miscellaneous",
                "name": "Target Machine Pirates (ターゲットマシン パイレーツ)",
                "year": 2010,
                "approx": True,
                "themes": ["pirates", "boats"],
                "cite": LISTING,
                "note": "The eremeka catalog dates this pirate-themed Target Machine to approximately 2010 (marked ~) by Tomato Land.",
            },
        ],
    },
    {
        # HQ (Nakano, Tokyo) is an AMpress fact, asserted in 0049.
        "mfg": ("towa", "Towa"),
        "ce": ("towa", "Towa"),
        "loc": [],
        "ce_note": "The eremeka catalog credits トーワ (Towa) with the hockey flipper game Slap Shot c.1996.",
        "models": [
            {
                "slug": "slap-shot-towa",
                "game_format": "miscellaneous",
                "name": "Slap Shot (スラップショット)",
                "year": 1996,
                "approx": False,
                "themes": ["hockey"],
                "cite": LISTING,
                "note": 'The eremeka catalog lists "1996 Slap Shot by Towa", a hockey flipper game (also shown in a 1997 version).',
            },
        ],
    },
    {
        # HQ city (Mitaka) is a Weblio fact, asserted in 0049 under the Weblio
        # cite (which also dates its bankruptcy), not here under eremeka.
        "mfg": ("sunwise", "Sunwise"),
        "ce": ("sunwise", "Sunwise"),
        "loc": [],
        "ce_note": "In the eremeka catalog, Sunwise appears for American Battle Dome (1995), co-developed with Tsukuda Original.",
        "models": [
            {
                "slug": "american-battle-dome",
                "game_format": "miscellaneous",
                "name": "American Battle Dome (アメリカンバトルゲーム)",
                "year": 1995,
                "approx": False,
                "themes": [],
                "cite": LISTING,
                "note": 'The eremeka catalog lists "1995 American Battle Dome by Sunwise & Tsukuda Original".',
            },
        ],
    },
]

# --------------------------------------------------------------------------- #
# 0044 — gap-fill models under existing makers (by existing CE slug)
# --------------------------------------------------------------------------- #
GAPFILL = [
    # Sankyo -> primary CE (not the duplicate yuen entity; we are not merging)
    {
        "ce": "sankyo-precision-equipment-company-ltd",
        "slug": "big-race-sankyo",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Big Race (ビックレース)",
        "year": 1969,
        "approx": True,
        "themes": ["cars"],
        "cite": f"{BLOG}/2024/06/big-race-by-sankyo.html",
        "note": 'The eremeka catalog dates this to approximately 1969 (marked ~) by Sankyo; Early Arcades Japan notes it "appeared in the 1969 machine directory, but could be from an earlier year."',
    },
    {
        "ce": "sankyo-precision-equipment-company-ltd",
        "slug": "japan-series",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Japan Series (日本シリーズ)",
        "year": 1969,
        "approx": True,
        "themes": ["baseball"],
        "cite": LISTING,
        "note": "The eremeka catalog dates this baseball game to approximately 1969 (marked ~) by Sankyo.",
    },
    {
        "ce": "sankyo-precision-equipment-company-ltd",
        "slug": "advantage",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Advantage (アドバンテージ)",
        "year": 1976,
        "approx": False,
        "themes": ["tennis"],
        "cite": LISTING,
        "note": 'The eremeka catalog lists "1976 Advantage by Sankyo", a tennis game.',
    },
    {
        "ce": "sankyo-precision-equipment-company-ltd",
        "slug": "american-football",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "American Football (アメリカンフットボール)",
        "year": 1976,
        "approx": False,
        "themes": ["american-football", "america"],
        "cite": LISTING,
        "note": 'The eremeka catalog lists "1976 American Football by Sankyo".',
    },
    {
        "ce": "sankyo-precision-equipment-company-ltd",
        "slug": "new-world-series",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "New World Series (ニューワールドシリーズ)",
        "year": 1976,
        "approx": False,
        "themes": ["baseball"],
        "cite": f"{BLOG}/2022/06/the-world-series-by-sankyo.html",
        "note": 'Early Arcades Japan says "The 1976 re-release is referred to as New World Series in Sankyo\'s advertisements."',
    },
    # Komaya
    {
        "ce": "komaya-co-ltd",
        "slug": "crazy-15-mark-ii",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Crazy 15 [Mark II] (クレイジー15ゲーム)",
        "year": 1965,
        "approx": False,
        "themes": [],
        "cite": f"{BLOG}/2022/03/15-crazy-15-by-komaya.html",
        "note": 'The eremeka catalog lists "1965 Crazy 15 game [mark II] by Komaya".',
    },
    {
        "ce": "komaya-co-ltd",
        "slug": "crazy-15-mark-iii",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Crazy 15 [Mark III] (クレイジー15ゲーム)",
        "year": 1969,
        "approx": False,
        "themes": [],
        "cite": f"{BLOG}/2022/04/1970-15-2nd-version-crazy-15-by-komaya.html",
        "note": 'The eremeka catalog lists "1969 Crazy 15 game mark III by Komaya".',
    },
    {
        "ce": "komaya-co-ltd",
        "slug": "saturn-komaya",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Saturn (サターン号)",
        "year": 1969,
        "approx": True,
        "themes": ["space", "science-fiction"],
        "cite": LISTING,
        "note": "The eremeka catalog dates this space-themed game to approximately 1969 (marked ~) by Komaya.",
    },
    {
        "ce": "komaya-co-ltd",
        "slug": "ware-sea-rover",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Ware Sea Rover (海賊ゲーム)",
        "year": 1969,
        "approx": True,
        "themes": ["pirates", "boats"],
        "cite": LISTING,
        "note": "The eremeka catalog dates this pirate game to approximately 1969 (marked ~) by Komaya.",
    },
    {
        "ce": "komaya-co-ltd",
        "slug": "ronin",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Ronin (浪人)",
        "year": 1970,
        "approx": False,
        "themes": ["japanese-culture", "martial-arts"],
        "cite": f"{BLOG}/2023/05/1970-ronin.html",
        "note": 'The eremeka catalog lists "1970 Ronin by Komaya".',
    },
    {
        "ce": "komaya-co-ltd",
        "slug": "pocket-ball",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Pocket Ball (ポケットボール)",
        "year": 1974,
        "approx": False,
        "themes": ["tennis"],
        "cite": LISTING,
        "note": 'The eremeka catalog lists "1974 Pocket Ball by Komaya".',
    },
    # Universal (Japan)
    {
        "ce": "universal-company-ltd",
        "slug": "orienteering",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Orienteering (オリエンテーリング)",
        "year": 1976,
        "approx": False,
        "themes": [],
        "cite": LISTING,
        "note": 'The eremeka catalog lists "1976 Orienteering by Universal".',
    },
    # Nihon Gorakuki
    {
        "ce": "japan-amusement-machine-company-ltd",
        "slug": "ultra-spark",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Ultra Spark (ウルトラスパーク)",
        "year": 1972,
        "approx": True,
        "themes": ["monsters", "robots", "licensed"],
        "cite": f"{BLOG}/2024/03/1972-ultra-attack-by-nihon-gorakuki.html",
        "note": "The eremeka catalog dates this kaiju/mecha game to approximately 1972 (marked ~), co-credited to Nihon Gorakuki and Nihon Tenbo.",
    },
    # Nihon Jidou Hanbaiki
    {
        "ce": "japan-automatic-vending-machine-company-ltd",
        "slug": "rodeo-game-mate",
        "game_format": "pinball",
        "technology_generation": "electromechanical",
        "name": "Rodeo (ロデオ)",
        "year": 1969,
        "approx": True,
        "themes": ["rodeo"],
        "cite": LISTING,
        "note": "The eremeka catalog dates this to approximately 1969 (marked ~) by Nihon Jidou Hanbaiki (Game Mate).",
    },
]

# Aliases split by what the name refers to (bare strings, no cite — self-evident):
# a brand/short name -> the MANUFACTURER; a full company name -> the CORPORATE ENTITY.
# When a maker's manufacturer name == its CE name, all its aliases ride on the CE.
# manufacturer_alias on the new makers' 0043 create entries:
MFG_ALIASES = {
    "nihon-tenbo": ["Nitten"],  # brand abbreviation (日展, of 日本展望)
    "banpresto": ["バンプレスト"],
    "tomato-land": ["トマトランド"],
}

# corporate_entity_alias on the new makers' 0044 create entries (keyed by CE slug):
NEW_CE_ALIASES = {
    "nihon-tenbo-goraku-sha": ["日本展望娯楽社", "Japan Outlook Entertainment Company"],
    "kato": ["カトウ", "カトウ製作所", "Kato Seisakusho"],
    "showa-yuen": ["昭和遊園"],
    "childrens-amusement-park-facilities": ["児童遊園設備", "Jidō Yūen Setsubi"],
    "towa": ["トーワ", "トーワジャパン", "Towa Japan"],
    "sunwise": ["サンワイズ"],
}

# Existing makers (seed/IPDB), aliased via guarded assert entries. Brand short names
# go on the manufacturer; the company-name kanji (精機 "precision machinery",
# 製作所 "manufacturing works", 遊園設備 "amusement-park equipment", etc.) on the CE.
# (slug, current name for the guard, aliases)
EXISTING_MFG_ALIASES = [
    ("sankyo-seiki", "Sankyo Seiki", ["三共"]),
    (
        "sankyo-yuen-setsubi-kabushikigaisha",
        "Sankyo Yuen Setsubi Kabushikigaisha",
        ["三共"],
    ),
    ("komaya-seisakusho", "Komaya Seisakusho", ["こまや"]),
    ("universal", "Universal", ["ユニバーサル"]),
    (
        "nihon-jidou-hanbaiki-kabushikigaisha",
        "Nihon Jidou Hanbaiki Kabushikigaisha",
        ["Game Mate"],
    ),
]
EXISTING_CE_ALIASES = [
    (
        "sankyo-precision-equipment-company-ltd",
        "Sankyo Precision Equipment Company, Ltd.",
        ["三共精機"],
    ),
    (
        "sankyo-amusement-park-equipment-company-ltd-ofjapan",
        "Sankyo Amusement Park Equipment Company, Ltd., ofJapan",
        ["三共遊園設備"],
    ),
    ("komaya-co-ltd", "Komaya Co., Ltd.", ["こまや製作所"]),
    (
        "japan-amusement-machine-company-ltd",
        "Japan Amusement Machine Company, Ltd.",
        ["日本娯楽機"],
    ),
    (
        "japan-automatic-vending-machine-company-ltd",
        "Japan Automatic Vending Machine Company, Ltd.",
        ["日本自動販売機"],
    ),
]


# --------------------------------------------------------------------------- #
# live preflight: collisions, location + theme + CE existence
# --------------------------------------------------------------------------- #
def die(msg):
    raise SystemExit(f"PREFLIGHT: {msg}")


# Regenerating over an already-applied DB (iterating on an applied set): set
# PATCHKIT_ALLOW_EXISTING=1 to downgrade the "new entity already exists" collision
# guards to warnings. The emitted YAML is identical either way.
ALLOW_EXISTING = bool(os.environ.get("PATCHKIT_ALLOW_EXISTING"))


def collide(msg):
    print(f"  (allowed) {msg}") if ALLOW_EXISTING else die(msg)


new_mfg = [m["mfg"][0] for m in NEW_MAKERS]
new_ce = [m["ce"][0] for m in NEW_MAKERS]
new_models = [mm["slug"] for m in NEW_MAKERS for mm in m["models"]] + [
    g["slug"] for g in GAPFILL
]
orphan_ids = [o["ipdb_id"] for m in NEW_MAKERS for o in m.get("orphans", [])]

for s in new_mfg:
    if Manufacturer.objects.filter(slug=s).exists():
        collide(f"manufacturer slug {s!r} already exists")
for s in set(new_ce):
    if CorporateEntity.objects.filter(slug=s).exists():
        collide(f"corporate-entity slug {s!r} already exists")
for s in new_models:
    if MachineModel.objects.filter(slug=s).exists():
        collide(f"model slug {s!r} already exists (collision)")
    if Title.objects.filter(slug=s).exists():
        collide(f"title slug {s!r} already exists (collision)")
if len(new_models) != len(set(new_models)):
    die("duplicate model slug within this run")

# existing CEs referenced by gapfill must exist
for s in {g["ce"] for g in GAPFILL}:
    if not CorporateEntity.objects.filter(slug=s).exists():
        die(f"gapfill target CE {s!r} missing")

# existing makers / CEs we attach aliases to must exist with the guarded name
for slug, name, _ in EXISTING_MFG_ALIASES:
    if not Manufacturer.objects.filter(slug=slug, name=name).exists():
        die(f"existing manufacturer {slug!r} (name {name!r}) missing or renamed")
for slug, name, _ in EXISTING_CE_ALIASES:
    if not CorporateEntity.objects.filter(slug=slug, name=name).exists():
        die(f"existing corporate-entity {slug!r} (name {name!r}) missing or renamed")

# locations must exist (relationship members can't be created same-patch)
for m in NEW_MAKERS:
    for p in m["loc"]:
        if not Location.objects.filter(location_path=p).exists():
            die(f"location {p!r} missing (create it in an earlier patch)")

# every theme slug must resolve
all_themes = {t for m in NEW_MAKERS for mm in m["models"] for t in mm["themes"]}
all_themes |= {t for m in NEW_MAKERS for o in m.get("orphans", []) for t in o["themes"]}
all_themes |= {t for g in GAPFILL for t in g["themes"]}
have_themes = set(
    Theme.objects.filter(slug__in=all_themes).values_list("slug", flat=True)
)
if all_themes - have_themes:
    die(f"unknown theme slugs: {sorted(all_themes - have_themes)}")

# orphan models must exist with the expected ipdb_id
live_orphans = {
    m["ipdb_id"]: m["slug"]
    for m in MachineModel.objects.filter(ipdb_id__in=orphan_ids).values(
        "ipdb_id", "slug"
    )
}
pk.check_resolved(orphan_ids, live_orphans)
for m in NEW_MAKERS:
    for o in m.get("orphans", []):
        if live_orphans[o["ipdb_id"]] != o["slug"]:
            die(
                f"orphan ipdb_id={o['ipdb_id']} slug drift: {o['slug']!r} != live {live_orphans[o['ipdb_id']]!r}"
            )


# --------------------------------------------------------------------------- #
# build — split by entity depth: creating an FK target and referencing it in the
# same patch is unsupported, so manufacturers (0043) -> corporate-entities (0044)
# -> models (0045), each referencing the prior patch's committed rows.
# --------------------------------------------------------------------------- #
e_mfg, e_ce, e_title, e_model = [], [], [], []
# (slug, name) of every model we CREATE (not the orphan reassigns, which already
# have titles): each needs a single-model Title sharing its slug, made first.
created = []


def abbr(name):
    """The Japanese name as a one-member abbreviation list, or None."""
    jp = jp_name(name)
    return [jp] if jp else None


for m in NEW_MAKERS:
    mfg_slug, mfg_name = m["mfg"]
    ce_slug, ce_name = m["ce"]
    e_mfg.append(
        emit(
            f"manufacturer.{mfg_slug}",
            create=True,
            fields={"name": mfg_name},
            cite=LISTING,
            note=m["ce_note"],
            aliases=MFG_ALIASES.get(mfg_slug),
        )
    )
    e_ce.append(
        emit(
            f"corporate-entity.{ce_slug}",
            create=True,
            fields={"name": ce_name, "manufacturer": mfg_slug},
            location=m["loc"],
            ce_aliases=NEW_CE_ALIASES.get(ce_slug),
            cite=LISTING,
            note=f"Corporate entity of {mfg_name}, per the eremeka catalog.",
        )
    )
    for mm in m["models"]:
        created.append((mm["slug"], mm["name"]))
        fields = {
            "name": mm["name"],
            "year": mm["year"],
            "title": mm["slug"],
            "corporate_entity": ce_slug,
            "game_format": mm["game_format"],  # required per-model; no default
        }
        if "technology_generation" in mm:
            fields["technology_generation"] = mm["technology_generation"]
        e_model.append(
            emit(
                f"model.{mm['slug']}",
                create=True,
                fields=fields,
                themes=mm["themes"] or None,
                abbreviations=abbr(mm["name"]),
                cite=mm["cite"],
                note=mm["note"],
            )
        )
    for o in m.get("orphans", []):
        e_model.append(
            emit(
                f"model.{o['slug']}",
                expect={"ipdb_id": o["ipdb_id"]},
                fields={
                    "corporate_entity": ce_slug,
                    "year": o["year"],
                    "game_format": o["game_format"],
                },
                themes=o["themes"] or None,
                cite=o["cite"],
                note=o["note"],
            )
        )
# alias-only entries for the existing Japanese makers (no cite — self-evident names):
# brand short names on the manufacturer, company-name kanji on the corporate entity
for slug, name, aliases in EXISTING_MFG_ALIASES:
    e_mfg.append(emit(f"manufacturer.{slug}", expect={"name": name}, aliases=aliases))
for slug, name, ce_aliases in EXISTING_CE_ALIASES:
    e_ce.append(
        emit(f"corporate-entity.{slug}", expect={"name": name}, ce_aliases=ce_aliases)
    )
for g in sorted(GAPFILL, key=lambda x: (x["ce"], x["slug"])):
    created.append((g["slug"], g["name"]))
    e_model.append(
        emit(
            f"model.{g['slug']}",
            create=True,
            fields={
                "name": g["name"],
                "year": g["year"],
                "title": g["slug"],
                "corporate_entity": g["ce"],
                "game_format": g["game_format"],  # required per-model; no default
                **(
                    {"technology_generation": g["technology_generation"]}
                    if "technology_generation" in g
                    else {}
                ),
            },
            themes=g["themes"] or None,
            abbreviations=abbr(g["name"]),
            cite=g["cite"],
            note=g["note"],
        )
    )
for slug, name in created:
    e_title.append(
        emit(
            f"title.{slug}",
            create=True,
            fields={"name": name},
            abbreviations=abbr(name),
            cite=LISTING,
            note=f"Title for {name}, per the eremeka catalog.",
        )
    )

pk.write_patch(
    OUT / "0043-japanese-manufacturers.yaml",
    attribution="flipcommons-catalog",
    description="New early-Japanese manufacturers, with aliases.",
    entries=e_mfg,
)
pk.write_patch(
    OUT / "0044-japanese-corporate-entities.yaml",
    attribution="flipcommons-catalog",
    description="Corporate entities for the new early-Japanese manufacturers, with aliases.",
    entries=e_ce,
)
pk.write_patch(
    OUT / "0045-japanese-titles.yaml",
    attribution="flipcommons-catalog",
    description="Titles for the early-Japanese models, created before the models that reference them.",
    entries=e_title,
)
pk.write_patch(
    OUT / "0046-japanese-models.yaml",
    attribution="flipcommons-catalog",
    description="Early-Japanese models.",
    entries=e_model,
)

print(
    f"wrote 0043 mfg ({len(e_mfg)}), 0044 ce ({len(e_ce)}), "
    f"0045 titles ({len(e_title)}), 0046 models ({len(e_model)})"
)
