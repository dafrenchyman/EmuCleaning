import sqlalchemy

from game_db.the_games_db_base import TheGamesDbBase

THEGAMESDB_JSON_LOCAL = "./database/games-db-database-latest.json"
THEGAMESDB_JSON_URL = "https://cdn.thegamesdb.net/json/database-latest.json"
THEGAMESDB_SQL_DUMP = "http://cdn.thegamesdb.net/tgdb_dump.zip"


class TheGamesDbSql(TheGamesDbBase):
    def __init__(
        self,
        platform: str,
        host: str = "10.152.183.234",
        user: str = "root",
        password: str = "root",
        port: int = 3306,
        database: str = "thegamesdb",
    ):
        connect_string = f"mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}"  # pragma: allowlist secret
        self.engine = sqlalchemy.create_engine(connect_string)

        # Call the base constructor
        super().__init__(platform=platform)
        return
