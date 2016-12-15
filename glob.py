# glob.py
# Moves photos and videos from scattered places into a single directory tree
# organized by year and month like:
#
# /2016/01 - Jan
# /2016/02 - Feb
#
# Syntax: glob [--skip-mismatched-dates] <source directory name> <target directory name>
#
# Fixes conflicting file names
# Can skip files where EXIF date time does not match file creation date time
# TODO: Handle duplicates

import os
import errno
import shutil
import datetime
import platform
from PIL import Image
from PIL.ExifTags import TAGS

class MediaFile:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.creation_time = self.__get_creation_time(self.file_name)
        self.exif_data = self.__load_exif(self.file_name)
        if self.exif_data:
            self.exif_creation_time = self.exif_data['DateTimeOriginal']
            self.exif_device_model = self.exif_data['Model']
        
    def is_valid(self) -> bool:
        return True if self.creation_time else False

    def is_image(self) -> bool:
        return True if self.exif_data else False

    def debugit(self):
        if self.is_image():
            print(self.file_name, "|", self.exif_creation_time, "|", self.exif_device_model)
        else:
            print(self.file_name, "(not an image)")

    def get_target_directory() -> str:
        if self.creation_time:
            ts = datetime.datetime.fromtimestamp(self.creation_time)
            tp = os.path.join("glob", "%Y", "%m")
            tf = datetime.datetime.strftime(ts, tp)
            return tf
        return "" 

    # http://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
    def __get_creation_time(self, path_to_file: str):
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            try:
                stat = os.stat(path_to_file)
                self.is_valid = True
                try:
                    return stat.st_birthtime
                except AttributeError:
                     # We're probably on Linux. No easy way to get creation dates here,
                     # so we'll settle for when its content was last modified.
                     return stat.st_mtime
            except FileNotFoundError:
                self.is_valid = False
                pass
        return 0

    def __load_exif(self, file_name: str):
        ret = {}
        try:
            image = Image.open(file_name)
        except IOError:
            return ret

        info = image._getexif()
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            # HACK/Optimization: Our app only needs a handful of the EXIF metadata types
            # if decoded not in ('UserComment', 'MakerNote', 'CameraOwnerName', 'LensModel'):
            if decoded in ('DateTimeOriginal', 'Model'):
                ret[decoded] = value
        return ret

class Target:
    def __init__(self):
        self.directories = set()

    def mkdir_p(self, path: str) -> None:
        if path not in self.directories:
           try:
               os.makedirs(path, 0o777, True)
               self.directories.add(path)
           except OSError as ex:
               if ex.errno == errno.EEXIST and os.path.isdir(path):
                   pass
               else:
                   raise

    def mkdir_for_media_file(self, media_file: MediaFile) -> str:
        td = media_file.get_target_directory()
        if td:
            self.mkdir_p(td)
            print(self.directories)
            return td

    def move_media_file_to_new_home(self, media_file: MediaFile) -> bool:
        media_file.debugit()
        return True
        home = self.mkdir_for_file(media_file.file_name)
        if home:
            shutil.move(media_file.file_name, home)

    def move_files_to_new_homes(self, path: str) -> None:
        for root, subdirs, files in os.walk(path):
            for base_file_name in files:
                full_file_name = os.path.join(root, base_file_name)
                media_file = MediaFile(full_file_name)
                if not self.move_media_file_to_new_home(media_file):
                    if media_file.is_valid():
                        self.__warn("Failed to move file:", full_file_name)
                    else:
                        self.__warn("Skipped missing file:", full_file_name)

    def __warn(self, message: str, *args):
        print("Warning:", message, *args)

# MAIN ---------------------------------------
target = Target()
target.move_files_to_new_homes("test")
print("Done")

