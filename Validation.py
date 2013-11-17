from collections import namedtuple
import tempfile
import threading
import random
import time
from subprocess import call
import MyStrategy

print 'Running my strategy vs Version 7 multiple times.'
PORT = 31000

MyStrategy.STDOUT_LOGGING = False

def RunServer(map_name, my_player_index, output_file):
  base_cmd = 'start java -cp .;local-runner.jar Run %(flags)s "#LocalTestPlayer" "#LocalTestPlayer" "#LocalTestPlayer" "#LocalTestPlayer"'
  flags_dict = {
    'move-count': 50,
    #'render-to-screen': 'true', 'render-to-screen-scale': 1.0, 'render-to-screen-sync': 'true',
    'debug': 'true', 'base-adapter-port': PORT,
    'p1-name': 'v7_P1', 'p2-name': 'v7_p2', 'p3-name': 'v7_p3', 'p4-name': 'v7_p4',
    'p1-team-size': 3, 'p2-team-size': 3, 'p3-team-size': 3, 'p4-team-size': 3,
    'results-file': output_file}
  if map_name is not None and map_name != 'default':
    flags_dict['map'] = '%s.map' % map_name
  key = 'p%d-name' % (my_player_index + 1)
  assert key in flags_dict, key
  flags_dict[key] = 'Latest'
  printed_flags = ' '.join('-%s=%s' % tup for tup in flags_dict.iteritems())
  full_cmd = base_cmd % {'flags': printed_flags}
  call(full_cmd, shell=True, cwd='C:/Coding/CodeTroopers/Combat')


def RunOldPlayer(index):
  D = 'C:/Coding/CodeTroopers/v7/'
  STRATEGY = 'C:/Coding/CodeTroopers/v7/RunPlayer.py'
  call(['python', STRATEGY, 'localhost', str(PORT + index), '0000000000000000'], shell=True, cwd=D)


def RunLatestPlayer(index):
  D = 'C:/Coding/CodeTroopers/src/'
  STRATEGY = 'C:/Coding/CodeTroopers/src/RunPlayer.py'
  call(['python', STRATEGY, 'localhost', str(PORT + index), '0000000000000000'], shell=True, cwd=D)


CombatResult = namedtuple('CombatResult', ['place', 'index', 'seed'])


def RunOneCombat(map):
  my_index = random.randint(0, 3)
  filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
  tserver = threading.Thread(target=RunServer, args=(map, my_index, filepath))
  tserver.start()
  time.sleep(1.)
  threads = [tserver]
  for n in range(4):
    tgt = RunLatestPlayer if n == my_index else RunOldPlayer
    tp = threading.Thread(target=tgt, args=(n,))
    tp.start()
    threads.append(tp)
    time.sleep(.2)
  for t in threads:
    t.join()

  with open(filepath) as fin:
    lines = [line.strip() for line in fin]
  assert lines[0] == 'OK'
  seed = lines[1][5:]
  for line in lines:
    assert 'crashed' not in line.lower()
  place = int(lines[2 + my_index][0])
  return place, seed


def RunManyCombats(N, map_name=None):
  results = []
  for n in range(N):
    place, seed = RunOneCombat(map_name)
    results.append(CombatResult(place, n, seed))
  for r in sorted(results):
    print r

  for n in range(1, 5):
    print '%d place: %d times' % (n, len([res for res in results if res.place == n]))
  print 'Average result:', sum(res.place for res in results) / float(N)


import sys
print sys.argv
if len(sys.argv) >= 2:
  PORT = int(sys.argv[1])

if len(sys.argv) <= 2:
  RunManyCombats(5, None)
elif len(sys.argv) > 2:
  RunManyCombats(20, sys.argv[2])
