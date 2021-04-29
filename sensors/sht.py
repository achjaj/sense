from config import Config

from pi_sht1x.logging import LOG_FORMAT
from pi_sht1x import SHT1x
from RPi.GPIO import BCM

from sys import argv, exit
from logging import getLogger, Formatter, INFO
from logging.handlers import RotatingFileHandler
from os import path
from time import sleep

from sense import Quantity

quantities = [
        Quantity("temperature", "°C"),
        Quantity("humidity", "%"),
        Quantity("dew_point", "°C")
    ]

name = "SHT10"

global sensor
def initialize(root):
    conf_keys = ["data_pin", "sck_pin", "log"]
    config = Config("#", "=", conf_keys)
    config.load(str(root.joinpath("config/sht")))

    logger = getLogger("sensor.sht.logger")
    log_filename = path.join(config.get("log"), "sht.log")
    log_formatter = Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(log_filename, mode='a', maxBytes=512000, backupCount=3)
    file_handler.setLevel(INFO)
    file_handler.setFormatter(log_formatter)

    del logger.handlers[:]
    logger.addHandler(file_handler)
    logger.setLevel(INFO)


    DATA_PIN = config.get("data_pin")
    SCK_PIN = config.get("sck_pin")
    
    global sensor
    sensor = SHT1x(DATA_PIN, SCK_PIN, gpio_mode=BCM, logger=logger)

def read(q):
    if q == quantities[0]:
        return sensor.read_temperature()
    if q == quantities[1]:
        return sensor.read_humidity()
    if q == quantities[2]:
        return sensor.calculate_dew_point()
