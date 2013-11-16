from utilities.BaseRunner import Runner
import MyStrategy

print 'Running my strategy vs SmartGuy multiple times.'


from subprocess import call
P = 'C:/Coding/CodeTroopers/Runner/multi-local-runner.bat'
result_file = 'C:/Coding/CodeTroopers/Runner/result.txt'
total = 0
N = 50
for n in range(N):
  call([P], shell=True)
  MyStrategy.INITIALIZED = False
  Runner().run()
  import time
  time.sleep(.1)
  with open(result_file) as fin:
    cnt = 0
    for line in fin:
      assert 'crashed' not in line.lower()
      if cnt == 3:
        total += int(line[0])
      cnt += 1

print total / float(N)