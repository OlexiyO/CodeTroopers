from collections import deque
import os
from subprocess import call
import tempfile
from threading import Thread
import datetime
import util


NUM_GAMES = 4
random_moves = 2
TEAM_SIZE = 5
MAPS_IN_PARALLEL = 3

def DoValidate(port, map_name, output_file):
  global random_moves
  with open(output_file, 'w') as fout:
    call('python Validation.py %d %s %d %d %d' % (port, map_name, NUM_GAMES, random_moves, TEAM_SIZE),
         shell=True,
         cwd='C:/Coding/CodeTroopers/src',
         stdout=fout)

port = 33000
threads = []
data = []
for map_name in ['default', 'map01', 'cheeser', 'map02', 'map03', 'map04', 'map05', 'map06', 'fefer']:
  filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
  print filepath
  t = Thread(target=DoValidate, kwargs={'port': port, 'map_name': map_name, 'output_file': filepath})
  threads.append(t)
  data.append((map_name, filepath))
  port += 100

T = len(threads)
for n in range(0, T, MAPS_IN_PARALLEL):
  tt = threads[n: n + MAPS_IN_PARALLEL]
  for t in tt:
    t.start()
  for t in tt:
    t.join()


def PrintResults():
  yield 'Random moves: %d' % random_moves
  for map_name, fname in data:
    yield ''
    yield  'Map: %s' % map_name
    yield  'Log: %s' % fname
    #d = deque(open(fname), 5 + N)
    d = deque(open(fname), 2 + util.PlayerCountFromTeamSize(TEAM_SIZE))
    yield  ''.join(d)

for line in PrintResults():
  print line

validation_filepath = os.path.join('C:/Coding/CodeTroopers/validation/',
                                   '%d_%s' % (TEAM_SIZE, datetime.datetime.now().strftime('%Y%m%d %H%M%S')))
with open(validation_filepath, 'w') as fout:
  fout.write('\n'.join(PrintResults()))
