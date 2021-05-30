import sys
import pathlib
import importlib
import inspect
import json
import os
from datetime import datetime as dt
from time import sleep
from pykson import *
import mqttools
import asyncio


class Settings(JsonObject):
    root = StringField()
    sensors = StringField()
    period = IntegerField()
    log = BooleanField()
    logDir = StringField()
    datDir = StringField()
    mqtt= StringField()


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
            "logDir": "logs",
            "mqtt": "localhost:1111"
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
                    self.remove_sensor(self.sensors_list[-1], False)
                
        self.validate()

    def to_bytes(self, o):
        return bytes(str(o).replace("'", '"'), "utf-8")

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

        tmp = settings["mqtt"].split(":")
        self.mqttIP = tmp[0]
        self.mqttPort = int(tmp[1])

        self.log("Settings loaded")
        self.sensors_list = list()
        self.mkpaths()
        self.load_sensors()

    def remove_sensor(self, sensor, publish):
        self.log("Removing sensor '{0}'".format(sensor.name))
        self.sensors_list.remove(sensor)
        if publish:
            self.publish_sensors_list()

    def publish_sensors_list(self):
        names = list(map(lambda s: s.name, self.sensors_list))
        self.client.publish("/meteo/sensors/list", self.to_bytes(names)) 
        
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
                self.remove_sensor(sensor, True)
                break
                

        return {"name": sensor.name, "quantities": readings}

    async def run(self):
        self.log("Starting MQTT publisher")
        self.client = mqttools.Client(self.mqttIP, self.mqttPort)
        try:
            await self.client.start()
        except Exception as e:
            self.log("Cannot start MQTT: '{0}'".format(e))
            exit(1)
        self.log("MQTT OK")
        self.publish_sensors_list()
        while True: 
            sensors_file = self.dataDir.joinpath("sensors.json")

            quantities = list()
            if len(self.sensors_list) == 0:
                self.log("No sensors")
            else:
                for sensor in self.sensors_list:  
                    data = self.get_sensor_data(sensor)
                    self.client.publish("/meteo/sensors/{0}".format(sensor.name), self.to_bytes(data)) 
    
                    for q in data["quantities"]:
                        quantities.append(q)
 
                self.log("Writing data")
                out = json.dumps(quantities, indent=4)
                with open(sensors_file, "w") as f:
                    f.write(out)

                self.client.publish("/meteo/quantities", self.to_bytes(out))

            sleep(self.period)


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    # execute only if run as a script
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Application(sys.argv).run())
