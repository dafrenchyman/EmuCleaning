import hashlib
import os
import sys
from pathlib import Path

from game_db.internet_game_db import InternetGameDb
from game_db.no_intro_db import NoIntroDb
from game_db.steam_grid_db import SteamGridDb
from game_db.the_games_db_sqlite import TheGamesDbSqlite
from pegasus.local_files import LocalFiles
from pegasus.pegasus_text_builder import PegasusTextBuilder

# Using the same system names found here:
#   https://gitlab.com/es-de/emulationstation-de/-/blob/master/USERGUIDE.md#game-system-customizations
ROM_FOLDER_PATHS = {
    "gc": "/ROMs/gc/",
    # "nes": "/ROMs/nes/",
    # "snes": "/ROMs/snes/",
    # "sega32x": "/ROMs/sega32x/",
    # "psx": "/ROMs/psx/",
    # "gb": "/ROMs/gb/",
    # "gba": "/ROMs/gba/",
    # "gbc": "/ROMs/gbc/",
    # "genesis": "/ROMs/genesis/",
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
        if self.platform not in ("psx", "gc"):
            self.no_intro_db = NoIntroDb(platform=platform)

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
        for filename in all_files:
            full_filename_path = os.path.join(self.rom_folder_path, filename)

            if os.path.isdir(full_filename_path):
                continue

            if self.platform not in ("psx", "gc"):
                game_no_intro = self.no_intro_db.get_game_info_from_filename(
                    full_filename_path
                )

                game_name_clean = NoIntroDb.get_regular_name_from_no_intro(
                    game_no_intro
                )

                if game_name_clean is None:
                    continue
            else:
                game_no_intro = {}
                game_name_clean = NoIntroDb.get_regular_name_from_no_intro(
                    {"@name": Path(filename).stem}
                )
            print(game_name_clean)

            # Get Games DB entry
            game_db = self.the_game_db.get_games_db_from_game_name(game_name_clean)

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
                )
        return

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

    print("test")

    return


if __name__ == "__main__":
    sys.exit(main())
