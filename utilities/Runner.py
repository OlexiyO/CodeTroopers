import os
from subprocess import call
import datetime
import MyStrategy
import search
import util
from utilities.BaseRunner import Runner


util.SaveDebugDataToDisk()

P = 'C:/Coding/CodeTroopers/Runner/local-runner.bat'
call([P], shell=True)
Runner().run()

search.PrintDebugInfo()
