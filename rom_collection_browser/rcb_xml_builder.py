import os
import re
from datetime import datetime

import lxml.builder
import lxml.etree
from the_games_db import TheGamesDb

IMAGE_TYPES = {
    "screenshot": "screenshots/",
    "boxback": "boxart/back/",
    "boxfront": "boxart/front/",
    "gameplay": "gameplay/",
    "clearlogo": "clearlogo/",
    "fanart": "fanart/",
    "cartridge": "cartridge/",
}


class RcbXmlBuilder:
    def __init__(self, the_games_db: TheGamesDb, artwork_root):
        self.the_games_db = the_games_db
        self.artwork_root = artwork_root

    def get_image_filename(self, game_db, image_type):
        game_db_id = game_db["id"]
        if image_type in IMAGE_TYPES.keys():
            image_type_path = IMAGE_TYPES[image_type]
            image_path = os.path.join(
                self.artwork_root, f"{image_type_path}{game_db_id}-1.jpg"
            )
            if os.path.isfile(image_path):
                return image_path
        return ""

    regions = {
        "(Australia)": "Australia",
        "(Brazil)": "Brazil",
        "(Canada)": "Canada",
        "(Europe)": "Europe",
        "(France)": "France",
        "(Germany)": "Germany",
        "(Hong Kong)": "Hong Kong",
        "(Italy)": "Italy",
        "(Japan)": "Japan",
        "(Korea)": "Korea",
        "(Netherlands)": "Netherlands",
        "(Spain)": "Spain",
        "(Sweden)": "Sweden",
        "(USA)": "USA",
    }

    def region_from_game_name(self, game_name):
        for region in self.regions.keys():
            regexp = re.compile(region)
            if regexp.search(game_name):
                return self.regions[region]
        return ""

    def generate_xml(self, game_db, no_intro):
        # Get RCB platform
        rcb_platform = self.the_games_db.get_rcb_platform_from_id(game_db["platform"])

        # region
        release = no_intro.get("release", None)
        region = None
        if release is not None:
            region = release.get("@region", None)
        if region is None:
            region = self.region_from_game_name(no_intro["@name"])

        # version

        e = lxml.builder.ElementMaker()
        try:
            xml = e.game(
                e.title(game_db["game_title"]),
                e.originalTitle(no_intro["@name"]),
                e.alternateTitle(),
                e.platform(rcb_platform),
                e.plot(game_db["overview"]),
                e.publisher(),
                e.developer(),
                e.year(
                    str(datetime.strptime(game_db["release_date"], "%Y-%m-%d").year)
                ),
                e.detailUrl(),
                e.maxPlayer(str(game_db["players"])),
                e.region(region),
                e.media(),
                e.perspective(),
                e.controller(),
                e.version(),
                e.rating(),
                e.votes(),
                e.isFavorite(),
                e.launchCount(str(0)),
                e.genre(),
                e.thumb(
                    local=self.get_image_filename(game_db, "screenshot"),
                    type="screenshot",
                ),
                e.thumb(
                    local=self.get_image_filename(game_db, "boxback"), type="boxback"
                ),
                e.thumb(
                    local=self.get_image_filename(game_db, "boxfront"), type="boxfront"
                ),
                e.thumb(
                    local=self.get_image_filename(game_db, "gameplay"), type="gameplay"
                ),
                e.thumb(
                    local=self.get_image_filename(game_db, "clearlogo"),
                    type="clearlogo",
                ),
                e.thumb(
                    local=self.get_image_filename(game_db, "fanart"), type="fanart"
                ),
                e.thumb(
                    local=self.get_image_filename(game_db, "cartridge"),
                    type="cartridge",
                ),
            )
        except Exception as exception:
            print(exception)
            return None

        return lxml.etree.tostring(xml, pretty_print=True).decode("utf-8")
