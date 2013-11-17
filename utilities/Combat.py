

from subprocess import call
from BaseRunner import Runner
from utilities import server_util

# SHARED_ID = None #'0000000000000000'
SHARED_ID = '2514997565372659'


server_util.RunOneCombat(None, 'C:/Coding/CodeTroopers/Combat/result.txt', 2, 31000, SHARED_ID, True)