from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import threading
import time
import os
import hashlib
import random
import string


class FileDistributor:
    def __init__(self, root, prefix):
        self.__root = root
        self.__prefix = prefix
        self.__handler = FileDistributorFileSystemHandler(self.__onFileSystemModified)
        self.__observer = Observer()
        self.__observer.schedule(self.__handler, root, recursive=True)
        self.__observer.start()
        self.__needUpdate = True
        self.__meta = {}
        self.__random = random.Random()
        self.__excluded = {'__pycache__', '.DS_Store', '.idea'}
        self.__fileMedaUpdateLoopThread = threading.Thread(target=self.__fileMedaUpdateLoop, daemon=True)
        self.__fileMedaUpdateLoopThread.start()

    def __onFileSystemModified(self, event):
        self.__needUpdate = True

    def __fileMedaUpdateLoop(self):
        while True:
            if self.__needUpdate:
                self.__needUpdate = False
                self.__meta = self.__updateFileMeta('')
            time.sleep(1)

    def getFilesVersion(self):
        return self.__meta['__version__']

    def getFilesMeta(self):
        return self.__meta

    def __updateFileMeta(self, path):
        meta = {}
        files = [path + '/' + f for f in os.listdir(self.__root + '/' + path)
                 if not self.__excluded.__contains__(f)]
        for file in files:
            if os.path.isfile(self.__root + file):
                input = open(self.__root + file, 'rb')
                fileSize = os.path.getsize(self.__root + file)
                content = input.read(fileSize)
                fmd5 = hashlib.md5(content)
                fullPath = file
                meta[fullPath] = [fileSize, fmd5.hexdigest()]
                input.close()
            if os.path.isdir(self.__root + file):
                meta.update(self.__updateFileMeta(file))
        timeStamp = time.strftime("%Y%m%d_%H%M%S_", time.localtime(time.time()))
        meta['__version__'] = timeStamp + ''.join(random.sample(string.ascii_letters + string.digits, 8))
        meta['__prefix__'] = self.__prefix
        return meta


class FileDistributorFileSystemHandler(FileSystemEventHandler):
    def __init__(self, onModified):
        self.onModified = onModified

    def on_modified(self, event):
        self.onModified(event)


if __name__ == '__main__':
    print('File Distributor')
    fd = FileDistributor('target', 'prefix')

    while True:
        time.sleep(1)
