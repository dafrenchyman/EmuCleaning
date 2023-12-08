import datetime
import json
import os
import sqlite3
import time
from typing import List

import pandas
import requests
from fuzzywuzzy import fuzz
from igdb.wrapper import IGDBWrapper

CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
API_KEY = os.getenv("IGDB_API_KEY")

PLATFORM_TO_WHERE_CAUSE = {
    # "Unknown": 'search "platform_name";'
    "3do": 'where name = ("3DO Interactive Multiplayer");',
    "amiga": 'where name = ("Amiga");',
    "arcade": 'where name = ("Arcade");',
    "atari2600": 'where name = ("Atari 2600");',
    "atari5200": 'where name = ("Atari 5200");',
    "atari7800": 'where name = ("Atari 7800");',
    "atarijaguar": 'where name = ("Atari Jaguar");',
    "atarilynx": 'where name = ("Atari Lynx");',
    "atarist": 'where name = ("Atari ST/STE");',
    "cdtv": 'where name = ("Commodore CDTV");',
    "colecovision": 'where name = ("ColecoVision");',
    "cpet": 'where name = ("Commodore PET");',
    "dreamcast": 'where name = ("Dreamcast");',
    "gameandwatch": 'where name = ("Game & Watch");',
    "gb": 'where name = ("Game Boy");',
    "gba": 'where name = ("Game Boy Advance");',
    "gbc": 'where name = ("Game Boy Color");',
    "gc": 'where name = ("Nintendo GameCube");',
    "genesis": 'where name = ("Sega Mega Drive/Genesis");',
    "ios": 'where name = ("iOS");',
    "mastersystem": 'where name = ("Sega Master System/Mark III");',
    "n3ds": 'where name = ("Nintendo 3DS");',
    "n64": 'where name = ("Nintendo 64");',
    "n64dd": 'where name = ("Nintendo 64DD");',
    "nds": 'where name = ("Nintendo DSi", "Nintendo DS");',
    "neogeo": 'where name = ("Neo Geo AES");',
    "nes": 'where name = ("Nintendo Entertainment System");',
    "ngp": 'where name = ("Neo Geo Pocket");',
    "ngpc": 'where name = ("Neo Geo Pocket Color");',
    "odyssey": 'where name = ("Odyssey");',
    "plus4": 'where name = ("Commodore Plus/4");',
    "ps2": 'where name = ("PlayStation 2");',
    "ps3": 'where name = ("PlayStation 3");',
    "ps4": 'where name = ("PlayStation 4", "PlayStation VR");',
    "ps5": 'where name = ("PlayStation 5", "PlayStation VR2");',
    "psp": 'where name = ("PlayStation Portable");',
    "psx": 'where name = ("PlayStation");',
    "psvita": 'where name = ("PlayStation Vita");',
    "saturn": 'where name = ("Sega Saturn");',
    "sega32x": 'where name = ("Sega 32X");',
    "segacd": 'where name = ("Sega CD");',
    "segapico": 'where name = ("Sega Pico")',
    "snes": 'where name = ("Super Nintendo Entertainment System", "Super Famicom");',
    "snes_widescreen": 'where name = ("Super Nintendo Entertainment System", "Super Famicom");',
    "switch": 'where name = ("Nintendo Switch");',
    "virtualboy": 'where name = ("Virtual Boy");',
    "wii": 'where name = ("Wii");',
    "wiiu": 'where name = ("WiiU");',
    "xbox": 'where name = ("Xbox");',
    "xbox360": 'where name = ("Xbox 360");',
    "xboxone": 'where name = ("Xbox One");',
    "xboxseriesx": 'where name = ("Xbox Series X|S");',
}


class InternetGameDb:
    def __init__(self, platform: str) -> None:
        self.platform = platform

        if platform not in PLATFORM_TO_WHERE_CAUSE.keys():
            raise ValueError(f"Invalid platform: {platform}")

        self.expired_time = datetime.datetime.now()
        self.igdb = self.get_wrapper()
        self.last_request = datetime.datetime.now()

        db_file = f"{os.path.dirname(__file__)}/../database/igdb.db"
        self.engine = sqlite3.connect(db_file)
        self._cursor = self.engine.cursor()

        # Create local caching tables
        self._create_tables()

        # Need the platform id to do lookups later
        self.platform_id = self.get_platform_id_by_name(platform)
        if len(self.platform_id) == 0:
            raise NotImplementedError(f"Platform {platform} not found in IGDB")
        return

    def __del__(self):
        self.engine.commit()
        self._cursor.close()
        self.engine.close()

    def _create_tables(self) -> None:
        # requests
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT NOT NULL,
                query TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """
        )
        self._cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS requests_endpoint_query_uidx ON
                requests (endpoint, query)
            """
        )

        # platforms
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                platform TEXT
            )
            """
        )
        self.engine.commit()
        return

    def get_platform_id_by_name(self, platform_name) -> List[str]:
        where_clause = PLATFORM_TO_WHERE_CAUSE[platform_name]
        platforms = self.run_request(
            endpoint="platforms", query=f"fields *; {where_clause}"
        )
        platform_ids = [i["id"] for i in platforms]
        return platform_ids

    def run_request(self, endpoint, query):
        # Remove quotes or SQL query will fail (can't seem to escape them)
        query_sql = query.replace("'", "")

        # check if value is cached in local sqlite first
        df = pandas.read_sql(
            f"""
            SELECT * FROM requests
            WHERE endpoint='{endpoint}' AND query='{query_sql}'""",
            self.engine,
        )
        if df.shape[0] > 0:
            results = json.loads(df["result"][0])
        else:
            # We can only do 4 requests per second. Wait to make sure we haven't reached the limit
            now = datetime.datetime.now()
            if self.last_request + datetime.timedelta(seconds=0.25) > now:
                duration = now - self.last_request + datetime.timedelta(seconds=0.25)
                time.sleep(duration.total_seconds())

            byte_array = self.igdb.api_request(endpoint, query)
            self.last_request = datetime.datetime.now()
            result_string = byte_array.decode("utf-8")

            # store results in DB
            self._cursor.execute(
                f"""
                INSERT INTO requests (endpoint, query, result)
                VALUES('{endpoint}', '{query_sql}', '{result_string}')
            """
            )
            self.engine.commit()

            results = json.loads(result_string)
        return results

    def get_wrapper(self):
        if datetime.datetime.now() > self.expired_time:
            token_url = f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={API_KEY}&grant_type=client_credentials"
            token_request = requests.post(token_url)
            data = json.loads(token_request.text)

            self.expired_time = datetime.datetime.now() + datetime.timedelta(
                seconds=data["expires_in"]
            )  # days, seconds, then other fields.
            self.token = data["access_token"]

        return IGDBWrapper(CLIENT_ID, self.token)

    def get_game_from_game_name(self, game_name: str):
        # game_name = game_name.replace("\'", "")
        platform_str = ",".join([str(i) for i in self.platform_id])
        games = self.run_request(
            endpoint="games",
            query=f'search "{game_name}"; fields *; where platforms = ({platform_str});',
        )

        best_fuzz_score = 0
        best_match = None

        for game in games:
            fuzz_score = fuzz.ratio(game_name, game["name"])
            if fuzz_score > 90 and fuzz_score > best_fuzz_score:
                best_fuzz_score = fuzz_score
                best_match = game

        # if we found a "best match" Process it
        if best_match is not None:
            if best_match.get("first_release_date", None) is not None:
                # Process First Release Date
                best_match["first_release_date"] = datetime.datetime.utcfromtimestamp(
                    int(best_match.get("first_release_date"))
                ).strftime("%Y-%m-%d")

        return best_match

    def download_all_art(self, game_id: int, art_path: str):
        raise NotImplementedError


def main():
    db = InternetGameDb(platform="atarist")
    game = db.get_game_from_game_name("Super Mario World")
    game


if __name__ == "__main__":
    main()
