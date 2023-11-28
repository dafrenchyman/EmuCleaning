import base64
import os
import pickle
import sqlite3
import time
from pathlib import Path
from typing import List

import pandas
import requests
from fuzzywuzzy import fuzz
from steamgrid import ImageType, MimeType, SteamGridDB, StyleType

API_KEY = os.getenv("STEAM_GRID_DB_API_KEY")


class SteamGridDb:
    def __init__(self, platform) -> None:
        self.sgdb = SteamGridDB(API_KEY)
        self.platform = platform

        db_file = f"{os.path.dirname(__file__)}/../database/steamgriddb.db"
        self.engine = sqlite3.connect(db_file)
        self._cursor = self.engine.cursor()

        # Create local caching tables
        self._create_tables()
        return

    def __del__(self) -> None:
        self.engine.commit()
        self._cursor.close()
        self.engine.close()
        return

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

        self.engine.commit()
        return

    def get_game_id_by_name(self, game_name: str):
        games = self._search_game(game_name)

        best_fuzz_score = 0
        best_match_id = None

        for game in games:
            fuzz_score = fuzz.ratio(game_name, game.name)
            if fuzz_score > 90 and fuzz_score > best_fuzz_score:
                best_fuzz_score = fuzz_score
                best_match_id = game.id
            if best_fuzz_score == 100:
                break
        return best_match_id

    def _get_result_from_local_db(self, endpoint, query):
        # Remove quotes or SQL query will fail (can't seem to escape them)
        query_encoded = base64.b64encode(pickle.dumps(query)).decode("ascii")

        # check if value is cached in local sqlite first
        df = pandas.read_sql(
            f"""
                SELECT * FROM requests
                WHERE endpoint='{endpoint}' AND query='{query_encoded}'
            """,
            self.engine,
        )
        results_decoded = None
        if df.shape[0] > 0:
            result_encoded = df["result"][0]
            results_decoded = pickle.loads(base64.b64decode(result_encoded))
            if results_decoded is None:
                results_decoded = "None"
        return results_decoded

    def _store_result_in_local_db(self, endpoint: str, query: any, grids: any):
        query_encoded = base64.b64encode(pickle.dumps(query)).decode("ascii")
        grids_encoded = base64.b64encode(pickle.dumps(grids)).decode("ascii")

        self._cursor.execute(
            f"""
                INSERT INTO requests (endpoint, query, result)
                VALUES('{endpoint}', '{query_encoded}', '{grids_encoded}')
            """
        )
        self.engine.commit()
        return

    def _search_game(
        self,
        term,
        number_of_attempts: int = 9,
    ):
        term = term.replace("/", " ")
        # See if the result is available locally first
        grids = self._get_result_from_local_db(
            endpoint="search_game",
            query=term,
        )

        if grids is None:
            curr_attempt = 1
            successfully_processed = False
            while not successfully_processed and curr_attempt <= number_of_attempts:
                try:
                    grids = self.sgdb.search_game(
                        term=term,
                    )
                    curr_attempt += 1
                    successfully_processed = True
                    self._store_result_in_local_db(
                        endpoint="search_game", query=term, grids=grids
                    )
                except Exception as e:  # noqa E722
                    print("\tAttempt failed, trying again")
                    time.sleep(5.0)
        elif grids == "None":
            grids = []
        return grids

    def _get_grids_by_gameid(
        self,
        game_ids: List[int],
        styles: List[StyleType] = [],
        mimes: List[MimeType] = [],
        types: List[ImageType] = [],
        is_nsfw: bool = False,
        is_humor: bool = False,
        number_of_attemps: int = 9,
    ):
        # See if the result is available locally first
        grids = self._get_result_from_local_db(
            endpoint="get_grids_by_gameid",
            query=game_ids,
        )

        if grids is None:
            curr_attempt = 1
            successfully_processed = False
            while not successfully_processed and curr_attempt <= number_of_attemps:
                try:
                    grids = self.sgdb.get_grids_by_gameid(
                        game_ids=game_ids,
                        styles=styles,
                        mimes=mimes,
                        types=types,
                        is_nsfw=is_nsfw,
                        is_humor=is_humor,
                    )
                    curr_attempt += 1
                    successfully_processed = True
                    self._store_result_in_local_db(
                        endpoint="get_grids_by_gameid", query=game_ids, grids=grids
                    )
                except:  # noqa E722
                    print("\tAttempt failed, trying again")
                    time.sleep(5.0)
        elif grids == "None":
            grids = None
        return grids

    def _get_logos_by_gameid(
        self,
        game_ids: List[int],
        styles: List[StyleType] = [],
        mimes: List[MimeType] = [],
        types: List[ImageType] = [],
        is_nsfw: bool = False,
        is_humor: bool = False,
        number_of_attemps: int = 9,
    ):
        # See if the result is available locally first
        grids = self._get_result_from_local_db(
            endpoint="get_logos_by_gameid",
            query=game_ids,
        )

        if grids is None:
            curr_attempt = 1
            successfully_processed = False
            while not successfully_processed and curr_attempt <= number_of_attemps:
                try:
                    grids = self.sgdb.get_logos_by_gameid(
                        game_ids=game_ids,
                        styles=styles,
                        mimes=mimes,
                        types=types,
                        is_nsfw=is_nsfw,
                        is_humor=is_humor,
                    )
                    curr_attempt += 1
                    successfully_processed = True
                    self._store_result_in_local_db(
                        endpoint="get_logos_by_gameid", query=game_ids, grids=grids
                    )
                except Exception:
                    print("\tAttempt failed, trying again")
                    time.sleep(5.0)
        elif grids == "None":
            grids = None
        return grids

    def _get_heroes_by_gameid(
        self,
        game_ids: List[int],
        styles: List[StyleType] = [],
        mimes: List[MimeType] = [],
        types: List[ImageType] = [],
        is_nsfw: bool = False,
        is_humor: bool = False,
        number_of_attemps: int = 9,
    ):
        # See if the result is available locally first
        grids = self._get_result_from_local_db(
            endpoint="get_heroes_by_gameid",
            query=game_ids,
        )

        if grids is None:
            curr_attempt = 1
            successfully_processed = False
            while not successfully_processed and curr_attempt <= number_of_attemps:
                try:
                    grids = self.sgdb.get_heroes_by_gameid(
                        game_ids=game_ids,
                        styles=styles,
                        mimes=mimes,
                        types=types,
                        is_nsfw=is_nsfw,
                        is_humor=is_humor,
                    )
                    curr_attempt += 1
                    successfully_processed = True
                    self._store_result_in_local_db(
                        endpoint="get_heroes_by_gameid", query=game_ids, grids=grids
                    )
                except Exception:
                    print("\tAttempt failed, trying again")
                    time.sleep(5.0)
        elif grids == "None":
            grids = None
        return grids

    def _download_image(self, grid, art_path, image_type, filename_links):
        image_url = grid.url
        extension = Path(image_url).suffix
        image_filename = str(grid.id) + extension

        image_path = os.path.join(art_path, image_type, image_filename)
        if not os.path.exists(os.path.dirname(image_path)):
            os.makedirs(os.path.dirname(image_path))

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
            filename_links[image_type].append(image_path)
        return

    def download_all_art(self, game_id: int, art_path_root: str):
        art_path = art_path_root + "steamgriddb/"
        if game_id is None:
            return {}

        grids = self._get_grids_by_gameid([game_id])

        # loop and download
        filename_links = {
            "poster": [],
            "poster_no_logo": [],
            "clearlogo": [],
            "fanart": [],
        }
        if grids is not None:
            for grid in grids:
                # Figure out the type of image we have
                if (
                    grid.height == 900
                    and grid.width == 600
                    and grid.style == "alternate"
                ):
                    image_type = "poster"
                elif (
                    grid.height == 900 and grid.width == 600 and grid.style == "no_logo"
                ):
                    image_type = "poster_no_logo"
                else:
                    continue

                # Download
                self._download_image(grid, art_path, image_type, filename_links)

        logos = self._get_logos_by_gameid([game_id])
        if logos is not None:
            for logo in logos:
                if logo.style == "official":
                    image_type = "clearlogo"
                else:
                    continue
                # Download
                self._download_image(logo, art_path, image_type, filename_links)

        heroes = self._get_heroes_by_gameid([game_id])
        if heroes is not None:
            for hero in heroes:
                # Download
                self._download_image(hero, art_path, "fanart", filename_links)

        return filename_links


def main():
    db = SteamGridDb(platform="xbox")
    game_id = db.get_game_id_by_name("Dark Angel")
    game_id


if __name__ == "__main__":
    main()
