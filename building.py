

class Building:
    def __init__(self, data):
        self.__data = data

    def var(self):
        return "building:" + self.__data["slug"]

    def human_readable_name(self):
        return self.__data["name"]