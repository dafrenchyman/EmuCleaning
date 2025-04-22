import os
import re
import zipfile

import requests
import yaml
from fuzzywuzzy import fuzz


class ScummVmDB:
    def __init__(self):
        self.game_list = "https://raw.githubusercontent.com/scummvm/scummvm-web/master/data/en/games.yaml"
        self.game_compat = "https://raw.githubusercontent.com/scummvm/scummvm-web/master/data/en/compatibility.yaml"

        db_file = f"{os.path.dirname(__file__)}/../database/scummvm_games.yaml"
        if not os.path.exists(db_file):
            response = requests.get(self.game_list)

            if response.status_code == 200:
                with open(db_file, "wb") as f:
                    f.write(response.content)
                print("File downloaded successfully!")
            else:
                raise Exception(
                    f"Error downloading file. Status code: {response.status_code}"
                )

        with open(db_file, "r") as file:
            self.game_list = yaml.safe_load(file)
        return

    def get_scummvm_from_game_name(self, game_name):
        best_fuzz_score = 0
        best_fuzz_location = None
        best_match = None

        # Clean the game_name
        all_reg_ex = [
            r"(\([a-zA-Z0-9 ,]+\))",
        ]

        for replacement in all_reg_ex:
            game_name = re.sub(replacement, "", game_name)

        game_name = game_name.strip()

        # Loop through every game in the DB and see which one is the best
        for idx, game in enumerate(self.game_list):
            # Fix the game name stuff
            fuzz_score = fuzz.ratio(game_name, game.get("name"))
            if fuzz_score > 50 and fuzz_score > best_fuzz_score:
                best_fuzz_score = fuzz_score
                best_fuzz_location = idx

        if best_fuzz_location is not None:
            best_match = self.game_list[best_fuzz_location]
        return best_match

    def create_lookup_file(self, full_filename_path, scumm_vm_info) -> None:
        scumm_vm_id_name = scumm_vm_info.get("id")

        # Create a .scummvm file inside of the zip file (if it doesn't already exist)
        scumm_vm_shortname = scumm_vm_id_name.split(":")[1]
        scumm_vm_filename = f"{scumm_vm_shortname}.scummvm"
        scumm_vm_file_present = False
        with zipfile.ZipFile(full_filename_path) as scumm_zip:
            if scumm_vm_filename in scumm_zip.namelist():
                scumm_vm_file_present = True

        if not scumm_vm_file_present:
            with zipfile.ZipFile(full_filename_path, "a") as zipped_f:
                zipped_f.writestr(scumm_vm_filename, scumm_vm_shortname)
        return
