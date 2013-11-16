

from subprocess import call
from utilities.BaseRunner import Runner

P = 'C:/Coding/CodeTroopers/Runner/local-runner.bat'
call([P], shell=True)
Runner().run()