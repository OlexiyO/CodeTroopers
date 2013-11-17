import os
from subprocess import call
import datetime
import MyStrategy
import search
import util
from utilities.BaseRunner import Runner

dt = datetime.datetime.now().strftime('%m%d_%H%M%S')
MyStrategy.LOG_DIR = os.path.join('C:/Coding/CodeTroopers/logs', dt)
os.makedirs(MyStrategy.LOG_DIR)

P = 'C:/Coding/CodeTroopers/Runner/local-runner.bat'
call([P], shell=True)
Runner().run()

print util.TOTAL_TIME
print sorted(search.M, reverse=True)
print sum(x[0] for x in search.M)