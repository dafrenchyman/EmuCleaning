import hashlib
import os
import sys
import tempfile
import zipfile
from pathlib import Path

from game_db.arcade_db import ArcadeDb
from game_db.internet_game_db import InternetGameDb
from game_db.launchbox_db import LaunchBoxDB
from game_db.no_intro_db import NoIntroDb
from game_db.scummvm_db import ScummVmDB
from game_db.steam_grid_db import SteamGridDb
from game_db.the_games_db_sqlite import TheGamesDbSqlite
from pegasus.local_files import LocalFiles
from pegasus.pegasus_text_builder import PegasusTextBuilder

# Using the same system names found here:
#   https://gitlab.com/es-de/emulationstation-de/-/blob/master/USERGUIDE.md#game-system-customizations
ROM_FOLDER_PATHS = {
    # "3do": "/ROMs/3do/",
    # "amiga": "/ROMs/amiga/",
    # "amigacd32": "/ROMs/amigacd32/",
    # "arcade": "/ROMs/arcade/",
    # "atari2600": "/ROMs/atari2600/",
    # "atari5200": "/ROMs/atari5200/",
    # "atari7800": "/ROMs/atari7800/",
    # "atarijaguar": "/ROMs/atarijaguar/",
    # "atarijaguarcd": "/ROMs/atarijaguarcd/",
    # "atarilynx": "/ROMs/atarilynx/",
    # "atarist": "/ROMs/atarist/",
    # "colecovision": "/ROMs/colecovision/",
    # "dreamcast": "/ROMs/dreamcast/",
    # "gb": "/ROMs/gb/",
    # "gba": "/ROMs/gba/",
    # "gbc": "/ROMs/gbc/",
    # "gc": "/ROMs/gc/",
    # "genesis": "/ROMs/genesis/",
    # "n64": "/ROMs/n64/",
    # "megacd": "/ROMs/megacd/",
    # "model2": "/ROMs/model2/",
    # "model3": "/ROMs/model3/",
    # "naomi": "/ROMs/naomi/",
    # "neogeo": "/ROMs/neogeo/",
    # "nes": "/ROMs/nes/",
    # "ngp": "/ROMs/ngp/",
    # "ngpc": "/ROMs/ngpc/",
    # "pcenginecd": "/ROMs/pcenginecd/",
    # "ps2": "/ROMs/ps2/",
    # "psp": "/ROMs/psp/",
    "ps3": "/ROMs/ps3/",
    # "psx": "/ROMs/psx/",
    # "saturn": "/ROMs/saturn/",
    # "sega32x": "/ROMs/sega32x/",
    # "segacd": "/ROMs/segacd/",
    # "scummvm": "/ROMs/scummvm/",
    # "snes": "/ROMs/snes/",
    # "snes_widescreen": "/ROMs/snes_widescreen/",
    # "switch": "/ROMs/switch/",
    # "tg-16": "/ROMs/tg-16/",
    # "tg-cd": "/ROMs/tg-cd/",
    # "virtualboy": "/ROMs/virtualboy/",
    # "wii": "/ROMs/wii/",
    # "wiiu": "/ROMs/wiiu/",
    # "wonderswan": "/ROMs/wonderswan/",
    # "wonderswancolor": "/ROMs/wonderswancolor/",
    # "xbox": "/ROMs/xbox/",
}

USES_ARCADE_DB = ["arcade", "model2", "model3", "naomi", "neogeo"]
USES_SCHUMMVM = ["scummvm"]
# USES_FOLDERS = ["ps3", "wiiu"]
USES_FOLDERS = ["wiiu"]

# Where to put the steamgriddb & thegamesdb images
ARTWORK_FOLDER_PATH = "/ROMs/.assets/"
VALID_EXTENSIONS = [
    "32x",  # Sega - 32X
    "a26",  # Atari - 2600
    "a52",  # Atari - 5200
    "a78",  # Atari - 7800
    "bin",  #
    "chd",  # Compressed Hard Disk
    "cl",  # Coleco - ColecoVision
    "cso",  # Compressed ISO
    "cue",  # bin/cue CD image
    "gb",  # Nintendo - Game Boy
    "gba",  # Nintendo - Game Boy Advanced
    "gbc",  # Nintendo - Game Boy Color
    "ipf",  # Atari - ST / Commodare - Amigi
    "iso",  # iso CD image
    "j64",  # Atari - Jaguar
    "lnx",  # Atari - Lynx
    "m3u",
    "md",  # Sega - Genesis
    "nes",  # Nintendo - Nintendo Entertainment System
    "ngp",  # Neo Geo Pocket / Neo Geo Pocket Color
    "nsp",  # Nintendo - Switch
    "nsz",  # Nintendo - Switch
    "rvz",  # Nintendo - Wii
    "smc",  # Nintendo - Super Nintendo
    "sfc",  # Nintendo - Super Nintendo
    "vb",  # Nintendo - Virtual Boy
    "ws",  # Bandai - WonderSwan
    "wsc",  # Bandai - WonderSwan Color
    "xci",  # Nintendo - Switch
    "z64",
    "zip",
]


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

        # Setup SCUMM VM
        if platform == "scummvm":
            self.scumm_vm = ScummVmDB()

        # Setup the NoIntroDB
        if NoIntroDb.platform_available(self.platform):
            self.no_intro_db = NoIntroDb(platform=platform)

        # Setup the ArcadeDB
        if platform in (USES_ARCADE_DB):
            self.arcade_db = ArcadeDb()

        # Setup LaunchBoxDB
        self.launch_box_db = LaunchBoxDB(platform)

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

            # Don't look at folders and unless it's for an emulator
            # that looks at an extracted game (ie: PS3)
            if os.path.isdir(full_filename_path) and self.platform not in USES_FOLDERS:
                continue

            # If it's for an emulator that requires a folder structure
            # and it's a file, skip it
            if not os.path.isdir(full_filename_path) and self.platform in USES_FOLDERS:
                continue

            # Ignore the ".assets" folder, as that just contains images
            if os.path.isdir(full_filename_path) and filename == ".assets":
                continue

            # Ignore the pegasus metadata file
            if filename == "metadata.pegasus.txt":
                continue

            self.process_rom(full_filename_path, filename)

        return

    def process_rom(self, full_filename_path: str, filename: str) -> None:
        game_name_clean = None
        game_title = None

        # Some game emulators use folders instead of files
        if self.platform not in USES_FOLDERS:
            # If the file doesn't have a valid extension skip it
            if Path(filename).suffix.replace(".", "") not in VALID_EXTENSIONS:
                return

        if NoIntroDb.platform_available(self.platform):
            rom_file_name = full_filename_path
            # Check if it's a zip file
            if zipfile.is_zipfile(full_filename_path):
                temp_rom_file = tempfile.mktemp()
                with zipfile.ZipFile(full_filename_path, "r") as zip_ref:
                    # Can only process if it's one ROM per file
                    if len(zip_ref.filelist) == 1:
                        rom_file_name = zip_ref.extract(
                            member=zip_ref.filelist[0], path=temp_rom_file
                        )
                    else:
                        return

            game_no_intro = self.no_intro_db.get_game_info_from_filename(rom_file_name)
            game_name_clean = NoIntroDb.get_regular_name_from_no_intro(game_no_intro)

        elif self.platform in USES_SCHUMMVM:
            game_no_intro = {}
            filename_no_ext = Path(filename).stem
            scumm_vm_info = self.scumm_vm.get_scummvm_from_game_name(filename_no_ext)
            if scumm_vm_info is not None:
                game_name_clean = scumm_vm_info.get("name")
                game_title = filename_no_ext

                self.scumm_vm.create_lookup_file(full_filename_path, scumm_vm_info)

        elif self.platform in USES_ARCADE_DB:
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

        # Get launch box DB game_id
        launch_box_game = self.launch_box_db.get_game_by_name(game_name_clean)

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

            # launchbox
            launchbox_assets = self.launch_box_db.download_all_art(
                launchbox_game=launch_box_game,
                filename=filename,
                art_path_root=ARTWORK_FOLDER_PATH,
            )

            all_assets = dict_merge(
                assets,
                local_assets,
                game_db_assets,
                steam_grid_assets,
                launchbox_assets,
            )

            # create xml string from game_db
            self.pegasus_text_builder.add_entry(
                filename=filename,
                game_db=game_db,
                internet_game_db=internet_game_db,
                no_intro=game_no_intro,
                images=all_assets,
                game_title=game_title,
                full_filename_path=full_filename_path,
            )
        else:
            print("\tUnable to find game ")

    def write_pegasus_file(self):
        with open(f"{self.rom_folder_path}metadata.pegasus.txt", "w") as output:
            output.write(self.pegasus_text_builder.text)
        return


def main():
    for platform in ROM_FOLDER_PATHS.keys():
        print(80 * "-")
        print(f"Processing: {platform}")
        print(80 * "-")
        rom_folder = ROM_FOLDER_PATHS[platform]

        if os.path.exists(rom_folder):
            rom_processor = RomProcessor(
                platform=platform,
                rom_folder=rom_folder,
            )
            rom_processor.process_roms()
            rom_processor.write_pegasus_file()

    return


if __name__ == "__main__":
    sys.exit(main())
