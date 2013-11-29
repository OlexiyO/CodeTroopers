import sys
import global_vars

print 'Latest version'
from utilities.BaseRunner import Runner

assert len(sys.argv) == 4
global_vars.FIRST_MOVES_RANDOM = int(sys.argv[3])
Runner(sys.argv[1], sys.argv[2]).run()