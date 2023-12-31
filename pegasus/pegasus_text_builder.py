import os
import re

from game_db.the_games_db_base import TheGamesDbBase

IMAGE_TYPES = {
    "screenshot": "screenshots/",
    "boxback": "boxart/back/",
    "boxfront": "boxart/front/",
    "gameplay": "gameplay/",
    "clearlogo": "clearlogo/",
    "fanart": "fanart/",
    "cartridge": "cartridge/",
}

NO_INTRO_REGION_LOOKUP = {
    "AUS": "Australia",
    "CAN": "Canada",
    "EUR": "Europe",
    "FRA": "France",
    "GER": "Germany",
    "HOL": "Netherlands",
    "ITA": "Italy",
    "JPN": "Japan",
    "SPA": "Spain",
    "SWE": "Sweden",
    "USA": "USA",
}

TYPE_EXPRESSION = (
    r"(\(([Uu]nl|[Bb]eta|[Rr]ev|[Pp]roto|[Dd]emo|[Ss]ample|[Aa]rcade)([ ]([0-9]))?\))"
)
ALLOWED_TYPES = ["ARCADE", "REV", "UNL"]  # , "BETA", "PROTO"

START_OF_TEXT = {
    "3do": """
collection: Panasonic 3DO
shortname: 3do
command: /bin/rom_launcher.sh 3do "{file.path}"

""",
    "amiga": """
collection: Commodore Amiga
shortname: amiga
command: /bin/rom_launcher.sh amiga "{file.path}"

""",
    "amigacd32": """
collection: Commodore Amiga CD 32
shortname: amigacd32
command: /bin/rom_launcher.sh amigacd32 "{file.path}"

""",
    "arcade": """
collection: Arcade
shortname: arcade
command: /bin/rom_launcher.sh arcade "{file.path}"

""",
    "atari2600": """
collection: Atari 2600
shortname: atari2600
command: /bin/rom_launcher.sh atari2600 "{file.path}"

""",
    "atari5200": """
collection: Atari 5200
shortname: atari5200
command: /bin/rom_launcher.sh atari5200 "{file.path}"

""",
    "atari7800": """
collection: Atari 7800
shortname: atari7800
command: /bin/rom_launcher.sh atari7800 "{file.path}"

""",
    "atarijaguar": """
collection: Atari Jaguar
shortname: atarijaguar
command: /bin/rom_launcher.sh atarijaguar "{file.path}"

""",
    "atarijaguarcd": """
collection: Atari Jaguar CD
shortname: atarijaguarcd
command: /bin/rom_launcher.sh atarijaguarcd "{file.path}"

""",
    "atarilynx": """
collection: Atari Lynx
shortname: atarilynx
command: /bin/rom_launcher.sh atarilynx "{file.path}"

""",
    "atarist": """
collection: Atari ST
shortname: atarist
command: /bin/rom_launcher.sh atarist "{file.path}"

""",
    "colecovision": """
collection: Coleco ColecoVision
shortname: colecovision
command: /bin/rom_launcher.sh colecovision "{file.path}"

""",
    "dreamcast": """
collection: Sega Dreamcast
shortname: dreamcast
command: /bin/rom_launcher.sh dreamcast "{file.path}"

""",
    "genesis": """
collection: Sega Genesis
shortname: genesis
command: /bin/rom_launcher.sh genesis "{file.path}"

""",
    "gb": """
collection: Game Boy
shortname: gb
command: /bin/rom_launcher.sh gb "{file.path}"

""",
    "gba": """
collection: Game Boy Advance
shortname: gba
command: /bin/rom_launcher.sh gba "{file.path}"

""",
    "gbc": """
collection: Game Boy Color
shortname: gbc
command: /bin/rom_launcher.sh gbc "{file.path}"

""",
    "gc": """
collection: Nintendo Gamecube
shortname: gc
command: /bin/rom_launcher.sh gc "{file.path}"

""",
    "megacd": """
collection: Sega Mega CD
shortname: megacd
command: /bin/rom_launcher.sh megacd "{file.path}"

""",
    "n64": """
collection: Nintendo 64
shortname: n64
command: /bin/rom_launcher.sh n64 "{file.path}"

""",
    "neogeo": """
collection: SNK Neo Geo
shortname: neogeo
command: /bin/rom_launcher.sh neogeo "{file.path}"

""",
    "nes": """
collection: Nintendo (NES)
shortname: nes
command: /bin/rom_launcher.sh nes "{file.path}"

""",
    "ngp": """
collection: SNK Neo Geo Pocket
shortname: ngp
command: /bin/rom_launcher.sh ngp "{file.path}"

""",
    "ngpc": """
collection: SNK Neo Geo Pocket Color
shortname: ngpc
command: /bin/rom_launcher.sh ngpc "{file.path}"

""",
    "pcengine": """
collection: NEC PC Engine
shortname: pcengine
command: /bin/rom_launcher.sh pcengine "{file.path}"

""",
    "pcenginecd": """
collection: NEC PC Engine CD
shortname: pcenginecd
command: /bin/rom_launcher.sh pcenginecd "{file.path}"

""",
    "ps2": """
collection: Sony Playstation 2
shortname: ps2
command: /bin/rom_launcher.sh ps2 "{file.path}"

""",
    "ps3": """
collection: Sony Playstation 3
shortname: ps3
command: /bin/rom_launcher.sh ps3 "{file.path}"

""",
    "psp": """
collection: Sony Playstation Portable
shortname: psp
command: /bin/rom_launcher.sh psp "{file.path}"

""",
    "psx": """
collection: Sony Playstation
shortname: psx
command: /bin/rom_launcher.sh psx "{file.path}"

""",
    "saturn": """
collection: Sega Saturn
shortname: saturn
command: /bin/rom_launcher.sh saturn "{file.path}"

""",
    "sega32x": """
collection: Sega 32X
shortname: sega32x
command: /bin/rom_launcher.sh sega32x "{file.path}"

""",
    "segacd": """
collection: Sega CD
shortname: segacd
command: /bin/rom_launcher.sh segacd "{file.path}"

""",
    "snes": """
collection: Super Nintendo (SNES)
shortname: snes
command: /bin/rom_launcher.sh snes "{file.path}"

""",
    "snes_widescreen": """
collection: Super Nintendo (SNES) Widescreen
shortname: snes_widescreen
command: /bin/rom_launcher.sh snes_widescreen "{file.path}"

""",
    "switch": """
collection: Nintendo - Switch
shortname: switch
command: /bin/rom_launcher.sh switch "{file.path}"

""",
    "tg-cd": """
collection: NEC Turbo Grafx CD
shortname: tg-cd
command: /bin/rom_launcher.sh tg-cd "{file.path}"

""",
    "virtualboy": """
collection: Nintendo Virtual Boy
shortname: virtualboy
command: /bin/rom_launcher.sh virtualboy "{file.path}"

""",
    "wii": """
collection: Nintendo Wii
shortname: wii
command: /bin/rom_launcher.sh gc "{file.path}"

""",
    "wiiu": """
collection: Nintendo WiiU
shortname: wiiu
command: /bin/rom_launcher.sh wiiu "{file.path}"

""",
    "wonderswan": """
collection: Bandai - WonderSwan
shortname: wonderswan
command: /bin/rom_launcher.sh wonderswan "{file.path}"

""",
    "wonderswancolor": """
collection: Bandai - WonderSwan Color
shortname: wonderswancolor
command: /bin/rom_launcher.sh wonderswancolor "{file.path}"

""",
    "xbox": """
collection: Microsoft Xbox
shortname: xbox
command: /bin/rom_launcher.sh xbox "{file.path}"

""",
}


class PegasusTextBuilder:
    def __init__(self, the_games_db: TheGamesDbBase, platform: str) -> None:
        self.the_games_db = the_games_db
        self.text = START_OF_TEXT[platform]
        self.platform = platform
        return

    def get_image_filename(self, game_db, image_type):
        game_db_id = game_db["id"]
        if image_type in IMAGE_TYPES.keys():
            image_type_path = IMAGE_TYPES[image_type]
            image_path = os.path.join(
                self.artwork_root, f"{image_type_path}{game_db_id}-1.jpg"
            )
            if os.path.isfile(image_path):
                return image_path
        return ""

    regions = {
        "(Australia)": "Australia",
        "(Brazil)": "Brazil",
        "(Canada)": "Canada",
        "(Europe)": "Europe",
        "(France)": "France",
        "(Germany)": "Germany",
        "(Hong Kong)": "Hong Kong",
        "(Italy)": "Italy",
        "(Japan)": "Japan",
        "(Korea)": "Korea",
        "(Netherlands)": "Netherlands",
        "(Spain)": "Spain",
        "(Sweden)": "Sweden",
        "(USA)": "USA",
    }

    def region_from_game_name(self, game_name):
        if game_name is None:
            return ""
        for region in self.regions.keys():
            regexp = re.compile(region)
            if regexp.search(game_name):
                return self.regions[region]
        return ""

    def add_entry(
        self,
        filename: str,
        game_db,
        internet_game_db,
        no_intro,
        images,
        game_title=None,
        full_filename_path=None,
    ):
        # region
        release = no_intro.get("release", None)
        region = None
        if release is not None:
            release_region = release.get("@region", None)
            region = NO_INTRO_REGION_LOOKUP[release_region]
        if region is None:
            region = self.region_from_game_name(no_intro.get("@name"))

        developers = self.the_games_db.get_developers_by_game_id(game_db["id"])
        developers = "\n  ".join([i["developer_name"] for i in developers.values()])
        publishers = self.the_games_db.get_publishers_by_game_id(game_db["id"])
        publishers = "\n  ".join([i["publisher_name"] for i in publishers.values()])

        genre = self.the_games_db.get_genres_by_game_id(game_db["id"])
        genre = "\n  ".join([i["genre"] for i in genre.values()])

        if game_title is None:
            game_title = os.path.splitext(os.path.basename(filename))[0]

        description = game_db.get("overview", "")
        if description is None:
            description = ""
        description = description.replace("\n", "").replace("\r", "")

        # Assets
        box_front = "\n  ".join(images["boxart_front"])
        box_back = "\n  ".join(images["boxart_back"])
        box_full = "\n  ".join(images["boxart_full"])
        box_spine = "\n  ".join(images["boxart_spine"])
        cart = "\n  ".join(images["cart"])
        logo = "\n  ".join(images["clearlogo"])
        screenshot = "\n  ".join(images["screenshot"])
        background = "\n  ".join(images["fanart"])
        titlescreen = "\n  ".join(images["titlescreen"])
        banner = "\n  ".join(images["banner"])
        music = "\n  ".join(images["music"])
        video = "\n  ".join(images["video"])
        poster = "\n  ".join(images["poster"])
        rating = ""
        if internet_game_db is not None:
            rating = internet_game_db.get("total_rating", None)
            rating = rating / 100 if rating is not None else ""

        # Figure out type
        type_match = re.compile(TYPE_EXPRESSION)
        expression = type_match.search(filename)
        if expression:
            rom_type = expression.group(2)

            if rom_type.upper() not in ALLOWED_TYPES:
                print(f"\tSkipping {filename}")
                return
            # rom_type_version = expression.group(4)
            # complete_rom_type = expression.group(1)
            # game_title_extras = complete_rom_type

        # PS3 needs to link to the <game_folder>/PS3_GAME/USRDIR/EBOOT.BIN
        if self.platform == "ps3":
            ps3_eboot_file = "PS3_GAME/USRDIR/EBOOT.BIN"
            filename = f"{filename}/{ps3_eboot_file}"

            # If the file doesn't exist, don't write an entry
            full_eboot_path = f"{full_filename_path}/{ps3_eboot_file}"
            if not os.path.isfile(full_eboot_path):
                print(f"Skipping, file doesn't exists: {full_eboot_path}")
                return

        # The complete text
        self.text += f"""\n
game: {game_title}
sort-by: {game_title}
file: {filename}
description: {description}
release: {game_db.get('release_date', '')}
region: {region}
developer: {developers}
publisher: {publishers}
genre: {genre}
players: {str(game_db.get('players',1))}
rating: {rating}
assets.box_front: {box_front}
assets.box_back: {box_back}
assets.box_full: {box_full}
assets.box_spine: {box_spine}
assets.cart: {cart}
assets.logo: {logo}
assets.screenshot: {screenshot}
assets.background: {background}
assets.titlescreen: {titlescreen}
assets.banner: {banner}
assets.video: {video}
assets.music: {music}
assets.poster: {poster}

"""
        return
