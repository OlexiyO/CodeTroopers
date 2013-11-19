from collections import namedtuple
import tempfile
import random
import MyStrategy
import global_vars
from utilities import server_util

print 'Running my strategy vs Version 7 multiple times.'

MyStrategy.STDOUT_LOGGING = False

CombatResult = namedtuple('CombatResult', ['place', 'index', 'seed'])

def RunManyCombats(base_port, N, map_name=None, first_moves_random='0'):
  results = []
  for n in range(N):
    filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
    my_index = random.randint(0, 3)
    place, seed = server_util.RunOneCombat(map_name, filepath, my_index, base_port, None, render=False, with_debug=False,
                                           first_moves_random=first_moves_random)
    results.append(CombatResult(place, n, seed))
  for r in sorted(results):
    print r

  for n in range(1, 5):
    print '%d place: %d times' % (n, len([res for res in results if res.place == n]))
  print 'Average result for map', map_name, ':', sum(res.place for res in results) / float(N)


import sys
print sys.argv
if len(sys.argv) == 1:
  # Single validation.
  RunManyCombats(31000, 5, map_name='default', first_moves_random='0')
else:
  # For validate_both
  assert len(sys.argv) == 5
  base_port = int(sys.argv[1])
  map_name = sys.argv[2]
  num_combats = int(sys.argv[3])
  RunManyCombats(base_port, num_combats, map_name=map_name, first_moves_random=sys.argv[4])
