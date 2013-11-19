

from subprocess import call
from BaseRunner import Runner
import search
import util
from utilities import server_util

SHARED_ID = '0000000000000000'
#SHARED_ID = '2516990789178515'


server_util.RunOneCombat('map1', 'C:/Coding/CodeTroopers/Combat/result.txt', 2, 31000, SHARED_ID, render=True,
                         with_debug=True, first_moves_random='4')