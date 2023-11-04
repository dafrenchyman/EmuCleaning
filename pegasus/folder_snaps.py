import os
import re
from pathlib import Path

from fuzzywuzzy import fuzz

COMMON_REGEX_REPLACEMENT = r"\(.* ?\)"


class FolderSnaps:
    def __init__(
        self,
        snaps_folder: str,
        relative_path: str,
    ):
        self.snaps_folder = snaps_folder
        # scan all files in folder
        snaps_lookup = {}
        snaps_lookup_2 = {}
        for filename in sorted(os.listdir(self.snaps_folder)):
            # Full filename (no extension) key
            full_filename_path = os.path.join(self.snaps_folder, filename)
            filename_no_ext = Path(filename).stem
            snaps_lookup[filename_no_ext] = full_filename_path.replace(
                relative_path, ""
            )

            # Name without (stuff)
            game_name = re.sub(COMMON_REGEX_REPLACEMENT, "", filename_no_ext).strip()
            snaps_lookup_2[game_name] = full_filename_path.replace(relative_path, "")

        self.snaps_lookup = snaps_lookup
        self.snaps_lookup_2 = snaps_lookup_2

    def get_full_filename_path_from_game_name(self, game_name):
        best_fuzz_score = 0
        best_fuzz_location = None
        best_match = None

        # Check if the key exists for a fast exit
        if game_name in self.snaps_lookup.keys():
            return self.snaps_lookup[game_name]

        game_name_no_extras = re.sub(COMMON_REGEX_REPLACEMENT, "", game_name).strip()

        # Loop through every game in the DB and see which one is the best
        for curr_game_name, all_games in zip(
            [game_name, game_name_no_extras], [self.snaps_lookup, self.snaps_lookup_2]
        ):
            for key, game in all_games.items():
                fuzz_score = fuzz.ratio(curr_game_name, key)
                if fuzz_score > 90 and fuzz_score > best_fuzz_score:
                    best_fuzz_score = fuzz_score
                    best_fuzz_location = key

            if best_fuzz_location is not None:
                best_match = all_games.get(best_fuzz_location)
                break

        return best_match
