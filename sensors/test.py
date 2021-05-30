from config import Config

from sense import Quantity

quantities = [
        Quantity("test_quantity", "U"),
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
