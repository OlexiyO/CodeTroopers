from dfs import PrintDebugInfo
import util
from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
token = '2fefb8e42cba7352024d54341aa2dece93925ea1'

call([P, token], shell=True)
util.StartSavingDebugDataToDisk()
Runner(31001).run()

PrintDebugInfo()