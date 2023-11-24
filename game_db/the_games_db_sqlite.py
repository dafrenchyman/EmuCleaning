import os
import sqlite3

from game_db.the_games_db_base import TheGamesDbBase


class TheGamesDbSqlite(TheGamesDbBase):
    def __init__(
        self,
        platform: str,
    ):
        # Load the sqlite3 DB
        db_file = f"{os.path.dirname(__file__)}/../database/tgdb.db"
        self.engine = sqlite3.connect(db_file)

        # Call the base constructor
        super().__init__(platform=platform)
        return


def main():
    games_db = TheGamesDbSqlite(platform="gc")

    game = games_db.get_games_db_from_game_name("Skies of Arcadia Legends")

    _ = games_db.download_all_art(game_db=game, art_path_root="/ROMs/.assets/")

    return


if __name__ == "__main__":
    main()
