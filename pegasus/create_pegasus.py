import hashlib
import os
import sys
import tempfile
import zipfile
from pathlib import Path

from game_db.arcade_db import ArcadeDb
from game_db.internet_game_db import InternetGameDb
from game_db.no_intro_db import NoIntroDb
from game_db.steam_grid_db import SteamGridDb
from game_db.the_games_db_sqlite import TheGamesDbSqlite
from pegasus.local_files import LocalFiles
from pegasus.pegasus_text_builder import PegasusTextBuilder

# Using the same system names found here:
#   https://gitlab.com/es-de/emulationstation-de/-/blob/master/USERGUIDE.md#game-system-customizations
ROM_FOLDER_PATHS = {
    "arcade": "/ROMs/arcade/",
    "atari2600": "/ROMs/atari2600/",
    "gb": "/ROMs/gb/",
    "gba": "/ROMs/gba/",
    "gbc": "/ROMs/gbc/",
    "gc": "/ROMs/gc/",
    "genesis": "/ROMs/genesis/",
    "nes": "/ROMs/nes/",
    "ngp": "/ROMs/ngp/",
    "ngpc": "/ROMs/ngpc/",
    "ps2": "/ROMs/ps2/",
    "psx": "/ROMs/psx/",
    "snes": "/ROMs/snes/",
    "sega32x": "/ROMs/sega32x/",
    "wii": "/ROMs/wii/",
    "xbox": "/ROMs/xbox/",
}

# Where to put the steamgriddb & thegamesdb images
ARTWORK_FOLDER_PATH = "/ROMs/.assets/"


def md5sum(filename, offset):
    h = hashlib.md5()
    with open(filename, "rb") as file:
        if offset > 0:
            file.read(offset)  # read files with an offset, for iNES roms etc
        chunk = 0
        while chunk != b"":
            chunk = file.read(1024)
            h.update(chunk)
    return h.hexdigest()


def dict_merge(*dicts_list):
    result = {}
    for d in dicts_list:
        for k, v in d.items():
            result.setdefault(k, [])
            for i in v:
                result[k].append(i)
    return result


class RomProcessor:
    def __init__(self, platform: str, rom_folder: str) -> None:
        self.platform = platform
        self.rom_folder_path = rom_folder

        # Setup the NoIntroDB
        if NoIntroDb.platform_available(self.platform):
            self.no_intro_db = NoIntroDb(platform=platform)

        # Setup the ArcadeDD
        if platform == "arcade":
            self.arcade_db = ArcadeDb()

        self.internet_game_db = InternetGameDb(platform)
        self.the_game_db = TheGamesDbSqlite(platform)
        self.steam_grid_db = SteamGridDb(platform)
        self.local_files = LocalFiles(rom_folder)
        self.pegasus_text_builder = PegasusTextBuilder(
            the_games_db=self.the_game_db,
            platform=platform,
        )
        return

    def process_roms(self):
        all_files = sorted(os.listdir(self.rom_folder_path), reverse=False)

        # Loop on files in folder
        for _, filename in enumerate(all_files):
            full_filename_path = os.path.join(self.rom_folder_path, filename)

            if os.path.isdir(full_filename_path):
                continue

            self.process_rom(full_filename_path, filename)

        return

    def process_rom(self, full_filename_path, filename):
        game_name_clean = None
        game_title = None
        if NoIntroDb.platform_available(self.platform):
            rom_file_name = full_filename_path
            # Check if it's a zip file
            if zipfile.is_zipfile(full_filename_path):
                temp_rom_file = tempfile.mktemp()
                with zipfile.ZipFile(full_filename_path, "r") as zip_ref:
                    # Can only process if it's one ROM per file
                    if len(zip_ref.filelist):
                        rom_file_name = zip_ref.extract(
                            member=zip_ref.filelist[0], path=temp_rom_file
                        )
                    else:
                        return

            game_no_intro = self.no_intro_db.get_game_info_from_filename(rom_file_name)
            game_name_clean = NoIntroDb.get_regular_name_from_no_intro(game_no_intro)

        elif self.platform == "arcade":
            game_no_intro = {}
            filename_no_ext = Path(filename).stem
            game_name_clean, game_title = self.arcade_db.convert_filename_to_game_name(
                filename_no_ext
            )
            # If we don't have a clean name for it, skip the game
            if game_name_clean is None:
                return

        if game_name_clean is None:
            game_no_intro = {}
            game_name_clean = NoIntroDb.get_regular_name_from_no_intro(
                {"@name": Path(filename).stem}
            )
        print(f"{game_name_clean}\t|\t{game_title}")

        # Get Games DB entry
        game_db = self.the_game_db.get_games_db_from_game_name(game_name_clean)
        if game_db is not None:
            print(f'\tBest Match: {game_db["game_title"]}')

        # Get Internet Game Database ID
        internet_game_db = self.internet_game_db.get_game_from_game_name(
            game_name=game_name_clean,
        )

        # Get Steam Grid DB ID
        steam_grid_id = self.steam_grid_db.get_game_id_by_name(game_name_clean)

        assets = {
            "banner": [],
            "boxart_back": [],
            "boxart_front": [],
            "boxart_full": [],
            "boxart_spine": [],
            "cart": [],
            "cart_label": [],
            "clearlogo": [],
            "fanart": [],
            "poster": [],
            "poster_no_logo": [],
            "screenshot": [],
            "titlescreen": [],
            "graphical": [],
            "music": [],
            "video": [],
        }

        # Get locals assets
        filename_no_ext = Path(filename).stem
        local_assets = self.local_files.get_assets_from_game_name(filename_no_ext)

        # Download images
        if game_db is not None:
            game_db_assets = self.the_game_db.download_all_art(
                game_db=game_db, art_path_root=ARTWORK_FOLDER_PATH
            )

            steam_grid_assets = self.steam_grid_db.download_all_art(
                game_id=steam_grid_id,
                art_path_root=ARTWORK_FOLDER_PATH,
            )

            all_assets = dict_merge(
                assets, local_assets, game_db_assets, steam_grid_assets
            )

            # create xml string from game_db
            self.pegasus_text_builder.add_entry(
                filename=filename,
                game_db=game_db,
                internet_game_db=internet_game_db,
                no_intro=game_no_intro,
                images=all_assets,
                game_title=game_title,
            )
        else:
            print("\tUnable to find game ")

    def write_pegasus_file(self):
        with open(f"{self.rom_folder_path}metadata.pegasus.txt", "w") as output:
            output.write(self.pegasus_text_builder.text)
        return


def main():
    for platform in ROM_FOLDER_PATHS.keys():
        rom_processor = RomProcessor(
            platform=platform, rom_folder=ROM_FOLDER_PATHS[platform]
        )
        rom_processor.process_roms()
        rom_processor.write_pegasus_file()

    return


if __name__ == "__main__":
    sys.exit(main())
