

from subprocess import call
from BaseRunner import Runner


def Server():
  P = 'C:/Coding/CodeTroopers/Combat/combat.bat'
  call([P], shell=True)

from threading import Thread
t1 = Thread(target=Server)
t1.start()

import time
time.sleep(2)

def Player(n):
  STRATEGY = 'C:/Coding/CodeTroopers/src/utilities/RunnerForCombat.py'
  call(['python', STRATEGY, 'localhost', str(31000 + n), '0000000000000000'], shell=True)

for n in range(4):
  tp = Thread(target=Player, args=(n,))
  tp.start()
