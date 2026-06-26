'''
Some text about the pyrpa module and the license
'''

# import third party dependencies

import sys
import os.path
import pandas as pd
import warnings
import numpy as np
import matplotlib.pyplot as plt

# import pyrpa modules

import pyrpa.blockmodel as blk
import pyrpa.sample as smp
import pyrpa.validation as valid
import pyrpa.eda
from pyrpa.capping import capping as capping
import pyrpa.io as io
from pyrpa.read_bef import read_bef as read_bef
import pyrpa.changeofsupport as gcos
import pyrpa.contact_plot as contact_plot
import pyrpa.rotation as rotation

# from . import capping
# from . import utils
# from . import plotting
