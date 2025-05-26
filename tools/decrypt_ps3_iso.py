import hashlib
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas
import xmltodict

# https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%203/

FOLDER = "/mnt/SnapArray02/Snap2_SSD_8TB_17/Consoles/Sony - Playstation 3/Games/S/"
DKEY_CSV = (
    "/mnt/SnapArray02/Snap2_SSD_8TB_09/Consoles/Sony - Playstation 3/Tools/ps3_dkey.csv"
)

# DAT_FILE comes from: http://redump.org/datfile/ps3/
DAT_FILE = "/home/mrsharky/src/EmuCleaning/tools/Sony - PlayStation 3 - Datfile (4418) (2025-02-01 21-15-43).dat"

# DKEYs from: http://redump.org/dkeys/ps3/
DKEY_FOLDER = "/mnt/SnapArray02/Snap2_SSD_8TB_09/Consoles/Sony - Playstation 3/Tools/Disc Keys TXT (4367) (2025-02-01 21-15-43)/"
PS3_dec_binary = "/home/mrsharky/dev/ps3/PS3Dec/build/Release/PS3Dec"


def md5sum(filename):
    md5 = hashlib.md5()
    # chunk_size = 4096
    # chunk_size = 65536
    chunk_size = 1_048_576
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)
    return md5.hexdigest()


def system_md5sum(filename):
    result = subprocess.run(["md5sum", filename], capture_output=True, text=True)
    return result.stdout.split()[0]


def generate_disc_keys_lookup():
    all_files = sorted(os.listdir(DKEY_FOLDER), reverse=False)
    disc_keys = {}
    for filename in all_files:
        filename_no_ext = Path(filename).stem
        full_path_filename = f"{DKEY_FOLDER}{filename}"

        with open(full_path_filename) as disc_key_file:
            key = disc_key_file.read()

        disc_keys[f"{filename_no_ext}.iso".upper()] = key.strip()
    return disc_keys


def generate_dat_file():
    with open(DAT_FILE) as df:
        no_intro_dat_file = xmltodict.parse(df.read())
    return no_intro_dat_file


def generate_lookups():
    disc_keys = generate_disc_keys_lookup()
    dat_file = generate_dat_file()

    serial_data = pandas.read_csv(DKEY_CSV)
    serial_data["Filename"] = serial_data["Filename"].str.upper()
    serial_data["MD5"] = serial_data["MD5"].str.upper()

    # Generate a cleaned version containing both
    filename_to_data = {}
    md5_to_data = {}
    for curr_game in dat_file["datafile"]["game"]:
        if isinstance(curr_game["rom"], list):
            roms = curr_game["rom"]
        else:
            roms = [curr_game["rom"]]
        for rom in roms:
            game_filename = rom["@name"]

            game_filename_extension = Path(game_filename).suffix
            if game_filename_extension in [".bin", ".cue"]:
                continue

            game_size = int(rom["@size"])
            game_crc = rom["@crc"].upper().strip()
            game_md5 = rom["@md5"].upper().strip()
            game_sha = rom["@sha1"].upper().strip()

            game_dkey = disc_keys.get(game_filename.upper(), None)

            # find serial number
            matching_rows = serial_data[
                serial_data["Filename"] == game_filename.upper()
            ]
            game_serial = "Unknown"
            if matching_rows.shape[0] == 1:
                game_serial = matching_rows.iloc[0]["GameID"]
            else:
                # See if we can find a match via md5
                matching_rows = serial_data[serial_data["MD5"] == game_md5]
                if matching_rows.shape[0] == 1:
                    game_serial = matching_rows.iloc[0]["GameID"]
                # elif "(USA)" in game_filename:
                #     game_serial = "BLUS"
                else:
                    print(f"Unknown Serial: {game_filename}")
                    raise Exception(f"Unknown Serial: {game_filename}")

            if game_dkey is not None:
                curr_game_data = {
                    "filename": game_filename,
                    "size": game_size,
                    "crc": game_crc,
                    "md5": game_md5,
                    "sha1": game_sha,
                    "dkey": game_dkey,
                    "id": game_serial,
                }
                filename_to_data[game_filename.upper()] = curr_game_data
                md5_to_data[game_md5] = curr_game_data
    return filename_to_data, md5_to_data


def main():
    # Load lookup data
    # dkey_data = pandas.read_csv(DKEY_CSV)
    filename_to_data, md5_to_data = generate_lookups()

    # Create processing folders
    invalid_folder_name = "invalid_md5"
    no_match_folder_name = "no_match"
    processed_folder_name = "processed"
    for folder in [invalid_folder_name, no_match_folder_name, processed_folder_name]:
        Path(f"{FOLDER}{folder}/").mkdir(parents=True, exist_ok=True)

    all_files = sorted(os.listdir(FOLDER), reverse=False)

    # Loop on files in folder
    for filename in all_files:
        actual_md5 = None
        filename_no_ext = Path(filename).stem
        full_path_filename = f"{FOLDER}{filename}"

        # Skip DIRs
        if os.path.isdir(full_path_filename):
            continue

        # print(f"Processing: {filename}")
        matched_game = filename_to_data.get(filename.upper())

        # If it's not matched, and the file has an "iso" extension and it was generated prior to
        # 1997, run md5sum on it to find out if it's just named wrong.
        mod_time = os.path.getmtime(full_path_filename)  # Last modification time
        mod_time_datetime = datetime.fromtimestamp(mod_time)
        game_filename_extension = Path(full_path_filename).suffix
        if (
            matched_game is None
            and mod_time_datetime < datetime(1997, 1, 1)
            and game_filename_extension.upper() == ".ISO"
        ):
            # Get the MD5
            print(f"Name invalid, calculating MD5: {filename}")
            actual_md5 = system_md5sum(full_path_filename).upper().strip()

            # Check the MD5 is in our other lookup
            matched_md5 = md5_to_data.get(actual_md5)
            if matched_md5:
                # Get what the filename "should" be
                filename = matched_md5["filename"]
                filename_no_ext = Path(filename).stem
                new_full_filename_from_md5 = f"{FOLDER}{filename}"

                # Rename the file to what it "should" be
                print(
                    f"\tRenaming file from: {full_path_filename}\t -> {new_full_filename_from_md5}"
                )
                os.rename(full_path_filename, new_full_filename_from_md5)
                full_path_filename = new_full_filename_from_md5

                matched_game = matched_md5

        # If we don't have a match skip the file
        if matched_game is None:
            # print("\tNo match")
            continue

        # Continue if we do

        game_id = matched_game["id"]
        _game_size = matched_game["size"]  # noqa: F841
        game_md5 = matched_game["md5"].upper().strip()
        game_dkey = matched_game["dkey"]

        # See if we've already processed the file (if so skip)
        new_filename = f"{filename_no_ext} ({game_id}).iso"
        new_full_filename = f"{FOLDER}{new_filename}"
        if os.path.exists(new_full_filename):
            print(f"\tAlready Processed: {filename}")
            continue

        if game_dkey is None:
            print("\tInvalid decryption key")
            continue

        # Get the actual MD5 of the file
        if actual_md5 is None:
            print(f"Calculating MD5: {filename}")
            actual_md5 = system_md5sum(full_path_filename).upper().strip()

        # If the md5s don't match, don't process this file
        if game_md5 != actual_md5:
            # It's possible the file is miss-named.
            if actual_md5 in md5_to_data.keys():
                matched_game = md5_to_data[actual_md5]
                print(f"\tMD5 found on another filename: {matched_game['filename']}")
            new_filename = f"{invalid_folder_name}/{filename}"
            new_full_filename = f"{FOLDER}{new_filename}"
            print("\tInvalid MD5")
            print(f"\t{filename} - {actual_md5}")

            # Rename the file specifying the issue
            os.rename(full_path_filename, new_full_filename)
            continue

        # Since the md5s match, time to decrypt it
        decrypt_command = [
            f"{PS3_dec_binary}",
            "d",
            "key",
            f"{game_dkey}",
            f"{full_path_filename}",
            f"{new_full_filename}",
        ]

        print(f"\tDecoding: {filename}")
        process = subprocess.Popen(decrypt_command, stdout=subprocess.PIPE)
        output, error = process.communicate()
        if error is not None:
            raise Exception("Failed decoding")

        processed_file_name = f"{FOLDER}{processed_folder_name}/{filename}"
        os.rename(full_path_filename, processed_file_name)

    return


if __name__ == "__main__":
    sys.exit(main())
