import sys
import global_vars

print 'Latest version'
from utilities.BaseRunner import Runner

assert len(sys.argv) == 3
global_vars.FIRST_MOVES_RANDOM = int(sys.argv[2])
Runner(sys.argv[1]).run()