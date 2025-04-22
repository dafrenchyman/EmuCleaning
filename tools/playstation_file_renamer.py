import os
import re
import sys

FOLDER = "/mnt/SnapSsdArray_01/SnapDisk_4TB_25/Consoles/.artwork/PS1/Screenshots/"

REG_EX_EXTRAS = " (\[.*\])"  # noqa W605


def main():
    all_files = sorted(os.listdir(FOLDER), reverse=False)

    # Loop on files in folder
    for filename in all_files:
        new_filename = filename

        # Change [NTSC-U] to (USA)
        new_filename = new_filename.replace("[NTSC-U]", "(USA)")

        # remove [junk] [junk2] from filename
        all_reg_ex = [REG_EX_EXTRAS]
        for replacement in all_reg_ex:
            new_filename = re.sub(replacement, "", new_filename)
        old_filename_path = os.path.join(FOLDER, filename)
        new_filename_path = os.path.join(FOLDER, new_filename)

        os.rename(old_filename_path, new_filename_path)

    return


if __name__ == "__main__":
    sys.exit(main())
