import json
import os
import re
import sys

import requests
from fuzzywuzzy import fuzz, process

API_KEY = "1e821bf1bab06854840650d77e7e2248f49583821ff9191f2cced47e43bf0a73"
GAME_NAME_URL = "https://api.thegamesdb.net/Games/ByGameName"

PLAYERS_LOOKUP = {
    "1 Player": 1,
    "1-2 Players": 2,
    "1-3 Players": 3,
    "1-4 Players": 4,
    "1-5 Players": 5,
    "1-6 Players": 6,
    "1-7 Players": 7,
    "1-8 Players": 8,
    "1-16 Players": 16,
}


def get_region(title):
    if "(USA)" in title:
        return "USA"
    elif "(Europe)" in title:
        return "Europe"
    else:
        return ""


def get_version(title):
    if "(v1.0)" in title:
        return 1.0
    if "(v1.1)" in title:
        return 1.1
    if "(v1.2)" in title:
        return 1.2
    if "(v1.3)" in title:
        return 1.3
    if "(v1.4)" in title:
        return 1.4
    if "(v1.5)" in title:
        return 1.5
    else:
        return 1.0


PLATFORM_ID = {"Sony Playstation": 10}


def main():
    # Convert database to json
    platform = "Sony Playstation"

    database = []
    if not os.path.isfile(platform + ".json"):
        # Load Database csv file into memory
        database_csv = platform + ".csv"

        with open(database_csv) as fp:
            for line in fp:
                game_info = line.split(">")

                # Original fields
                full_name = game_info[0]
                name = game_info[1]
                year = game_info[2]
                rating = game_info[3]
                publisher = game_info[4]
                developer = game_info[5]
                genre = game_info[6]
                score = game_info[7]
                players = game_info[8]
                description = game_info[9]

                database.append(
                    {
                        # Original fields
                        "name": name,
                        "full_name": full_name,
                        "year": year,
                        "rating": rating,
                        "publisher": publisher,
                        "developer": developer,
                        "genre": genre,
                        "score": score,
                        "players": players,
                        "description": description,
                        # rom collection browser fields
                        "title": name,
                        "originalTitle": "",
                        "alternateTitle": "",
                        "platform": platform,
                        "plot": description,
                        "detailUrl": "",
                        "maxPlayer": PLAYERS_LOOKUP[players],
                        "region": get_region(full_name),
                        "media": "",
                        "perspective": "",
                        "controller": "",
                        "version": get_version(full_name),
                        "votes": 0,
                        "isFavorite": 0,
                        "launchCount": 0,
                    }
                )

        database_json = json.dumps(database, indent=2, separators=(",", ":"))

        with open(platform + ".json", "w") as json_file:
            json_file.write(database_json)
    else:
        with open(platform + ".json") as fp:
            database = json.load(fp)

    # Add thegamesdb id to the json
    for counter, curr_game in enumerate(database):
        curr_name = curr_game["name"]
        curr_year = curr_game["year"]

        if "thegamesdb_id" not in curr_game.keys():
            # Clean up the `curr_name` field
            curr_name = curr_name.replace("  Disc 1", "")
            curr_name = curr_name.replace("  Disc 2", "")
            curr_name = curr_name.replace("  Disc 3", "")
            curr_name = curr_name.replace("  Disc 4", "")
            curr_name = curr_name.replace("  Disc 5", "")
            curr_name = curr_name.replace("  Disc 6", "")
            curr_name = curr_name.replace(" - ", ": ")

            # Get the game data from thegamesdb
            params = {
                "apikey": API_KEY,
                "name": curr_name,
                "platform": PLATFORM_ID[platform],
            }
            r = requests.get(url=GAME_NAME_URL, params=params)

            # extracting data in json format
            data = r.json()
            potential_matches = data["data"]["games"]

            scraper_matches = []
            for curr_match in potential_matches:
                db_release_date = curr_match["release_date"]

                if db_release_date is not None:
                    db_release_year = db_release_date.split("-")[0]
                    if (
                        PLATFORM_ID[platform] == curr_match["platform"]
                        and curr_year == db_release_year
                    ):
                        scraper_matches.append(curr_match)

            if len(scraper_matches) == 1:
                game_db_name = scraper_matches[0]["game_title"]
                games_db_id = scraper_matches[0]["id"]

                if fuzz.ratio(curr_name, game_db_name) >= 95:
                    database[counter]["thegamesdb_id"] = games_db_id

                    database_json = json.dumps(
                        database, indent=2, separators=(",", ":")
                    )
                    with open(platform + ".json", "w") as json_file:
                        json_file.write(database_json)
                else:
                    print(
                        f"Skipping Orig:{curr_name}, GDB:{game_db_name}, ID:{games_db_id} "
                    )

            if data["remaining_monthly_allowance"] <= 100:
                break

        else:
            print(f"Already processed: {curr_name}")

    if False:
        # Create a list from the dictionary values
        games_list = list(database.keys())

        # See which file the game must belong to
        files = os.listdir("/Users/appfolio/Code/emu/PSX")
        for file in files:
            if file.upper().endswith(".PBP"):
                game_name = os.path.splitext(file)[0]
                game_name = re.sub(r"\(USA\)", "", game_name)
                game_name = game_name.strip()
                best_match = process.extractOne(game_name, games_list)
                best_match_name = best_match[0]
                best_match_score = best_match[1]

                curr_game_data = database[best_match_name]
                curr_year = curr_game_data["year"]

                print(f"{game_name} | {best_match_name} | {best_match_score}")

                # Get the game data from thegamesdb
                params = {"apikey": API_KEY, "name": best_match_name, "platform": 10}
                r = requests.get(url=GAME_NAME_URL, params=params)

                # extracting data in json format
                data = r.json()
                potential_matches = data["data"]["games"]

                scraper_matches = [
                    curr_match
                    for curr_match in potential_matches
                    if curr_match["release_date"].split("-")[0] == curr_year
                ]

                if len(scraper_matches) == 1:
                    games_db_id = scraper_matches[0]["id"]
                    database[best_match_name]["thegamesdb_id"] = games_db_id

                database[best_match_name]

    return


if __name__ == "__main__":
    sys.exit(main())
