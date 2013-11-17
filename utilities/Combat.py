

from subprocess import call
from BaseRunner import Runner

SHARED_ID = None #'0000000000000000'


def Server(map_name=None):
  cmd = ('start java -cp .;local-runner.jar Run -move-count=50'
         ' -render-to-screen=true -render-to-screen-scale=1.0 -render-to-screen-sync=true -debug=true -base-adapter-port=31000'
         ' -p1-name=v7_P1 -p2-name=v7_p2 -p3-name=Current -p4-name=v7_p4 -p1-team-size=3 -p2-team-size=3 -p3-team-size=3 -p4-team-size=3'
         ' "#LocalTestPlayer" "#LocalTestPlayer" "#LocalTestPlayer" "#LocalTestPlayer" -results-file=combat_result.txt')
  if map_name is not None:
    #cmd += ' -map=C:/Coding/CodeTroopers/maps/%s.map' % map
    cmd += ' -map=%s.map' % map_name
  call(cmd, shell=True, cwd='C:/Coding/CodeTroopers/Combat')


def Player(n):
  if n != R:
    D = 'C:/Coding/CodeTroopers/v7/'
    STRATEGY = 'C:/Coding/CodeTroopers/v7/RunPlayer.py'
  else:
    D = 'C:/Coding/CodeTroopers/src/'
    STRATEGY = 'C:/Coding/CodeTroopers/src/RunPlayer.py'
  call(['python', STRATEGY, 'localhost', str(31000 + n), SHARED_ID or '0000000000000000'], shell=True, cwd=D)

from threading import Thread
t1 = Thread(target=Server, args=('map1',))
# t1 = Thread(target=Server)
t1.start()

import time
time.sleep(2)

R = 2

for n in range(4):
  tp = Thread(target=Player, args=(n,))
  tp.start()
  time.sleep(.5)
