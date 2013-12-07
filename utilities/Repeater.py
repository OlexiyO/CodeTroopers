from dfs import PrintDebugInfo
import util
from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
token = '564a03715287ddf23792167cc07cec5026cd11fc'

call([P, token], shell=True)
util.StartSavingDebugDataToDisk()
Runner(31001).run()

PrintDebugInfo()