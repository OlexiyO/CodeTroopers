from collections import namedtuple
import tempfile
import random
import MyStrategy
from utilities import server_util

print 'Running my strategy vs Version 7 multiple times.'

MyStrategy.STDOUT_LOGGING = False

CombatResult = namedtuple('CombatResult', ['place', 'index', 'seed'])

def RunManyCombats(base_port, N, map_name=None):
  results = []
  for n in range(N):
    filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
    my_index = random.randint(0, 3)
    place, seed = server_util.RunOneCombat(map_name, filepath, my_index, base_port, None, False)
    results.append(CombatResult(place, n, seed))
  for r in sorted(results):
    print r

  for n in range(1, 5):
    print '%d place: %d times' % (n, len([res for res in results if res.place == n]))
  print 'Average result for map ', map_name, ':', sum(res.place for res in results) / float(N)


import sys
print sys.argv
if len(sys.argv) >= 2:
  base_port = int(sys.argv[1])
else:
  base_port = 31000

if len(sys.argv) <= 2:
  RunManyCombats(base_port, 5, None)
elif len(sys.argv) > 2:
  # For validate_both
  RunManyCombats(base_port, 20, sys.argv[2])
