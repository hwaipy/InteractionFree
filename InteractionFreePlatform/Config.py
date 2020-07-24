import configparser


class Config:
    def __init__(self, path):
        self.__path = path
        self.__config = configparser.ConfigParser()
        file = open(path)
        self.__config.read_file(file)
        file.close()

    def __getitem__(self, item):
        return ConfigItem(self, item, '')

    def get(self, section, option):
        return self.__config.get(section, option)


class ConfigItem:
    def __init__(self, config, section, option):
        self.__config = config
        self.__section = section
        self.__option = option

    def getOption(self, option):
        if self.__option: return ConfigItem(self.__config, self.__section, self.__path + '.' + option)
        return ConfigItem(self.__config, self.__section, option)

    def __getattr__(self, item):
        return self.getOption(item)

    def asString(self):
        return self.__config.get(self.__section, self.__option)

    def asInt(self):
        return int(self.asString())


Config = Config('Config.ini')

if __name__ == '__main__':
    c = Config('Config.ini')
    # print(c.MongoDB.FEO.r44.asString())
    print(c['MongoDB.IFConfig'].Username.asString())
