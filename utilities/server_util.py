from subprocess import call
import threading
import time
from utilities import BaseRunner
from utilities.RemoteProcessClient import RemoteProcessClient

def RunServer(map_name, my_player_index, output_file, render, base_port, ID):
  base_cmd = 'start java -cp .;local-runner.jar Run %(flags)s "#LocalTestPlayer" "#LocalTestPlayer" "#LocalTestPlayer" "#LocalTestPlayer"'
  flags_dict = {
    'move-count': 50,
    'debug': 'true', 'base-adapter-port': base_port,
    'p1-name': 'v7_P1', 'p2-name': 'v7_p2', 'p3-name': 'v7_p3', 'p4-name': 'v7_p4',
    'p1-team-size': 3, 'p2-team-size': 3, 'p3-team-size': 3, 'p4-team-size': 3,
    'seed': ID,
    'results-file': output_file}
  if render:
    flags_dict.update({'render-to-screen': 'true', 'render-to-screen-scale': 1.0, 'render-to-screen-sync': 'true'})
  if map_name is not None and map_name != 'default':
    flags_dict['map'] = '%s.map' % map_name

  key = 'p%d-name' % (my_player_index + 1)
  assert key in flags_dict, key
  flags_dict[key] = 'Latest'
  printed_flags = ' '.join('-%s=%s' % tup for tup in flags_dict.iteritems())
  full_cmd = base_cmd % {'flags': printed_flags}
  print full_cmd
  call(full_cmd, shell=True, cwd='C:/Coding/CodeTroopers/Combat')


def RunOldPlayer(base_port, index, ID):
  D = 'C:/Coding/CodeTroopers/v7/'
  STRATEGY = 'C:/Coding/CodeTroopers/v7/RunPlayer.py'
  call(['python', STRATEGY, 'localhost', str(base_port + index), ID], shell=True, cwd=D)


def RunLatestPlayer(base_port, index, ID, with_debug):
  if with_debug:
    runner = BaseRunner.Runner()
    runner.remote_process_client = RemoteProcessClient('localhost', base_port + index)
    runner.token = ID
    runner.run()
  else:
    D = 'C:/Coding/CodeTroopers/src/'
    STRATEGY = 'C:/Coding/CodeTroopers/src/RunPlayer.py'
    call(['python', STRATEGY, 'localhost', str(base_port + index), ID], shell=True, cwd=D)


def RunOneCombat(map, filepath, my_player_index, base_port, ID, render, with_debug):
  ID = ID or '0000000000000000'
  print ID
  tserver = threading.Thread(target=RunServer, args=(map, my_player_index, filepath, render, base_port, ID))
  tserver.start()
  time.sleep(1.)
  threads = [tserver]
  for n in range(4):
    if n == my_player_index:
      tgt = RunLatestPlayer
      tp = threading.Thread(target=tgt, args=(base_port, n, ID, with_debug))
    else:
      tgt = RunOldPlayer
      tp = threading.Thread(target=tgt, args=(base_port, n, ID))
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
  place = int(lines[2 + my_player_index][0])
  return place, seed