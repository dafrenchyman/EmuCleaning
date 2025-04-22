import os

import pandas


class ArcadeDb:
    def __init__(self):
        db_file = f"{os.path.dirname(__file__)}/../database/arcade.csv"
        arcade_data = pandas.read_csv(db_file, sep=";")
        self.arcade_db = {}
        for idx, row in arcade_data.iterrows():
            self.arcade_db[row["name"]] = row.to_dict()
        return

    def convert_filename_to_game_name(self, filename):
        game_name_short = None
        game_name_long = None
        if filename in self.arcade_db:
            game_name_short = self.arcade_db.get(filename).get("short_title")
            game_name_long = self.arcade_db.get(filename).get("description")
        return game_name_short, game_name_long
