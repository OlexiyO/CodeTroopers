from collections import namedtuple
import tempfile
import random
import global_vars
from utilities import server_util, create_config

print 'Running my strategy vs Version 7 multiple times.'

global_vars.STDOUT_LOGGING = False

CombatResult = namedtuple('CombatResult', ['place', 'index', 'seed'])

def RunManyCombats(base_port, N, map_name=None, first_moves_random='0'):
  results = []
  for n in range(N):
    output_filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
    my_player_index = random.randint(0, 3)
    config_file = create_config.CreateConfigFile(render='false', map_name=map_name, output_filepath=output_filepath,
                                                 seed='0000000000000000', base_port=base_port)
    import time
    time.sleep(.05)
    place, seed = server_util.RunOneCombat(config_file, output_filepath, base_port, '0000000000000000', my_player_index,
                                           with_debug=False, first_moves_random=first_moves_random)
    results.append(CombatResult(place, n, seed))
  for r in sorted(results):
    print r

  for n in range(1, 5):
    print '%d place: %d times' % (n, len([res for res in results if res.place == n]))
  PTS = [0, 8, 4, 2, 1]
  pts_total = sum(PTS[res.place] for res in results)
  print 'Points scored: %d (av = %.1f)' % (pts_total, (15 * N) / 4.)
  print 'Average result for map', map_name, ':', sum(res.place for res in results) / float(N)


import sys
print sys.argv
if len(sys.argv) == 1:
  # Single validation.
  RunManyCombats(33333, 2, map_name='map03', first_moves_random='0')
else:
  # For validate_both
  assert len(sys.argv) == 5
  base_port = int(sys.argv[1])
  map_name = sys.argv[2]
  num_combats = int(sys.argv[3])
  RunManyCombats(base_port, num_combats, map_name=map_name, first_moves_random=sys.argv[4])
