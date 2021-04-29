from datetime import datetime
from time import sleep
import os


class Config:
    def __init__(self, comment, delimiter, validKeys):
        self.comment = comment
        self.delimiter = delimiter
        self.validKeys = validKeys

        self.foundKeys = list()
        self.data = {}

    def add(self, key, value):
        if key not in self.validKeys:
            raise Exception("'{}' is not valid key".format(key))

        tmp = 0
        try:
            tmp = int(value)
        except ValueError:
            try:
                tmp = float(value)
            except ValueError:
                tmp = value

        self.data[key] = tmp
        self.foundKeys.append(key)

    def load(self, filePath):
        with open(filePath, "r") as file:
            line = file.readline().strip()
            while line != "":
                if line != "" or line[0] != self.comment:
                    pair = line.split(self.delimiter)
                    key = pair[0].strip()
                    value = pair[1].strip()

                    self.add(key, value)
                line = file.readline().strip()

        if len(self.foundKeys) != len(self.validKeys):
            missing = [key for key in self.validKeys if key not in self.foundKeys]
            raise Exception("Missing key/s: " + " ".join(missing))

    def get(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None
