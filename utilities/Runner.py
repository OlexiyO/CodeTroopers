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

print '\n'.join('%s: %.2f' % t for t in sorted(util.TOTAL_TIME.iteritems(), reverse=True, key=lambda x: x[1]))
print '\n'.join('Move %d: %d' % (t[1], t[0]) for t in sorted(search.M, reverse=True))
print 'Total:', sum(x[0] for x in search.M)