from config import Config

from sys import argv, exit
from os import path
from time import sleep

from sense import Quantity

quantities = [
        Quantity("test_quantity1", "U"),
        ]

name = "TestSensor"

global value  
value = 0
def initialize(root):
   pass 
def read(q):
    global value
    v = value
    value += 1
    return v
