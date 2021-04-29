from config import Config

from adafruit_bmp280 import *
from busio import I2C
from board import SCL, SDA

from sys import argv, exit
from time import sleep

from sense import Quantity

quantities = [
        Quantity("pressure", "Pa"),
        Quantity("temperature", "°C")
    ]


name = "BMP280"
global root

def get_mode(str):
    if str == "sleep":
        return MODE_SLEEP
    elif str == "normal":
        return MODE_NORMAL
    elif str == "force":
        return MODE_FORCE
    else:
        raise Exception("Unknown mode: '{}'".format(str))


def get_iir(val):
    if val == "disable":
        return IIR_FILTER_DISABLE
    elif val == 2:
        return IIR_FILTER_X2
    elif val == 4:
        return IIR_FILTER_X4
    elif val == 8:
        return IIR_FILTER_X8
    elif val == 16:
        return IIR_FILTER_X16
    else:
         raise Exception("Unknown IIR: '{}'".format(val))


def get_os(val):
    if val == "disable":
        return OVERSCAN_DISABLE
    elif val == 1:
        return OVERSCAN_X1
    elif val == 2:
        return OVERSCAN_X2
    elif val == 4:
        return OVERSCAN_X4
    elif val == 8:
        return OVERSCAN_X8
    elif val == 16:
        return OVERSCAN_X16
    else:
         raise Exception("Unknown overscan: '{}'".format(val))


def get_sp(p):
    if p == 0.5:
        return STANDBY_TC_0_5
    elif p == 10:
        return STANDBY_TC_10
    elif p == 20:
        return STANDBY_TC_20
    elif p == 62.5:
        return STANDBY_TC_62_5
    elif p == 125:
        return STANDBY_TC_125
    elif p == 250:
        return STANDBY_TC_500
    elif p == 500:
        return STANDBY_TC_500
    elif p == 1000:
        return STANDBY_TC_1000
    else:
        raise Exception("Unknown standby period: '{}'".format(p))


global sensor
def initialize(root):
    config_keys = ["address", "mode", "iir", "osp", "ost", "sp"]
    config = Config("#", "=", config_keys)
    config.load(str(root.joinpath("config/bmp")))

    global sensor
    i2c = I2C(SCL, SDA)
    sensor = Adafruit_BMP280_I2C(i2c, address=config.get("address"))
    sensor.mode = get_mode(config.get("mode"))
    sensor.iir_filter = get_iir(config.get("iir"))
    sensor.overscan_pressure = get_os(config.get("osp"))
    sensor.overscan_temperature = get_os(config.get("ost"))
    sensor.standby_period = get_sp(config.get("sp"))

def read(q):
    if q == quantities[0]:
        return sensor.pressure
    if q == quantities[1]:
        return sensor.temperature
