import json
from os import path

import requests

API_KEY = "1e821bf1bab06854840650d77e7e2248f49583821ff9191f2cced47e43bf0a73"

# thegamesdb URLs:
THE_GAMES_DB_DEVELOPERS_URL = "https://api.thegamesdb.net/v1/Developers"
THE_GAMES_DB_GAME_URL = "https://cdn.thegamesdb.net/json/database-latest.json"
THE_GAMES_DB_GENRES_URL = "https://api.thegamesdb.net/v1/Genres"
THE_GAMES_DB_PLATFORM_URL = "https://api.thegamesdb.net/v1/Platforms"
THE_GAMES_DB_PUBLISHERS_URL = "https://api.thegamesdb.net/v1/Publishers"

# thegamesdb local jsons
THE_GAMES_DB_DEVELOPERS_JSON = "../config/thegamesdb_developers.json"
THE_GAMES_DB_GAME_JSON = "../config/thegamesdb_games.json"
THE_GAMES_DB_GENRES_JSON = "../config/thegamesdb_genres.json"
THE_GAMES_DB_PLATFORM_JSON = "../config/thegamesdb_platforms.json"
THE_GAMES_DB_PUBLISHERS_JSON = "../config/thegamesdb_publishers.json"


class TheGamesDb:
    def _get_data_from_api(self, url, output_file):
        if not path.isfile(output_file):
            params = {
                "apikey": API_KEY,
            }
            r = requests.get(url=url, params=params)
            data = r.json()
            with open(output_file, "w") as outfile:
                json.dump(data, outfile)
        with open(output_file, "r") as infile:
            json_data = json.load(infile)
        return json_data

    def _get_data_from_url(self, url, output_file):
        if not path.isfile(output_file):
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(output_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            # f.flush()
        with open(output_file, "r") as infile:
            json_data = json.load(infile)
        return json_data

    def __init__(self):
        # Get the json game list (this is a giant json)
        self.games = self._get_data_from_url(
            THE_GAMES_DB_GAME_URL, THE_GAMES_DB_GAME_JSON
        )

        # Get the individual
        self.platforms = self._get_data_from_api(
            THE_GAMES_DB_PLATFORM_URL, THE_GAMES_DB_PLATFORM_JSON
        )
        self.publishers = self._get_data_from_api(
            THE_GAMES_DB_PUBLISHERS_URL, THE_GAMES_DB_PUBLISHERS_JSON
        )
        self.developers = self._get_data_from_api(
            THE_GAMES_DB_DEVELOPERS_URL, THE_GAMES_DB_DEVELOPERS_JSON
        )
        self.genres = self._get_data_from_api(
            THE_GAMES_DB_GENRES_URL, THE_GAMES_DB_GENRES_JSON
        )
        return

    def _clean_game_name(self, game_name: str):
        # Remove out Country
        game_name = game_name.replace(" (USA)", "")
        return game_name

    def get_platform_id_by_name(self, platform_name):
        for platform in list(self.platforms["data"]["platforms"].values()):
            if platform_name == platform["name"]:
                return platform["id"]

    def get_id_by_name(self, game_name, platform_id):
        game_name = self._clean_game_name(game_name)
        for game in self.games["data"]["games"]:
            if game["GameTitle"] == game_name and platform_id == game["SystemId"]:
                return game["id"]
