import os
from subprocess import call
import threading
import time
import dfs
import global_vars
import util
from utilities import BaseRunner

global_vars.AT_HOME = True

def RunServer(config_file, seed):
  #cmd = 'start java -cp .;local-runner.jar "%s"' % config_file
  cmd = 'start javaw -cp ".;*" -jar "local-runner.jar" '  +('"%s"' % config_file)
  if seed and int(seed) != 0:
    cmd += ' %s' % seed
  print cmd
  call(cmd, shell=True, cwd='C:/Coding/CodeTroopers/Runner')


def RunOldPlayer(port, ID, first_moves_random):
  VERSION = 12
  D = 'C:/Coding/CodeTroopers/v%d/' % VERSION
  STRATEGY = os.path.join(D, 'RunPlayer.py')
  if VERSION >= 22:
    call(['python', STRATEGY, str(port), first_moves_random], shell=True, cwd=D)
  else:
    call(['python', STRATEGY, '127.0.0.1', str(port), ID, first_moves_random], shell=True, cwd=D)


def RunLatestPlayer(port, ID, with_debug, first_moves_random):
  if with_debug:
    global_vars.FIRST_MOVES_RANDOM = int(first_moves_random or '0')
    runner = BaseRunner.Runner(port=port)
    util.StartSavingDebugDataToDisk()
    runner.run()
    dfs.PrintDebugInfo()
  else:
    D = 'C:/Coding/CodeTroopers/src/'
    STRATEGY = 'C:/Coding/CodeTroopers/src/RunPlayer.py'
    call(['python', STRATEGY, str(port), first_moves_random], shell=True, cwd=D)


def RunOneCombat(config_file, output_filepath, base_port, seed, my_player_index, with_debug, first_moves_random):
  tserver = threading.Thread(target=RunServer, args=(config_file, seed))
  tserver.start()
  time.sleep(.75)
  threads = [tserver]
  for n in range(4):
    if n == my_player_index:
      tgt = RunLatestPlayer
      tp = threading.Thread(target=tgt, args=(base_port + n, seed, with_debug, first_moves_random))
    else:
      tgt = RunOldPlayer
      tp = threading.Thread(target=tgt, args=(base_port + n, seed, first_moves_random))
    tp.start()
    threads.append(tp)
    time.sleep(.2)

  for t in threads:
    t.join()

  time.sleep(.2)
  with open(output_filepath) as fin:
    lines = [line.strip() for line in fin]
  assert lines[0] == 'OK'
  seed = lines[1][5:]
  if 'crashed' in lines[2 + my_player_index].lower():
    print lines
    print my_player_index
  place = int(lines[2 + my_player_index][0])
  return place, seed