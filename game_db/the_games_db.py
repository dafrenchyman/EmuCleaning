import json
import os

import requests
from fuzzywuzzy import fuzz

THEGAMESDB_JSON_LOCAL = "./database/games-db-database-latest.json"
THEGAMESDB_JSON_URL = "https://cdn.thegamesdb.net/json/database-latest.json"
THEGAMESDB_SQL_DUMP = "http://cdn.thegamesdb.net/tgdb_dump.zip"


class TheGamesDb:
    def __init__(self, json_local):
        if not os.path.exists(json_local):
            game_db_download = requests.get(THEGAMESDB_JSON_URL)
            open(json_local, "wb").write(game_db_download.content)
        with open(json_local, "r") as file:
            self.the_games_db_json = json.loads(file.read())

    ALIAS_TO_RCB_PLATFORM = {"super-nintendo-snes": "SNES"}

    def get_games_db_from_game_name(self, game_name, platform_alias):
        platform_id = self.get_platform_id_from_alias(platform_alias)
        best_fuzz_score = 0
        best_fuzz_location = None
        best_match = None

        # Loop through every game in the DB and see which one is the best
        for i, game in enumerate(self.the_games_db_json["data"]["games"]):
            if game["platform"] == platform_id:
                fuzz_score = fuzz.ratio(game_name, game["game_title"])
                if fuzz_score > 90 and fuzz_score > best_fuzz_score:
                    best_fuzz_score = fuzz_score
                    best_fuzz_location = i

        if best_fuzz_location is not None:
            best_match = self.the_games_db_json["data"]["games"][best_fuzz_location]
        return best_match

    def get_platform_id_from_alias(self, platform_alias):
        platforms = self.the_games_db_json["include"]["platform"]["data"]
        for platform in platforms.keys():
            if platforms[platform]["alias"] == platform_alias:
                return platforms[platform]["id"]
        raise (f"Invalid platform alias: {platform_alias}")

    def get_platform_alias_from_id(self, platform_id):
        platforms = self.the_games_db_json["include"]["platform"]["data"]
        for platform in platforms.keys():
            if platforms[platform]["id"] == platform_id:
                return platforms[platform]["alias"]
        raise (f"Invalid platform alias: {platform_id}")

    def get_rcb_platform_from_alias(self, platform_alias):
        return self.ALIAS_TO_RCB_PLATFORM[platform_alias]

    def get_rcb_platform_from_id(self, platform_id):
        platform_alias = self.get_platform_alias_from_id(platform_id)
        return self.get_rcb_platform_from_alias(platform_alias)

    def download_all_art(self, game_db, art_path: str):
        game_db_id = game_db.get("id", None)

        # Get Image data from database
        game_db_id = str(game_db_id)
        game_images = self.the_games_db_json["include"]["boxart"]["data"][game_db_id]
        base_url = self.the_games_db_json["include"]["boxart"]["base_url"]["original"]

        filename_links = {
            "boxart_back": [],
            "boxart_front": [],
            "clearlogo": [],
            "fanart": [],
            "screenshot": [],
            "titlescreen": [],
            "graphical": [],
        }

        for image in game_images:
            image_filename: str = image["filename"]
            image_path = os.path.join(art_path, image_filename)
            if not os.path.exists(os.path.dirname(image_path)):
                os.makedirs(os.path.dirname(image_path))
            image_url = f"{base_url}{image_filename}"
            have_image = False
            if not os.path.isfile(image_path):
                image_web = requests.get(image_url)
                if image_web.status_code == 200:
                    with open(image_path, "wb") as output:
                        output.write(image_web.content)
                        have_image = True
            else:  # already downloaded
                have_image = True

            if have_image:
                if image["type"].upper() == "BOXART":
                    if image["side"].upper() == "FRONT":
                        key = "boxart_front"
                    elif image["side"].upper() == "BACK":
                        key = "boxart_back"
                    else:
                        raise ValueError(f"Invalid side: {image['side']}")
                elif image["type"].upper() == "FANART":
                    key = "fanart"
                elif image["type"].upper() == "SCREENSHOT":
                    key = "screenshot"
                elif image["type"].upper() == "CLEARLOGO":
                    key = "clearlogo"
                elif image["type"].upper() == "TITLESCREEN":
                    key = "titlescreen"
                elif image["type"].upper() == "GRAPHICAL":
                    key = "graphical"
                else:
                    raise ValueError(f"Invalid type: {image['type']}")
                filename_links[key].append(image_path)

        return filename_links
