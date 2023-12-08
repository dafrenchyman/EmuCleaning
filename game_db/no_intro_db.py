import hashlib
import re

import xmltodict as xmltodict

NO_INTRO_ROOT = "/mnt/SnapSsdArray_01/SnapDisk_4TB_27/Consoles/DatFiles/No-Intro Love Pack (Standard) (2023-04-13)"
PLATFORM_LOOKUP = {
    "amiga": f"{NO_INTRO_ROOT}/No-Intro/Commodore - Amiga (20220712-143036).dat",
    "atari800": f"{NO_INTRO_ROOT}/No-Intro/Atari - 2600 (20230330-104503).dat",
    "atari2600": f"{NO_INTRO_ROOT}/No-Intro/Atari - 2600 (20230330-104503).dat",
    "atari5200": f"{NO_INTRO_ROOT}/No-Intro/Atari - 5200 (20220405-183755).dat",
    "atari7800": f"{NO_INTRO_ROOT}/No-Intro/Atari - 7800 (20220714-205237).dat",
    "atarilynx": f"{NO_INTRO_ROOT}/No-Intro/Atari - Lynx (20230322-221226).dat",
    "atarijaguar": f"{NO_INTRO_ROOT}/No-Intro/Atari - Jaguar (J64) (20230312-215215).dat",
    "colecovision": f"{NO_INTRO_ROOT}/No-Intro/Coleco - ColecoVision (20230204-141322).dat",
    "gameandwatch": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Game & Watch (20211228-000000).dat",
    "gb": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Game Boy (20230413-112139).dat",
    "gba": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Game Boy Advance (20230412-152643).dat",
    "gbc": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Game Boy Color (20230402-224108).dat",
    "genesis": f"{NO_INTRO_ROOT}/No-Intro/Sega - Mega Drive - Genesis (20230413-082302).dat",
    "n64": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Nintendo 64 (BigEndian) (20230410-124148).dat",
    "n64dd": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Nintendo 64DD (20230131-042611).dat",
    "nes": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Nintendo Entertainment System (Headerless) (20230413-090934).dat",
    # "nes": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Nintendo Entertainment System (Headered) (20230413-090934).dat",
    "ngp": f"{NO_INTRO_ROOT}/No-Intro/SNK - NeoGeo Pocket (20230307-173713).dat",
    "ngpc": f"{NO_INTRO_ROOT}/No-Intro/SNK - NeoGeo Pocket Color (20230408-021339).dat",
    "sega32x": f"{NO_INTRO_ROOT}/No-Intro/Sega - 32X (20230308-124118).dat",
    "snes": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Super Nintendo Entertainment System (20230409-114707).dat",
    "virtualboy": f"{NO_INTRO_ROOT}/No-Intro/Nintendo - Virtual Boy (20230405-120113).dat",
    "wonderswan": f"{NO_INTRO_ROOT}/No-Intro/Bandai - WonderSwan (20230317-075216).dat",
    "wonderswancolor": f"{NO_INTRO_ROOT}/No-Intro/Bandai - WonderSwan Color (20230218-062956).dat",
}
REG_EX_COUNTRIES = (
    r"( \(("
    # Revisions / Beta
    r"Beta|Beta\s?\d|"
    r"Demo|Demo\s?\d|"
    r"Proto|Proto\s?\d|"
    r"Sample|Sample\s?\d|"
    r"Rev A|"
    r"Rev B|"
    r"Rev|Rev\s?\d+|"
    r"Rev|Rev\s?\d.\d+|"
    r"V\d+|"
    r"V\d.\d+|"
    r"v\d+|"
    r"v\d.\d+|"
    r"Disc\s?\d+|"
    r"SGB Enhanced\, GB Compatible|"
    r"Unknown|"
    r"Aftermarket|"
    r"Arcade|"
    r"Alt|"
    r"e-Reader Edition|"
    r"Earlier|"
    r"FamicomBox|"
    r"GameCube Edition|"
    r"GB Compatible|"
    r"J-Cart|"
    r"Not For Resale|"
    r"NP|"
    r"Pirate|"
    r"Program|"
    r"Rumble Version|"
    r"SGB Enhanced|"
    r"SegaNet|"
    r"Super Mega|"
    r"Switch|"
    r"Test Program|"
    r"Unl|"
    r"USA Wii Virtual Console, Wii U Virtual Console|"
    r"Virtual Console|"
    r"Virtual Console, Switch Online|"
    r"Wii Virtual Console|"
    r"Wii U Virtual Console|"
    # Collections
    r"C&E|"
    r"Idea-Tek|"
    r"Namcot Collection|"
    r"Piepacker.com|"
    r"Nei-Hu|"
    r"Victor|"
    # Countries
    r"Australia|"
    r"Brazil|"
    r"Brazil, Spain|"
    r"China|"
    r"Canada|"
    r"Europe|"
    r"France|"
    r"Germany|"
    r"Hong Kong|"
    r"Italy|"
    r"Ja|"
    r"Japan|"
    r"Japan, Europe|"
    r"Japan, Europe, Korea|"
    r"Japan, Korea|"
    r"Japan, USA|"
    r"Korea|"
    r"Mexico|"
    r"Netherlands|"
    r"Spain|"
    r"Sweden|"
    r"Taiwan|"
    r"United Kingdom|"
    r"USA|"
    r"USA, Australia|"
    r"USA, Europe|"
    r"USA, Europe, Korea|"
    r"USA, Korea|"
    # Region
    r"Asia|"
    r"En,Ja|"
    r"NTSC|"
    r"PAL|"
    r"World"
    r")\))"
    # \(((Asia|Korea|USA)(\, )?)+\)
)

REG_EX_LANG = r"\(((En-(US|GB)\,)+)?(\,)?(([A-Z][a-z]|[A-Z][a-z]\+[A-Z][a-z])(\,)?)+\)"
REG_EX_DATE = r" \([0-9]{4}-[0-9]{1,2}-[0-9]{1,2}\)"
REG_EX_EXTRAS = r"\[(SC|SL)(US)-[0-9]+ \([0-9].[0-9]+\)\]"


class NoIntroDb:
    def __init__(self, platform: str):
        self.platform = platform

        if platform not in PLATFORM_LOOKUP.keys():
            raise ValueError(f"Invalid Platform {platform}")

        with open(PLATFORM_LOOKUP[platform]) as df:
            self.no_intro_dat_file = xmltodict.parse(df.read())

    @staticmethod
    def platform_available(platform: str) -> bool:
        return platform in PLATFORM_LOOKUP.keys()

    def get_game_info_from_dat(self, hash, dat):
        for game in dat["datafile"]["game"]:
            if isinstance(game["rom"], list):
                for curr_file in game["rom"]:
                    if curr_file.get("@md5", "").upper() == hash.upper():
                        return curr_file
            elif isinstance(game["rom"], dict):
                curr_file = game["rom"]
                if curr_file.get("@md5", "").upper() == hash.upper():
                    return game
        return

    def get_game_info_from_filename(self, full_filename_path):
        # TODO: Handle zip files
        offset = 0

        # Nes roms
        if full_filename_path.endswith(".nes") and self.platform == "nes":
            offset = 16  # 16

        # Super Nintendo roms
        if (
            full_filename_path.endswith(".sfc")
            or full_filename_path.endswith(".smc")
            and self.platform == "snes"
        ):
            offset = 0

        hash = self.md5sum(
            full_filename_path, offset
        ).upper()  # no-intro dats checksums are uppercase

        # Get game name by hash
        game_no_intro = self.get_game_info_from_dat(hash, self.no_intro_dat_file)

        result = game_no_intro
        return result

    @staticmethod
    def get_regular_name_from_no_intro(no_intro_game):
        game_name = None
        if no_intro_game is not None:
            game_name = no_intro_game["@name"]
            all_reg_ex = [REG_EX_COUNTRIES, REG_EX_LANG, REG_EX_DATE, REG_EX_EXTRAS]
            for replacement in all_reg_ex:
                game_name = re.sub(replacement, "", game_name)
            if ", The" in game_name:
                game_name = "The " + game_name.replace(", The", "")
        return game_name

    def md5sum(self, filename, offset):
        h = hashlib.md5()
        with open(filename, "rb") as file:
            if offset > 0:
                file.read(offset)  # read files with an offset, for iNES roms etc
            chunk = 0
            while chunk != b"":
                chunk = file.read(1024)
                h.update(chunk)
        return h.hexdigest()
