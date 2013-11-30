from subprocess import call
import dfs
import util
from utilities.BaseRunner import Runner


util.StartSavingDebugDataToDisk()

P = 'C:/Coding/CodeTroopers/Runner/local-runner-vs-smart-guys.bat'
call([P], shell=True)
Runner(31001).run()

dfs.PrintDebugInfo()
