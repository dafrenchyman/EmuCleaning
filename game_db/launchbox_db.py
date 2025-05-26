import os
import re
import sqlite3
import zipfile
from pathlib import Path
from typing import Any, Union

import numpy
import pandas
import requests
import xmltodict
from fuzzywuzzy import fuzz

"gamesdb.launchbox-app.com/games/dbid/<id-here>"

PLATFORM_LOOKUP = {
    "3do": "3DO Interactive Multiplayer",
    "amiga": "Commodore Amiga",
    "amigacd32": "Commodore Amiga CD32",
    "arcade": "Arcade",
    "atari2600": "Atari 2600",
    "atari5200": "Atari 5200",
    "atari7800": "Atari 7800",
    "atarijaguar": "Atari Jaguar",
    "atarijaguarcd": "Atari Jaguar CD",
    "atarilynx": "Atari Lynx",
    "atarist": "Atari ST",
    "colecovision": "ColecoVision",
    "dreamcast": "Sega Dreamcast",
    "gb": "Nintendo Game Boy",
    "gba": "Nintendo Game Boy Advance",
    "gbc": "Nintendo Game Boy Color",
    "gc": "Nintendo GameCube",
    "genesis": "Sega Genesis",
    "n64": "Nintendo 64",
    "megacd": "Sega CD",
    "model2": "Sega Model 2",
    "model3": "Sega Model 3",
    "naomi": "Sega Naomi",
    "neogeo": "SNK Neo Geo AES",
    "nes": "Nintendo Entertainment System",
    "ngp": "SNK Neo Geo Pocket",
    "ngpc": "SNK Neo Geo Pocket Color",
    "pcenginecd": "PC Engine SuperGrafx",
    "ps2": "Sony Playstation 2",
    "ps3": "Sony Playstation 3",
    "psp": "Sony PSP",
    "psx": "Sony Playstation",
    "saturn": "Sega Saturn",
    "sega32x": "Sega 32X",
    "segacd": "Sega CD",
    "scummvm": "Windows",
    "snes": "Super Nintendo Entertainment System",
    "snes_widescreen": "Super Nintendo Entertainment System",
    "switch": "Nintendo Switch",
    "tg-16": "NEC TurboGrafx-16",
    "tg-cd": "NEC TurboGrafx-CD",
    "virtualboy": "Nintendo Virtual Boy",
    "wii": "Nintendo Wii",
    "wiiu": "Nintendo Wii U",
    "wonderswan": "WonderSwan",
    "wonderswancolor": "WonderSwan Color",
    "xbox": "Microsoft Xbox",
}


class LaunchBoxDB:
    def __init__(self, platform: str):
        self.platform = platform

        # Download and process the launchbox DB zip file
        self.process_files = self._get_and_process_files()

        # Now check if we've created a SQLite database for it.
        self.engine = sqlite3.connect(self.local_db_file)
        self._cursor = self.engine.cursor()

        # Create local caching tables
        self._create_tables()
        self._populate_tables()

        # Get all the games for the current platform
        self.platform_id = self._get_platform_id(self.platform)
        self.all_platform_games = self._get_all_games_from_platform_id(self.platform_id)

        return

    def __del__(self) -> None:
        self.engine.commit()
        self._cursor.close()
        self.engine.close()
        return

    def _get_and_process_files(self):
        # For now, we are NOT going to process the files
        process_files = False

        # Get the current script's location
        current_dir = Path(__file__).parent

        # See if we've already downloaded the XML file
        http_metadata_file_zip = "http://gamesdb.launchbox-app.com/Metadata.zip"
        local_metadata_file_zip = current_dir / ".." / "database" / "Metadata.zip"
        self.local_metadata_folder = current_dir / ".." / "database" / "Metadata"
        self.local_db_file = current_dir / ".." / "database" / "launchbox.db"

        # If the file doesn't exist, download it
        if not local_metadata_file_zip.exists():
            # Make the HTTP request to download the file
            response = requests.get(http_metadata_file_zip)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Save the content to the file
                with open(local_metadata_file_zip, "wb") as file:
                    file.write(response.content)
            else:
                raise Exception("Failed to download Metadata.zip")

        # Check if the extraction folder exists, if not, create it
        if not self.local_metadata_folder.exists():
            self.local_metadata_folder.mkdir(parents=True)
            print(f"Created folder: {self.local_metadata_folder}")

            # Extract the ZIP file contents if the file exists
            if local_metadata_file_zip.exists():
                with zipfile.ZipFile(local_metadata_file_zip, "r") as zip_ref:
                    zip_ref.extractall(self.local_metadata_folder)
                print(f"Extracted contents to {self.local_metadata_folder}")

                # First time extracting everything - Process the files
                process_files = True
        return process_files

    def _process_string_for_insert(self, value, allow_null=True):
        value = None if value is None else value.replace("'", "''")
        if allow_null:
            value = f"'{value}'" if value is not None else "NULL"
        else:
            value = '""' if value is None else value
        return value

    def _process_string_bool_for_insert(self, value: Union[str, bool]) -> bool:
        result = False
        if value in [True, False]:
            result = value
        elif value is None:
            result = False
        elif value.upper().strip() == "TRUE":
            result = True
        return result

    def _process_platforms_file(self):
        # Read the platforms xml file
        platforms_file_path = self.local_metadata_folder / "Platforms.xml"

        # Open and read the XML file
        print("Loading Launchbox: Platforms.xml")
        with open(platforms_file_path, "r") as xml_file:
            platforms_xml_content = xml_file.read()

        # Convert the XML content to a dictionary
        platform_root = xmltodict.parse(platforms_xml_content).get("LaunchBox")
        platforms = platform_root.get("Platform")
        platforms_alternative = platform_root.get("PlatformAlternateName")

        # Populate the DB with the platform data
        self.platform_lookup = {}
        for idx, platform in enumerate(platforms):
            # Process the fields
            name = self._process_string_for_insert(platform.get("Name"))
            emulated = self._process_string_bool_for_insert(
                platform.get("Emulated", "FALSE")
            )
            release_date = self._process_string_for_insert(platform.get("ReleaseDate"))
            developer = self._process_string_for_insert(platform.get("Developer"))
            manufacturer = self._process_string_for_insert(platform.get("Manufacturer"))
            cpu = self._process_string_for_insert(platform.get("Cpu"))
            memory = self._process_string_for_insert(platform.get("Memory"))
            graphics = self._process_string_for_insert(platform.get("Graphics"))
            sound = self._process_string_for_insert(platform.get("Sound"))
            display = self._process_string_for_insert(platform.get("Display"))
            media = self._process_string_for_insert(platform.get("Media"))
            max_controllers = self._process_string_for_insert(
                platform.get("MaxControllers")
            )
            notes = self._process_string_for_insert(platform.get("Notes"))
            category = self._process_string_for_insert(platform.get("Category"))
            use_mame_files = self._process_string_bool_for_insert(
                platform.get("UseMameFiles", False)
            )

            # Create the lookup entry
            self.platform_lookup[name] = idx

            # Insert into the DB
            self._cursor.execute(
                f"""
                    INSERT OR REPLACE INTO platform (
                        platform_id,
                        name,
                        emulated,
                        release_data,
                        developer,
                        manufacturer,
                        cpu,
                        memory,
                        graphics,
                        sound,
                        display,
                        media,
                        max_controllers,
                        notes,
                        category,
                        use_mame_files
                    )
                    VALUES(
                        {idx},
                        {name},
                        {emulated},
                        {release_date},
                        {developer},
                        {manufacturer},
                        {cpu},
                        {memory},
                        {graphics},
                        {sound},
                        {display},
                        {media},
                        {max_controllers},
                        {notes},
                        {category},
                        {use_mame_files}
                    )
                """
            )
        self.engine.commit()

        # Platform alternative
        for idx, platform_alternative in enumerate(platforms_alternative):
            # Process the fields
            platform_name = self._process_string_for_insert(
                platform_alternative.get("Name")
            )
            platform_id = self.platform_lookup[platform_name]
            alternative_name = platform_alternative.get("Alternate")

            self._cursor.execute(
                f"""
                    INSERT OR REPLACE INTO platform_alternative (
                        platform_alternative_id,
                        platform_id,
                        name
                    )
                    VALUES(
                        {idx},
                        {platform_id},
                        '{alternative_name}'
                    )
                """
            )
        self.engine.commit()

    def _process_metadata_file(self):
        # Read the Metadata xml file
        metadata_file_path = self.local_metadata_folder / "Metadata.xml"

        # Open and read the XML file
        with open(metadata_file_path, "r") as xml_file:
            metadata_xml_content = xml_file.read()

        # Convert the XML content to a dictionary
        print("Loading Launchbox: Metadata.xml - Starting")
        metadata_root = xmltodict.parse(metadata_xml_content).get("LaunchBox")
        print("Loading Launchbox: Metadata.xml - Completed")
        games = metadata_root.get("Game")
        game_images = metadata_root.get("GameImage")

        # Games
        # Check if the length of the game table is the same as the length from metadata
        df = pandas.read_sql(
            "SELECT COUNT(*) AS cnt FROM game",
            self.engine,
        )
        game_len = int(df["cnt"][0])
        game_len = 0
        if game_len != len(games):
            for idx, game in enumerate(games):
                # Process the fields
                name = self._process_string_for_insert(game.get("Name"))
                release_year = game.get("ReleaseYear")
                release_year = "NULL" if release_year is None else int(release_year)
                overview = self._process_string_for_insert(game.get("Overview"))
                max_players = int(game.get("MaxPlayers", 1))
                release_type = self._process_string_for_insert(game.get("ReleaseType"))
                cooperative = self._process_string_bool_for_insert(
                    game.get("Cooperative", False)
                )
                video_url = self._process_string_for_insert(game.get("VideoURL"))
                game_id = game.get("DatabaseID")
                community_rating = float(game.get("CommunityRating", 0.0))
                platform = self._process_string_for_insert(game.get("Platform"))
                platform_id = self.platform_lookup[platform]
                esrb = self._process_string_for_insert(game.get("ESRB"))
                community_rating_count = int(game.get("CommunityRatingCount", 0))
                genres = self._process_string_for_insert(game.get("Genres"))
                developer = self._process_string_for_insert(game.get("Developer"))
                publisher = self._process_string_for_insert(game.get("Publisher"))

                self._cursor.execute(
                    f"""
                        INSERT OR REPLACE INTO game (
                            game_id,
                            name,
                            release_year,
                            overview,
                            max_players,
                            release_type,
                            cooperative,
                            video_url,
                            community_rating ,
                            platform_id,
                            esrb,
                            community_rating_count,
                            genres,
                            developer,
                            publisher
                        )
                        VALUES(
                            {game_id},
                            {name},
                            {release_year},
                            {overview},
                            {max_players},
                            {release_type},
                            {cooperative},
                            {video_url},
                            {community_rating},
                            {platform_id},
                            {esrb},
                            {community_rating_count},
                            {genres},
                            {developer},
                            {publisher}
                        )
                    """
                )

                # commit every so many records
                if idx % 10_000 == 0:
                    self.engine.commit()
            self.engine.commit()

        # Game Images
        # Check if the length of the game table is the same as the length from metadata
        df = pandas.read_sql(
            "SELECT COUNT(*) AS cnt FROM game_image",
            self.engine,
        )
        game_image_len = int(df["cnt"][0])
        game_image_len = 0
        if len(game_images) != game_image_len:
            for idx, game_image in enumerate(game_images):
                game_id = game_image.get("DatabaseID")
                file_name = self._process_string_for_insert(game_image.get("FileName"))
                image_type = self._process_string_for_insert(game_image.get("Type"))
                region = self._process_string_for_insert(game_image.get("Region"))
                crc32 = self._process_string_for_insert(game_image.get("CRC32"))

                self._cursor.execute(
                    f"""
                        INSERT OR REPLACE INTO game_image (
                            game_id,
                            type,
                            region,
                            file_name,
                            crc32
                        )
                        VALUES(
                            {game_id},
                            {image_type},
                            {region},
                            {file_name},
                            {crc32}
                        )
                    """
                )
                # commit every so many records
                if idx % 10_000 == 0:
                    self.engine.commit()
            self.engine.commit()

        return

    def _process_mame_file(self):
        # Read the Metadata xml file
        mame_file_path = self.local_metadata_folder / "Mame.xml"

        # Open and read the XML file
        with open(mame_file_path, "r") as xml_file:
            mame_xml_content = xml_file.read()

        # Convert the XML content to a dictionary
        print("Loading Launchbox: Mame.xml - Starting")
        mame_root = xmltodict.parse(mame_xml_content).get("LaunchBox")
        print("Loading Launchbox: Mame.xml - Completed")
        mame_files = mame_root.get("MameFile")

        # Games
        # Check if the length of the game table is the same as the length from metadata
        df = pandas.read_sql(
            "SELECT COUNT(*) AS cnt FROM mame_file",
            self.engine,
        )
        mame_file_len = int(df["cnt"][0])
        mame_file_len = 0
        if mame_file_len != len(mame_files):
            for mame_id, mame in enumerate(mame_files):
                # Process the fields
                file_name = self._process_string_for_insert(mame.get("FileName"))
                name = self._process_string_for_insert(mame.get("Name"))
                status = self._process_string_for_insert(mame.get("Status"))
                developer = self._process_string_for_insert(mame.get("Developer"))
                publisher = self._process_string_for_insert(mame.get("Publisher"))
                year = mame.get("Year")
                try:
                    year = "NULL" if year is None else int(year)
                except:  # noqa: E722
                    year = "NULL"
                is_mechanical = self._process_string_bool_for_insert(
                    mame.get("IsMechanical", False)
                )
                is_bootleg = self._process_string_bool_for_insert(
                    mame.get("IsBootleg", False)
                )
                is_prototype = self._process_string_bool_for_insert(
                    mame.get("IsPrototype", False)
                )
                is_hack = self._process_string_bool_for_insert(
                    mame.get("IsHack", False)
                )
                is_mature = self._process_string_bool_for_insert(
                    mame.get("IsMature", False)
                )
                is_quiz = self._process_string_bool_for_insert(
                    mame.get("IsQuiz", False)
                )
                is_fruit = self._process_string_bool_for_insert(
                    mame.get("IsFruit", False)
                )
                is_casino = self._process_string_bool_for_insert(
                    mame.get("IsCasino", False)
                )
                is_rhythm = self._process_string_bool_for_insert(
                    mame.get("IsRhythm", False)
                )
                is_table_top = self._process_string_bool_for_insert(
                    mame.get("IsTableTop", False)
                )
                is_play_choice = self._process_string_bool_for_insert(
                    mame.get("IsPlayChoice", False)
                )
                is_mahjong = self._process_string_bool_for_insert(
                    mame.get("IsMahjong", False)
                )
                is_non_arcade = self._process_string_bool_for_insert(
                    mame.get("IsNonArcade", False)
                )
                genre = self._process_string_for_insert(mame.get("Genre"))
                play_mode = self._process_string_for_insert(mame.get("PlayMode"))
                play_mode = "NULL" if play_mode == "'???'" else play_mode
                language = self._process_string_for_insert(mame.get("Language"))
                source = self._process_string_for_insert(mame.get("Source"))

                self._cursor.execute(
                    f"""
                        INSERT OR REPLACE INTO mame_file (
                            mame_id,
                            filename,
                            name,
                            status,
                            developer,
                            publisher,
                            year,
                            is_mechanical,
                            is_bootleg,
                            is_prototype,
                            is_hack,
                            is_mature,
                            is_quiz,
                            is_fruit,
                            is_casino,
                            is_rhythm,
                            is_table_top,
                            is_play_choice,
                            is_mahjong,
                            is_non_arcade,
                            genre,
                            play_mode,
                            language,
                            source
                        )
                        VALUES(
                            {mame_id},
                            {file_name},
                            {name},
                            {status},
                            {developer},
                            {publisher},
                            {year},
                            {is_mechanical},
                            {is_bootleg},
                            {is_prototype},
                            {is_hack},
                            {is_mature},
                            {is_quiz},
                            {is_fruit},
                            {is_casino},
                            {is_rhythm},
                            {is_table_top},
                            {is_play_choice},
                            {is_mahjong},
                            {is_non_arcade},
                            {genre},
                            {play_mode},
                            {language},
                            {source}
                        )
                    """
                )

                # commit every so many records
                if mame_id % 10_000 == 0:
                    self.engine.commit()
            self.engine.commit()
        return

    def _populate_tables(self):
        if True:
            return

        self._process_platforms_file()
        self._process_metadata_file()
        self._process_mame_file()

        return

    def _create_tables(self):
        # platform
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS platform (
                platform_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                emulated BOOLEAN NOT NULL,
                release_data TIMESTAMP NULL,
                developer TEXT NULL,
                manufacturer TEXT NULL,
                cpu TEXT NULL,
                memory TEXT NULL,
                graphics TEXT NULL,
                sound TEXT NULL,
                display TEXT NULL,
                media TEXT NULL,
                max_controllers TEXT NULL,
                notes TEXT NULL,
                category TEXT NULL,
                use_mame_files BOOLEAN DEFAULT False
            )
            """
        )
        self._cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS platform_name_uidx ON
                platform (name)
            """
        )

        # platform_alternative
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_alternative (
                platform_alternative_id INTEGER PRIMARY KEY,
                platform_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL
            )
            """
        )
        self._cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS platform_alternative_name_uidx ON
                platform_alternative (name)
            """
        )

        # game
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game (
                game_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                release_year INT NULL,
                overview TEXT NULL,
                max_players INT DEFAULT 1,
                release_type TEXT NULL,
                cooperative BOOLEAN DEFAULT False,
                video_url TEXT NULL,
                community_rating FLOAT NULL,
                platform_id INT NOT NULL,
                esrb TEXT NULL,
                community_rating_count INT DEFAULT 0,
                genres TEXT NULL,
                developer TEXT NULL,
                publisher TEXT NULL
            )
            """
        )
        self._cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS game_name_idx ON
                game (name)
            """
        )
        self._cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS game_platform_idx ON
                game (platform_id)
            """
        )

        # game_alternative
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_alternative (
                game_alternative_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                game_id INT NOT NULL,
                name TEXT NOT NULL
            )
            """
        )
        self._cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS game_alternative_game_id_idx ON
                game_alternative (game_id)
            """
        )

        # game_image
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_image (
                game_image_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                game_id INT NOT NULL,
                type TEXT NOT NULL,
                region TEXT NULL,
                file_name TEXT NOT NULL,
                crc32 TEXT NULL
            )
            """
        )
        self._cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS game_image_game_id_dx ON
                game_image (game_id)
            """
        )
        self._cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS game_image_file_name_dx ON
                game_image (file_name)
            """
        )

        # mame_file
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mame_file (
                mame_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filename TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NULL,
                developer TEXT NULL,
                publisher TEXT NULL,
                year INT NULL,
                is_mechanical BOOLEAN DEFAULT FALSE,
                is_bootleg BOOLEAN DEFAULT FALSE,
                is_prototype BOOLEAN DEFAULT FALSE,
                is_hack BOOLEAN DEFAULT FALSE,
                is_mature BOOLEAN DEFAULT FALSE,
                is_quiz BOOLEAN DEFAULT FALSE,
                is_fruit BOOLEAN DEFAULT FALSE,
                is_casino BOOLEAN DEFAULT FALSE,
                is_rhythm BOOLEAN DEFAULT FALSE,
                is_table_top BOOLEAN DEFAULT FALSE,
                is_play_choice BOOLEAN DEFAULT FALSE,
                is_mahjong BOOLEAN DEFAULT FALSE,
                is_non_arcade BOOLEAN DEFAULT FALSE,
                genre TEXT NULL,
                play_mode TEXT NULL,
                language TEXT NULL,
                source TEXT NULL
            )
            """
        )
        self._cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS mame_filename_uidx ON
                mame_file (filename)
            """
        )
        self._cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS mame_name_uidx ON
                mame_file (name)
            """
        )

        # Commit all the table generation
        self.engine.commit()
        return

    def _get_platform_id(self, platform: str):
        platform_lookup = PLATFORM_LOOKUP[platform]
        df = pandas.read_sql(
            f"""
                SELECT * FROM platform
                WHERE UPPER(name) = UPPER('{platform_lookup}')""",
            self.engine,
        )
        return df["platform_id"][0]

    def _get_all_games_from_platform_id(self, platform_id):
        df = pandas.read_sql(
            f"""
                SELECT * FROM game
                WHERE platform_id = {platform_id}""",
            self.engine,
        )
        all_games = {}
        for idx, row in df.iterrows():
            values = row.to_dict()
            if numpy.isnan(values["release_year"]):
                values["release_year"] = None
            name = values["name"]
            all_games[name] = values
        return all_games

    def get_game_by_name(self, game_name: str):
        game_name = game_name.strip()
        best_fuzz_score = 0
        best_match = None

        for db_game_name in self.all_platform_games.keys():
            fuzz_score = fuzz.ratio(game_name, db_game_name)
            if fuzz_score > 80 and fuzz_score > best_fuzz_score:
                best_fuzz_score = fuzz_score
                best_match = self.all_platform_games[db_game_name]
            if best_fuzz_score == 100:
                break
        return best_match

    def _find_artwork(
        self,
        artworks: list[dict[str, Any]],
        artwork_type: str,
        order_of_regions: list[str],
    ):
        # Find relevant artwork
        found_artworks = []
        for region in order_of_regions:
            criteria = {"region": region, "type": artwork_type}
            found_artworks += list(
                filter(
                    lambda d: all(
                        d.get(k).upper() == v.upper() for k, v in criteria.items()
                    ),
                    artworks,
                )
            )
            if len(found_artworks) > 0:
                break
        return found_artworks

    def get_artwork_from_game(self, game: dict[str, Any], filename: str):
        df = pandas.read_sql(
            f"SELECT * FROM game_image WHERE game_id = {game['game_id']}", self.engine
        )
        df["index"] = df["game_image_id"]
        artworks = df.set_index("index").T.to_dict("dict")
        artworks = list(artworks.values())

        # Some artwork doesn't have a region setup. Set it to "None"
        for artwork in artworks:
            if artwork["region"] is None:
                artwork["region"] = "None"

        # Get the order of precedence for artwork
        # We try to have the countries alphabetically, but since there's a pattern of (Korea, USA)
        # I'd rather want the USA images
        if re.search(r"\(.*USA.*\)", filename.upper()):
            order_of_regions = [
                "USA",
                "NORTH AMERICA",
                "WORLD",
                "EUROPE",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*AUSTRALIA.*\)", filename.upper()):
            order_of_regions = [
                "AUSTRALIA",
                "OCEANIA" "WORLD",
                "ASIA",
                "EUROPE",
                "NORTH AMERICA",
                "USA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*BRAZIL.*\)", filename.upper()):
            order_of_regions = [
                "BRAZIL",
                "WORLD",
                "EUROPE",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*CANADA.*\)", filename.upper()):
            order_of_regions = [
                "CANADA",
                "NORTH AMERICA",
                "WORLD",
                "EUROPE",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*FRANCE.*\)", filename.upper()):
            order_of_regions = [
                "FRANCE",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*GERMANY.*\)", filename.upper()):
            order_of_regions = [
                "GERMANY",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*GREECE.*\)", filename.upper()):
            order_of_regions = [
                "GREECE",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*ITALY.*\)", filename.upper()):
            order_of_regions = [
                "ITALY",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*INDIA.*\)", filename.upper()):
            order_of_regions = [
                "INDIA",
                "ASIA",
                "WORLD",
                "NORTH AMERICA",
                "EUROPE",
                "NONE",
            ]
        elif re.search(r"\(.*JAPAN.*\)", filename.upper()):
            order_of_regions = [
                "JAPAN",
                "ASIA",
                "KOREA",
                "WORLD",
                "NORTH AMERICA",
                "EUROPE",
                "NONE",
            ]
        elif re.search(r"\(.*KOREA.*\)", filename.upper()):
            order_of_regions = [
                "KOREA",
                "ASIA",
                "WORLD",
                "JAPAN",
                "NORTH AMERICA",
                "EUROPE",
                "NONE",
            ]
        elif re.search(r"\(.*NETHERLANDS.*\)", filename.upper()):
            order_of_regions = [
                "NETHERLANDS",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*POLAND.*\)", filename.upper()):
            order_of_regions = [
                "POLAND",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*PORTUGAL.*\)", filename.upper()):
            order_of_regions = [
                "PORTUGAL",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*RUSSIA.*\)", filename.upper()):
            order_of_regions = [
                "RUSSIA",
                "EUROPE",
                "WORLD",
                "USA",
                "NORTH AMERICA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*SPAIN.*\)", filename.upper()):
            order_of_regions = [
                "SPAIN",
                "EUROPE",
                "WORLD",
                "USA",
                "NORTH AMERICA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*UK.*\)", filename.upper()):
            order_of_regions = [
                "UNITED KINGDOM",
                "UK",
                "EUROPE",
                "WORLD",
                "USA",
                "NORTH AMERICA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*UNITED ARAB EMIRATES.*\)", filename.upper()):
            order_of_regions = [
                "UNITED ARAB EMIRATES",
                "EUROPE",
                "WORLD",
                "USA",
                "NORTH AMERICA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*ASIA.*\)", filename.upper()):
            order_of_regions = [
                "ASIA",
                "WORLD",
                "EUROPE",
                "NORTH AMERICA",
                "USA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*EUROPE.*\)", filename.upper()):
            order_of_regions = [
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*NORTH AMERICA.*\)", filename.upper()):
            order_of_regions = [
                "NORTH AMERICA",
                "USA",
                "WORLD",
                "EUROPE",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*SCANDINAVIA.*\)", filename.upper()):
            order_of_regions = [
                "SCANDINAVIA",
                "EUROPE",
                "WORLD",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        elif re.search(r"\(.*WORLD.*\)", filename.upper()):
            order_of_regions = [
                "WORLD",
                "EUROPE",
                "NORTH AMERICA",
                "USA",
                "ASIA",
                "JAPAN",
                "NONE",
            ]
        else:
            raise Exception("no region found")

        # banner
        banners = self._find_artwork(
            artworks=artworks,
            artwork_type="Banner",
            order_of_regions=order_of_regions,
        )
        boxart_back = self._find_artwork(
            artworks=artworks,
            artwork_type="Box - Back",
            order_of_regions=order_of_regions,
        )
        boxart_front = self._find_artwork(
            artworks=artworks,
            artwork_type="Box - Front",
            order_of_regions=order_of_regions,
        )
        clearlogo = self._find_artwork(
            artworks=artworks,
            artwork_type="Clear Logo",
            order_of_regions=order_of_regions,
        )
        fanart = self._find_artwork(
            artworks=artworks,
            artwork_type="Fanart - Background",
            order_of_regions=order_of_regions,
        )
        screenshot = self._find_artwork(
            artworks=artworks,
            artwork_type="Screenshot - Gameplay",
            order_of_regions=order_of_regions,
        )
        titlescreen = self._find_artwork(
            artworks=artworks,
            artwork_type="Screenshot - Game Title",
            order_of_regions=order_of_regions,
        )

        final_artwork = {
            "banner": banners,
            "boxart_back": boxart_back,
            "boxart_front": boxart_front,
            "clearlogo": clearlogo,
            "fanart": fanart,
            "screenshot": screenshot,
            "titlescreen": titlescreen,
        }

        return final_artwork

    def download_all_art(self, launchbox_game: Any, filename: str, art_path_root: str):
        if launchbox_game is None:
            return {}
        art_path = art_path_root + "launchbox/"

        # Get Image data from database
        game_images = self.get_artwork_from_game(launchbox_game, filename)
        base_url = "https://images.launchbox-app.com//"

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
        for image_type, launchbox_images in game_images.items():
            for image in launchbox_images:
                image_filename: str = image["file_name"]
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
                    filename_links[image_type].append(image_path)

        return filename_links
