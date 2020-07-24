from IFWorker import IFWorker
import os
import threading
import time
import hashlib
import requests


class IFLocalLauncher:
    def __init__(self, brokerEndpoint, name, localPath, httpPrefix):
        self.__localPath = localPath
        self.__httpPrefix = httpPrefix
        if not os.path.exists(self.__localPath): os.mkdir(self.__localPath)
        self.__fileVersion = ''
        self.__excluded = {'__pycache__', '.DS_Store', '.idea'}
        self.__updateStatus = 'UP TO DATE'
        self.__worker = IFWorker(brokerEndpoint, serviceName=name, serviceObject=self, interfaces=['IFLocalLauncher'])
        threading.Thread(target=self.__checkFileUpdateLoop, name='CheckFileUpdateLoop').start()
        self.__updateOnNextLoop = False

    def __checkFileUpdateLoop(self):
        while True:
            try:
                version = self.__worker.IFLocalFileMeta.getFilesVersion()
                if version != self.__fileVersion:
                    self.__updateStatus = 'NEED UPDATE'
                    if self.__updateOnNextLoop:
                        self.__updateOnNextLoop = False
                        self.__updateStatus = 'UPDATING'
                        self.__doUpdate()
                        self.__updateStatus = 'UP TP DATE'
            except BaseException as e:
                print(e)
            time.sleep(1)

    def needUpdate(self):
        return self.__updateStatus == 'NEED UPDATE'

    def isUpdating(self):
        return self.__updateStatus == 'UPDATING'

    def getFileVersion(self):
        return self.__fileVersion

    def updateASAP(self):
        self.__updateOnNextLoop = True

    def __doUpdate(self):
        print('update')
        meta = self.__worker.IFLocalFileMeta.getFilesMeta()
        self.__fileVersion = meta.pop('__version__')
        prefix = meta.pop('__prefix__')
        localFiles = self.__updateFileMeta('')
        tobeDownloaded = []
        for localFile in localFiles:
            if meta.__contains__(localFile):
                detail = meta.pop(localFile)
                if localFiles[localFile] == detail:
                    pass
                else:
                    tobeDownloaded.append(localFile)
            else:
                os.remove(self.__localPath + localFile)
        for remoteFile in meta:
            tobeDownloaded.append(remoteFile)
        for remoteFile in tobeDownloaded:
            localPath = self.__localPath + remoteFile
            localDir = localPath[:localPath.rindex('/')]
            if not os.path.exists(localDir):
                os.makedirs(localDir)
            r = requests.get(self.__httpPrefix + prefix + remoteFile)
            with open(self.__localPath + remoteFile, "wb") as code:
                code.write(r.content)

    def __updateFileMeta(self, path):
        meta = {}
        files = [path + '/' + f for f in os.listdir(self.__localPath + '/' + path)
                 if not self.__excluded.__contains__(f)]
        for file in files:
            if os.path.isfile(self.__localPath + file):
                input = open(self.__localPath + file, 'rb')
                fileSize = os.path.getsize(self.__localPath + file)
                content = input.read(fileSize)
                fmd5 = hashlib.md5(content)
                meta[file] = [fileSize, fmd5.hexdigest()]
                input.close()
            if os.path.isdir(self.__localPath + file):
                meta.update(self.__updateFileMeta(file))
        return meta


if __name__ == '__main__':
    ifll = IFLocalLauncher('tcp://172.16.60.199:224', 'testIFLL', '.IFLocal', 'http://172.16.60.199')
    ifll.updateASAP()
    # print(worker.IFLocalFileMeta.getFilesVersion())
    # print(worker.IFLocalFileMeta.getFilesMeta())
