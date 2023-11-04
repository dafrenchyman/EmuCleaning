import os

from pegasus.folder_snaps import FolderSnaps


class LocalFiles:
    def __init__(
        self,
        rom_folder: str,
    ):
        # Backgrounds
        root_folder = f"{rom_folder}.assets/"
        backgrounds_folder = f"{root_folder}background/"
        self.backgrounds_folder = (
            backgrounds_folder if os.path.isdir(backgrounds_folder) else None
        )
        self.backgrounds_snap = (
            FolderSnaps(
                snaps_folder=self.backgrounds_folder,
                relative_path=rom_folder,
            )
            if self.backgrounds_folder is not None
            else None
        )

        # Boxart Back
        boxart_back_folder = f"{root_folder}box_back/"
        self.boxart_back_folder = (
            boxart_back_folder if os.path.isdir(boxart_back_folder) else None
        )
        self.boxart_back_snap = (
            FolderSnaps(
                snaps_folder=self.boxart_back_folder,
                relative_path=rom_folder,
            )
            if self.boxart_back_folder is not None
            else None
        )

        # Boxart Front
        boxart_front_folder = f"{root_folder}box_front/"
        self.boxart_front_folder = (
            boxart_front_folder if os.path.isdir(boxart_front_folder) else None
        )
        self.boxart_front_snap = (
            FolderSnaps(
                snaps_folder=self.boxart_front_folder,
                relative_path=rom_folder,
            )
            if self.boxart_front_folder is not None
            else None
        )

        # Boxart Full
        boxart_full_folder = f"{root_folder}box_full/"
        self.boxart_full_folder = (
            boxart_full_folder if os.path.isdir(boxart_full_folder) else None
        )
        self.boxart_full_snap = (
            FolderSnaps(snaps_folder=self.boxart_full_folder, relative_path=rom_folder)
            if self.boxart_full_folder is not None
            else None
        )

        # Boxart Splines
        boxart_spine_folder = f"{root_folder}box_spline/"
        self.boxart_spine_folder = (
            boxart_spine_folder if os.path.isdir(boxart_spine_folder) else None
        )
        self.boxart_spine_snap = (
            FolderSnaps(
                snaps_folder=self.boxart_spine_folder,
                relative_path=rom_folder,
            )
            if self.boxart_spine_folder is not None
            else None
        )

        # Cart Labels
        cart_labels_folder = f"{root_folder}cart_label/"
        self.cart_labels_folder = (
            cart_labels_folder if os.path.isdir(cart_labels_folder) else None
        )
        self.cart_labels_snap = (
            FolderSnaps(
                snaps_folder=self.cart_labels_folder,
                relative_path=rom_folder,
            )
            if self.cart_labels_folder is not None
            else None
        )

        # Carts
        carts_folder = f"{root_folder}cart/"
        self.carts_folder = carts_folder if os.path.isdir(carts_folder) else None
        self.carts_snap = (
            FolderSnaps(
                snaps_folder=self.carts_folder,
                relative_path=rom_folder,
            )
            if self.carts_folder is not None
            else None
        )

        # Logos
        logos_folder = f"{root_folder}logo/"
        self.logos_folder = logos_folder if os.path.isdir(logos_folder) else None
        self.logos_snap = (
            FolderSnaps(
                snaps_folder=self.logos_folder,
                relative_path=rom_folder,
            )
            if self.logos_folder is not None
            else None
        )

        # Music
        music_folder = f"{root_folder}music/"
        self.music_folder = music_folder if os.path.isdir(music_folder) else None
        self.music_snap = (
            FolderSnaps(
                snaps_folder=self.music_folder,
                relative_path=rom_folder,
            )
            if self.music_folder is not None
            else None
        )

        # Screenshots
        screenshots_folder = f"{root_folder}screenshot/"
        self.screenshots_folder = (
            screenshots_folder if os.path.isdir(screenshots_folder) else None
        )
        self.screenshots_snap = (
            FolderSnaps(
                snaps_folder=self.screenshots_folder,
                relative_path=rom_folder,
            )
            if self.screenshots_folder is not None
            else None
        )

        # Titlescreens
        titlescreen_folder = f"{root_folder}titlescreen/"
        self.titlescreen_folder = (
            titlescreen_folder if os.path.isdir(titlescreen_folder) else None
        )
        self.titlescreen_snap = (
            FolderSnaps(
                snaps_folder=self.titlescreen_folder,
                relative_path=rom_folder,
            )
            if self.titlescreen_folder is not None
            else None
        )

        # Videos
        videos_folder = f"{root_folder}video/"
        self.videos_folder = videos_folder if os.path.isdir(videos_folder) else None
        self.videos_snap = (
            FolderSnaps(
                snaps_folder=self.videos_folder,
                relative_path=rom_folder,
            )
            if self.videos_folder is not None
            else None
        )

        return

    def get_assets_from_game_name(self, game_name):
        filename_links = {}
        for k, f, s in [
            ("boxart_back", self.boxart_back_folder, self.boxart_back_snap),
            ("boxart_front", self.boxart_front_folder, self.boxart_front_snap),
            ("boxart_full", self.boxart_full_folder, self.boxart_full_snap),
            ("boxart_spine", self.boxart_spine_folder, self.boxart_spine_snap),
            ("cart", self.carts_folder, self.carts_snap),
            ("cart_label", self.cart_labels_folder, self.cart_labels_snap),
            ("clearlogo", self.logos_folder, self.logos_snap),
            ("music", self.music_folder, self.music_snap),
            ("fanart", self.backgrounds_folder, self.backgrounds_snap),
            ("screenshot", self.screenshots_folder, self.screenshots_snap),
            ("titlescreen", self.titlescreen_folder, self.titlescreen_snap),
            ("video", self.videos_folder, self.videos_snap),
        ]:
            curr_snap = []
            if f is not None:
                snap = s.get_full_filename_path_from_game_name(game_name)
                if snap is not None:
                    curr_snap.append(snap)
                    filename_links[k] = curr_snap

        return filename_links
