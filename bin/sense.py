import sys
import pathlib
import importlib
import inspect
import json
import os
from datetime import datetime as dt
from time import sleep
from pykson import *


class Settings(JsonObject):
    root = StringField()
    sensors = StringField()
    period = IntegerField()
    log = BooleanField()
    logDir = StringField()
    datDir = StringField()


class Quantity:

    def __init__(self, name, unit):
        self.qname = name
        self.qunit = unit

    @property
    def name(self) -> str:
        return self.qname

    @property
    def unit(self) -> str:
        return self.qunit


class Application:
    def mkpaths(self):
        self.log("Creating directories")
        self.root.mkdir(parents=True, exist_ok=True)
        self.logDir.mkdir(parents=True, exist_ok=True)
        self.dataDir.mkdir(parents=True, exist_ok=True)
        #self.root.joinpath("sensors").mkdir(parents=True, exist_ok=True)
        #self.root.joinpath("quantities").mkdir(parents=True, exist_ok=True)

    def log(self, msg):
        if self.logB: 
            txt = "[{0}] {1}\n".format(dt.now().strftime("%H:%M:%S"), msg)
            self.logFile.write(txt)
            print(txt)
            
    def get_default_settings(self):
        root = pathlib.Path.home().joinpath(".config/sense")
        return {
            "root": str(root),
            "sensors": str(root.joinpath("modules")),
            "period": 1000, # milliseconds
            "log": True,
            "logDir": "logs"
        }

    def load_settings(self, path):
        with open(path, "r") as file:
            return json.load(file)

    def validate(self):
        self.log("Validating sensors")
        to_remove = list()
        for sensor in self.sensors_list:
            found = 0
            for member in inspect.getmembers(sensor):
                if member[0] in ["name", "quantities", "read"]:
                    found += 1

            if found < 3:
                print("Invalid sensor: '" + sensor.__name__.split(".")[1] + "'", file=sys.stderr)
                to_remove.append(sensor)
        
        self.log("Invalid sensors: " + str(to_remove))
        for invalid in to_remove:
            self.sensors_list.remove(invalid)

    def load_sensors(self):
        self.log("Loading sensors")
        mod_file = self.sources.joinpath("__init__.py")

        if not self.sources.is_dir():
            self.log("IOError: Not a directory: '{0}'".format(self.sources))
            raise IOError("Not a directory: '{0}'".format(self.sources))

        if not mod_file.is_file():
            mod_file.touch()

        sys.path.append(str(self.sources.parent))
        for file in self.sources.iterdir():
            if not (file.name == "__init__.py") and file.suffix == ".py":
                name = file.name.replace(file.suffix, "") 
                self.sensors_list.append(importlib.import_module("." + name, package=self.sources.name))

                self.log("Initializing sensor: '{0}'".format(name)) 
                try:
                    self.sensors_list[-1].initialize(self.root)
                except Exception as e:
                    self.log("Initialization failed: {0}".format(e))
                    self.log("Removing sensor '{0}'".format(name))
                    self.sensors_list.remove(self.sensors_list[-1])
                
        self.validate()

    def __init__(self, args):
        if len(args) > 1:
            settings = self.load_settings(args[1])
        else:
            settings = self.get_default_settings()

        self.root = pathlib.Path(settings["root"])
        global root
        root = self.root
        self.sources = self.root.joinpath(settings["sensors"])
        self.period = settings["period"]
        self.logB = settings["log"]
        self.logDir = self.root.joinpath(settings["logDir"])
        self.logFile = open(str(self.logDir.joinpath("sense.log")), "w")
        self.dataDir = self.root.joinpath(settings["dataDir"])

        self.log("Settings loaded")
        self.sensors_list = list()
        self.mkpaths()
        self.load_sensors()

    def get_sensor_data(self, sensor):
        readings = list()
        self.log("Reading sensor: '{0}'".format(sensor.name))

        for quantity in sensor.quantities:
            self.log("Reading quantity '{0}'".format(quantity.name))
            try:
                val = sensor.read(quantity)
                print("\t", quantity.name, "->", val)
                reading = {"name": quantity.name, "unit": quantity.unit, "sensor": sensor.name,
                       "value": val}

                readings.append(reading)
            except Exception as e:
                self.log("Reading error: {0}".format(e))
                self.log("Removing sensor '{0}'".format(sensor.name))
                self.sensors_list.remove(sensor)
                break

        return {"name": sensor.name, "quantities": readings}

    def run(self):
        while True:
            sensors_file = self.dataDir.joinpath("sensors.json")

            quantities = list()
            if len(self.sensors_list) == 0:
                self.log("No sensors")
            else:
                for sensor in self.sensors_list:
                    data = self.get_sensor_data(sensor)
    
                    for q in data["quantities"]:
                        quantities.append(q)
 
                self.log("Writing data")
                with open(sensors_file, "w") as f:
                    f.write(json.dumps(quantities, indent=4))

            sleep(self.period)


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    # execute only if run as a script
    Application(sys.argv).run()
