import glob
import os
import sys
from os import path
from xml.etree import cElementTree

import xmltodict as xmltodict

from datomatic.generate_hashes import GenerateHashes
from gamesdb.the_games_db import TheGamesDb
from utils.downloader import download_binary_with_user_agent, check_url_exists


def main():
    SNES_DAT_FILE = "../config/Nintendo - Super Nintendo Entertainment System (Combined) (20200206-010456).dat"
    INPUT_ROMS_FOLDER = "../roms/snes/*.sfc"

    # Open GamesDB
    the_games_db = TheGamesDb()

    platform_id = the_games_db.get_platform_id_by_name("Super Nintendo (SNES)")

    # read dat
    with open(SNES_DAT_FILE) as df:
        doc = xmltodict.parse(df.read())
    games = doc["datafile"]["game"]

    # Create a dictionary lookup by sha1
    sha1_lookup = {}
    filename_lookup = {}
    for game in games:
        if "rom" in game:
            if "@sha1" in game["rom"]:
                sha1 = game["rom"]["@sha1"]
                sha1_lookup[sha1] = game
            if "@name" in game["rom"]:
                name = game["rom"]["@name"]
                filename_lookup[name] = game

    # Scan files
    for file in glob.glob(INPUT_ROMS_FOLDER):
        filename = os.path.basename(file)
        print(filename)
        sha1 = GenerateHashes().generate_sha1(file)

        # Check the SHA matches a real SHA
        if sha1 in sha1_lookup:
            game = sha1_lookup[sha1]
            game_name: str = game["@name"]

            game_id = the_games_db.get_id_by_name(game_name, platform_id)

            # Get gamesdb data
            game_data = the_games_db.get_game_data_by_id(game_id)

            # Download artwork

            # Front
            image_infos = [
                {
                    "type": "boxfront",
                    "url": "https://cdn.thegamesdb.net/images/original/boxart/front/",
                    "folder": "../artwork/boxart_front/",
                },
                {
                    "type": "boxback",
                    "url": "https://cdn.thegamesdb.net/images/original/boxart/back/",
                    "folder": "../artwork/boxart_back/",
                },
                {
                    "type": "fanart",
                    "url": "https://cdn.thegamesdb.net/images/original/fanart/",
                    "folder": "../artwork/fanart/",
                },
                {
                    "type": "screenshot",
                    "url": "https://cdn.thegamesdb.net/images/original/screenshots/",
                    "folder": "../artwork/screenshot/",
                },
            ]

            for image_info in image_infos:
                for i in range(1, 20):
                    front_url = f"{image_info['url']}{game_id}-{i}.jpg"
                    front_loc = f"{image_info['folder']}{game_id}-{i}.jpg"
                    if not path.isfile(front_loc):
                        if check_url_exists(front_url):
                            download_binary_with_user_agent(front_url, front_loc)
                        else:
                            break

            banner_url = (
                f"https://cdn.thegamesdb.net/images/original/graphical/{game_id}-g.jpg"
            )
            banner_loc = f"../artwork/banner/{game_id}-g.jpg"
            if not path.isfile(banner_url):
                if check_url_exists(banner_url):
                    download_binary_with_user_agent(banner_url, banner_loc)

            clearlogo_url = (
                f"https://cdn.thegamesdb.net/images/original/clearlogo/{game_id}.png"
            )
            clearlogo_loc = f"../artwork/clearlogo/{game_id}.png"
            if not path.isfile(clearlogo_loc):
                if check_url_exists(banner_url):
                    download_binary_with_user_agent(clearlogo_url, clearlogo_loc)

            # Generate XML nfo file
            platform_name = the_games_db.get_platform_name_by_id(platform_id)

            # Create XML
            root = cElementTree.Element("game")
            cElementTree.SubElement(root, "title").text = game_data["game_title"]
            cElementTree.SubElement(root, "originalTitle").text = game_name

            cElementTree.SubElement(root, "platform").text = platform_name
            cElementTree.SubElement(root, "plot").text = game_data["overview"]

            # publisher
            for publisher_id in game_data["publishers"]:
                publisher_name = the_games_db.get_publisher_by_id(publisher_id)
                cElementTree.SubElement(root, "publisher").text = publisher_name

            # developer
            for developer_id in game_data["developers"]:
                developer_name = the_games_db.get_developer_by_id(developer_id)
                cElementTree.SubElement(root, "developer").text = developer_name

            cElementTree.SubElement(root, "year").text = game_data["release_date"]

            # genre
            for genre_id in game_data["genres"]:
                genre_name = the_games_db.get_genre_by_id(genre_id)
                cElementTree.SubElement(root, "genre").text = genre_name

            cElementTree.SubElement(root, "maxPlayers").text = game_data["players"]

            # region
            if game_name.find("(USA)") > 0:
                cElementTree.SubElement(root, "region").text = "USA"
            else:
                cElementTree.SubElement(root, "region").text = ""

            cElementTree.SubElement(root, "media").text = ""
            cElementTree.SubElement(root, "perspective").text = ""
            cElementTree.SubElement(root, "controller").text = ""
            cElementTree.SubElement(root, "version").text = ""
            cElementTree.SubElement(root, "rating").text = ""
            cElementTree.SubElement(root, "votes").text = 0
            cElementTree.SubElement(root, "isFavorite").text = 0
            cElementTree.SubElement(root, "launchCount").text = 0

            for image_info in image_infos:
                image_type = image_info["type"]
                front_loc = f"{image_info['folder']}{game_id}-1.jpg"
                if path.isfile(front_loc):
                    cElementTree.SubElement(
                        doc, "thumb", local=front_loc, type=image_type
                    ).text = ""
            tree = cElementTree.ElementTree(root)

            nfo_output_file = os.path.splitext(file)[0] + ".nfo"
            tree.write(nfo_output_file)


if __name__ == "__main__":
    sys.exit(main())
