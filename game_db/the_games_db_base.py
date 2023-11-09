import os

import pandas
import requests
from fuzzywuzzy import fuzz

THEGAMESDB_JSON_LOCAL = "./database/games-db-database-latest.json"
THEGAMESDB_JSON_URL = "https://cdn.thegamesdb.net/json/database-latest.json"
THEGAMESDB_SQL_DUMP = "http://cdn.thegamesdb.net/tgdb_dump.zip"


PLATFORM_TO_DB_NAME = {
    "3do": "3do",
    "atari2600": "atari-2600",
    "dreamcast": "sega-dreamcast",
    "gameandwatch": "game-and-watch",
    "gamegear": "sega-game-gear",
    "gb": "nintendo-gameboy",
    "gba": "nintendo-gameboy-advance",
    "gbc": "nintendo-gameboy-color",
    "gc": "nintendo-gamecube",
    "genesis": "sega-genesis",
    "mastersystem": "sega-master-system",
    "n3ds": "nintendo-3ds",
    "n64": "nintendo-64",
    "n64dd": "nintendo-64",
    "nds": "nintendo-ds",
    "nes": "nintendo-entertainment-system-nes",
    "ngp": "neo-geo-pocket",
    "ngpc": "neo-geo-pocket-color",
    "ps2": "sony-playstation-2",
    "ps3": "sony-playstation-3",
    "ps4": "sony-playstation-4",
    "ps5": "sony-playstation-5",
    "psp": "sony-psp",
    "psx": "sony-playstation",
    "psvita": "sony-playstation-vita",
    "saturn": "sega-saturn",
    "sega32x": "sega-32x",
    "segacd": "sega-cd",
    "snes": "super-nintendo-snes",
    "switch": "nintendo-switch",
    "wii": "nintendo-wii",
    "wiiu": "nintendo-wii-u",
    "xbox": "microsoft-xbox",
    "xbox360": "microsoft-xbox-360",
    "xboxone": "microsoft-xbox-one",
    "xboxseriesx": "microsoft-xbox-series-x",
}


class TheGamesDbBase:
    def __init__(
        self,
        platform: str,
    ):
        if platform not in PLATFORM_TO_DB_NAME.keys():
            raise ValueError(f"Invalid Platform {platform}")

        self._load_developers()
        self._load_platforms()
        self._load_publishers()
        self._load_genres()

        # Load the platform
        self.platform = platform
        self.platform_id = self.get_platform_id_by_alias(PLATFORM_TO_DB_NAME[platform])
        return

    def _load_developers(self):
        df = pandas.read_sql("SELECT * FROM devs_list", self.engine)
        df["index"] = df["id"]
        self.developers = df.set_index("index").T.to_dict("dict")
        return

    def _load_platforms(self):
        df = pandas.read_sql("SELECT * FROM platforms", self.engine)
        df["index"] = df["id"]
        self.platforms = df.set_index("index").T.to_dict("dict")
        return

    def _load_publishers(self):
        df = pandas.read_sql("SELECT * FROM publishers", self.engine)
        df["index"] = df["id"]
        self.publishers = df.set_index("index").T.to_dict("dict")
        return

    def _load_genres(self):
        df = pandas.read_sql("SELECT * FROM genres", self.engine)
        df["index"] = df["id"]
        self.genres = df.set_index("index").T.to_dict("dict")
        return

    def get_developer_by_id(self, id: int):
        if self.genres is None:
            self._load_developers()
        return self.developers.get(id)

    def get_platform_by_id(self, id: int):
        if self.platforms is None:
            self._load_platforms()
        return self.platforms.get(id)

    def get_platform_id_by_alias(self, alias: str):
        if self.platforms is None:
            self._load_platforms()
        return_id = None
        for platform_id, platform_values in self.platforms.items():
            if platform_values["alias"] == alias:
                return_id = platform_id
                break
        return return_id

    def get_publisher_by_id(self, id: int):
        if self.genres is None:
            self._load_publishers()
        return self.publishers.get(id)

    def get_genre_by_id(self, id: int):
        if self.genres is None:
            self._load_genres()
        return self.genres.get(id)

    def get_games_by_platform_id(self, platform_id: int):
        df = pandas.read_sql(
            f"""SELECT
                id
                , game_title
                , SOUNDEX
                , COALESCE(players, 1) AS players
                , release_date
                , COALESCE(overview, '') AS overview
                , last_updated
                , COALESCE(rating, '') AS rating
                , COALESCE(hits, 0) AS hits
                , disabled
                , platform AS platform_id
                , COALESCE(coop, 'no') AS coop
                , youtube
                , os
                , processor
                , ram
                , hdd
                , video
                , sound
                , region_id
                , country_id
            FROM games WHERE platform = {platform_id}""",
            self.engine,
        )
        df["index"] = df["id"]
        games = df.set_index("index").T.to_dict("dict")
        return games

    def get_genres_by_game_id(self, game_id: int):
        df = pandas.read_sql(
            f"""
        SELECT
            gg.genres_id AS id
            , g.genre
            FROM games_genre gg
            JOIN genres g ON gg.genres_id = g.id
        WHERE games_id = {game_id}
        """,
            self.engine,
        )
        df["index"] = df["id"]
        developers = df.set_index("index").T.to_dict("dict")
        return developers

    def get_developers_by_game_id(self, game_id: int):
        df = pandas.read_sql(
            f"""
        SELECT
            gd.dev_id AS id
            , dl.name AS developer_name
            FROM games_devs gd
            JOIN devs_list dl ON gd.dev_id = dl.id
        WHERE games_id = {game_id}
        """,
            self.engine,
        )
        df["index"] = df["id"]
        developers = df.set_index("index").T.to_dict("dict")
        return developers

    def get_publishers_by_game_id(self, game_id: int):
        df = pandas.read_sql(
            f"""
        SELECT
            gp.pub_id AS id
            , pl.name AS publisher_name
            FROM games_pubs gp
            JOIN pubs_list pl ON gp.pub_id = pl.id
        WHERE gp.games_id = {game_id}
        """,
            self.engine,
        )
        df["index"] = df["id"]
        publishers = df.set_index("index").T.to_dict("dict")
        return publishers

    def get_artwork_from_game_id(self, game_id: int):
        df = pandas.read_sql(
            f"SELECT * FROM banners WHERE games_id = {game_id}", self.engine
        )
        df["index"] = df["id"]
        artwork = df.set_index("index").T.to_dict("dict")
        return artwork

    ALIAS_TO_RCB_PLATFORM = {"super-nintendo-snes": "SNES"}

    def _fix_game_data(self, game):
        game["game_title"] = (
            game.get("game_title", "")
            .replace("&quot;", '"')
            .replace("&#039;", "'")
            .replace("&amp;", "&")
        )
        game["overview"] = (
            game.get("overview", "")
            .replace("&quot;", '"')
            .replace("&#039;", "'")
            .replace("&amp;", "&")
        )
        return game

    def get_games_db_from_game_name(self, game_name):
        best_fuzz_score = 0
        best_fuzz_location = None
        best_match = None

        all_games = self.get_games_by_platform_id(self.platform_id)

        # Loop through every game in the DB and see which one is the best
        for key, game in all_games.items():
            # Fix the game name stuff
            game = self._fix_game_data(game)
            fuzz_score = fuzz.ratio(game_name, game["game_title"])
            if fuzz_score > 90 and fuzz_score > best_fuzz_score:
                best_fuzz_score = fuzz_score
                best_fuzz_location = key

        if best_fuzz_location is not None:
            best_match = all_games.get(best_fuzz_location)
        return best_match

    def get_platform_alias_from_id(self, platform_id):
        platforms = self.the_games_db_json["include"]["platform"]["data"]
        for platform in platforms.keys():
            if platforms[platform]["id"] == platform_id:
                return platforms[platform]["alias"]
        raise (f"Invalid platform alias: {platform_id}")

    def get_rcb_platform_from_alias(self, platform_alias):
        return self.ALIAS_TO_RCB_PLATFORM[platform_alias]

    def get_rcb_platform_from_id(self, platform_id):
        platform_alias = self.get_platform_by_id(platform_id)["alias"]
        return self.get_rcb_platform_from_alias(platform_alias)

    def download_all_art(self, game_db, art_path_root: str):
        art_path = art_path_root + "thegamedb/"
        game_db_id = game_db.get("id", None)

        # Get Image data from database
        game_images = self.get_artwork_from_game_id(game_db_id)
        base_url = "https://cdn.thegamesdb.net/images/original/"

        filename_links = {
            "banner": [],
            "boxart_back": [],
            "boxart_front": [],
            "clearlogo": [],
            "fanart": [],
            "screenshot": [],
            "titlescreen": [],
            "graphical": [],
        }

        for key, image in game_images.items():
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
                elif image["type"].upper() == "BANNER":
                    key = "banner"
                else:
                    raise ValueError(f"Invalid type: {image['type']}")
                filename_links[key].append(image_path)

        return filename_links
