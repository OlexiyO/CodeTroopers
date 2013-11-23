from collections import deque
from subprocess import call
import tempfile
from threading import Thread


N = 20
random_moves = 5

def DoValidate(port, map_name, output_file):
  global random_moves
  with open(output_file, 'w') as fout:
    call('python Validation.py %d %s %d %d' % (port, map_name, N, random_moves),
       shell=True,
       cwd='C:/Coding/CodeTroopers/src',
       stdout=fout)

port = 35000
threads = []
data = []
for map_name in ['default', 'map1']:
  filepath = tempfile.mktemp(prefix='C:/Coding/CodeTroopers/tmp/')
  print filepath
  t = Thread(target=DoValidate, kwargs={'port': port, 'map_name': map_name, 'output_file': filepath})
  threads.append(t)
  data.append((map_name, filepath))
  port += 1000

for t in threads:
  t.start()
for t in threads:
  t.join()

print 'Random moves:', random_moves
for map_name, fname in data:
  print
  print 'Map:', map_name
  d = deque(open(fname), 5 + N)
  print ''.join(d)
