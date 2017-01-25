"""

media.py - Media module that supports handling media files

"""

import os
import errno
import shutil
import datetime
import platform
import collections
from PIL import Image
from PIL.ExifTags import TAGS


class MediaFile:
    def __init__(self, file_name: str, run: bool, verbose: bool):
        self.file_name = file_name
        self.run = run
        self.verbose = verbose
        times = self.__get_file_ts(self.file_name)
        self.created_ts = times.created_time if times else 0
        self.modified_ts = times.modified_time if times else 0
        self.exif_data = self.__load_exif(self.file_name)
        self.exif_created_ts = self.__parse_datetime(
            self.exif_data['DateTimeOriginal']) if self.exif_data else 0
        self.exif_model = self.exif_data['Model'] if self.exif_data else ""

    def debugit(self):
        if self.is_hidden():
            if self.verbose:
                print(self.file_name, "|(hidden)|")
        elif self.is_image():
            self.sync_modified_time_with_exif_time(self.file_name)
            print(self.file_name,
                  "AFTER :",
                  self.get_exif_created_time(),
                  "|", self.get_created_time(),
                  "|", self.get_modified_time(),
                  "|", self.exif_model)
        elif self.is_file():
            print(self.file_name, "|(non-image)|", self.get_created_time(),
                  "|", self.get_modified_time())
        else:
            print(self.file_name, "(not a valid file)")

    def is_file(self) -> bool:
        return True if self.created_ts else False

    def is_hidden(self) -> bool:
        return os.path.basename(self.file_name).startswith('.')

    def is_image(self) -> bool:
        return True if self.exif_data else False

    def get_target_directory(self) -> str:
        if self.created_ts:
            ts = datetime.datetime.fromtimestamp(self.created_ts)
            tp = os.path.join("glob", "%Y", "%m")
            tf = datetime.datetime.strftime(ts, tp)
            return tf
        return ""

    def sync_modified_time_with_exif_time(self, file_name: str) -> bool:
        if self.exif_created_ts and self.exif_created_ts != self.created_ts:
            os.utime(file_name, (self.exif_created_ts, self.exif_created_ts))
            return True
        return False

    # http://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
    def __get_file_ts(self, path_to_file: str):
        Times = collections.namedtuple('Times', 'created_time, modified_time')
        if platform.system() == 'Windows':
            ctime = os.path.getctime(path_to_file)
            return Times(ctime, os.path.getmtime(path_to_file))
        else:
            try:
                stat = os.stat(path_to_file)
                try:
                    ctime = stat.st_birthtime
                except AttributeError:
                    # Probably on Linux? No easy way to get creation dates,
                    # so we'll settle for last modified.
                    ctime = stat.st_mtime
                    pass
                return Times(ctime, stat.st_mtime)
            except FileNotFoundError:
                pass
        return None

    def get_created_time(self) -> str:
        return self.__format_ts(self.created_ts)

    def get_modified_time(self) -> str:
        return self.__format_ts(self.modified_ts)

    def get_exif_created_time(self) -> str:
        return self.__format_ts(self.exif_created_ts)

    def __format_ts(self, timestamp: int) -> str:
        ts = datetime.datetime.fromtimestamp(timestamp)
        return datetime.datetime.strftime(ts, "%Y-%m-%d %H:%M:%S")

    def __parse_datetime(self, date_time: str) -> int:
        # EXIF DateTimeOriginal format
        dt = datetime.datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
        return dt.timestamp()

    def __load_exif(self, file_name: str):
        ret = {}
        try:
            image = Image.open(file_name)
        except IOError:
            return ret
        info = image._getexif()
        image.close()
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            # HACK/Optimization: Our app only needs a handful of the EXIF
            # metadata types. Old code gets rid of crazy long types:
            # if decoded not in ('UserComment', 'MakerNote',
            #                    'CameraOwnerName', 'LensModel'):
            if decoded in ('DateTimeOriginal', 'Model'):
                ret[decoded] = value
        return ret


class Target:
    def __init__(self, target_dir: str, run: bool, verbose: bool):
        self.target_dir = target_dir
        self.run = run
        self.verbose = verbose
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

    def move_media_file_to_new_place(self, media_file: MediaFile) -> bool:
        media_file.debugit()
        return True
        home = self.mkdir_for_file(media_file.file_name)
        if home:
            shutil.move(media_file.file_name, home)

    def move_files_to_new_places(self, path: str) -> None:
        for root, subdirs, files in os.walk(path):
            for base_file_name in files:
                full_file_name = os.path.join(root, base_file_name)
                media_file = MediaFile(full_file_name, self.run, self.verbose)
                if not self.move_media_file_to_new_place(media_file):
                    if media_file.is_file():
                        self.__warn("Failed to move file:", full_file_name)
                    else:
                        self.__warn("Skipped missing file:", full_file_name)

    def __warn(self, message: str, *args):
        print("Warning:", message, *args)
