# EmuCleaning

This code is currently a mess. It needs a lot of cleanup.

## Setup for developement:

- Setup a python 3.x venv (usually in `.venv`)
- `pip3 install --upgrade pip`
- Install pip-tools `pip3 install pip-tools`
- Update dev requirements: `pip-compile --output-file=requirements.dev.txt requirements.dev.in`
- Update requirements: `pip-compile --output-file=requirements.txt requirements.in`
- Install dev requirements `pip3 install -r requirements.dev.txt`
- Install requirements `pip3 install -r requirements.txt`
- `pre-commit install`

## Run `pre-commit` locally.

`pre-commit run --all-files`

## Create baseline secrets file

`detect-secrets scan > .secrets.baseline`

# To write a Pegasus Front-end `metadata-pegasus.txt` file

Code is in the Pegasus folder.

You'll need to set the following environment variables:

```
IGDB_CLIENT_ID="..."
IGDB_API_KEY="..."
STEAM_GRID_DB_API_KEY="..."
```

You'll need to get these from their respective sources. They're free.

## To get dat files:

Datomatic files are used to check the hashes of ROMs and get clean names for them.

- Go to the daily page: https://datomatic.no-intro.org/index.php?page=download&s=64&op=daily
- Checkmark all the stuff you want and download
- Currently, everything is hard coded, you'll need to modify the file locations in: `game_db/no_intro_db.py`

## To get arcade info files:

- Go to http://adb.arcadeitalia.net/lista_mame.php and then click options and then download the `Detailed CSV`. Don't filter on anything so you can grab everything.
- Extract the file and name it `./database/arcade.csv`

## Convert GamesDB sqldump to sqlite3

- Run the `setup.sh` script in the root. it **should** take care of it.

## Adding assets from https://emumovies.com

- In the folder that has the roms for a given platform
- Add a `.assets` folder
- In there, add the following folders for whatever assets you have:
  - `background`: AKA fanarts
  - `box_back`: Back of boxes
  - `box_front`: Front of boxes
  - `box_full`: The whole box front/back/side
  - `box_spine`: The spine (side) of the box
  - `cart`: What the cart looks like
  - `cart_label`: Just the carts label
  - `logo`: Clear logos (png)
  - `music`: Music for the game (I'm not sure any themes support this)
  - `screenshot`: Game screenshot
  - `titlescreen`: Game's titlescreen
  - `video`: A video snap

# Convert PSX bin/cue to chd

This is something I wrote a while back to clean up zipped bin/cue files and convert them to chd.
Everything runs in a container.

- It's in the `./docker` folder
- Modify the docker-compose.yml to point to your zipped bin/cue files
- Build the container
- Run the container

# `rom_collection_browser`

This work is dead.
