from dfs import PrintDebugInfo
import util
from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
token = '794998a2f07b4f00fc997a873d85fdf0984db504'

call([P, token], shell=True)
util.StartSavingDebugDataToDisk()
Runner(31001).run()

PrintDebugInfo()