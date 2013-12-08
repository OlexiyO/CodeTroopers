from collections import namedtuple
import tempfile
import random
import global_vars
import util
from utilities import server_util, create_config

print 'Running my strategy vs Version 7 multiple times.'

global_vars.STDOUT_LOGGING = False

CombatResult = namedtuple('CombatResult', ['place', 'index', 'seed'])

def RunManyCombats(base_port, N, map_name=None, first_moves_random='0', team_size=4):
  results = []
  player_count = util.PlayerCountFromTeamSize(team_size)
  for n in range(N):
    output_filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
    my_player_index = random.randint(0, player_count - 1)
    config_file = create_config.CreateConfigFile(render='false', map_name=map_name, output_filepath=output_filepath,
                                                 seed='0000000000000000', base_port=base_port, team_size=team_size)
    import time
    time.sleep(.05)
    place, seed = server_util.RunOneCombat(config_file, output_filepath, base_port, '0000000000000000', my_player_index,
                                           with_debug=False, first_moves_random=first_moves_random,
                                           player_count=player_count)
    results.append(CombatResult(place, n, seed))

  for r in sorted(results):
    print r

  for n in range(1, player_count + 1):
    print '%d place: %d times' % (n, len([res for res in results if res.place == n]))
  PTS = [0, 8, 4, 2, 1] if player_count == 4 else [0, 2, 0]
  pts_total = sum(PTS[res.place] for res in results)
  print 'Points scored: %d (av = %.1f)' % (pts_total, (sum(PTS) * N) / float(player_count))
  print 'Average result for map', map_name, ':', sum(res.place for res in results) / float(N)


import sys
print sys.argv
if len(sys.argv) == 1:
  # Single validation.
  RunManyCombats(33333, 10, map_name='fefer', first_moves_random='2', team_size=5)
else:
  # For validate_both
  assert len(sys.argv) == 6
  base_port = int(sys.argv[1])
  map_name = sys.argv[2]
  num_combats = int(sys.argv[3])
  first_moves_random = sys.argv[4]
  team_size = int(sys.argv[5])
  RunManyCombats(base_port, num_combats, map_name=map_name, first_moves_random=first_moves_random,
                 team_size=team_size)
