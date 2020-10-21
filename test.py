import socket
import ssl
import json
import time
import select
import sys
import struct
import logging
import configparser
import os
import random

t=b'{"ans": "init","msg":"ok"}'

u=json.loads(t.decode("UTF-8"))
n_box=6
number_car=str(int(random.random()*100))
message={"number_car":number_car,"n_box":n_box}
message=json.dumps(message)
print(type(message))

import configparser
import os
