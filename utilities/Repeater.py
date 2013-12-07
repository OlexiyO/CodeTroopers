from dfs import PrintDebugInfo
import util
from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
token = 'd7a001bc365615c258a41fb14434739170d0b6b6'

call([P, token], shell=True)
util.StartSavingDebugDataToDisk()
Runner(31001).run()

PrintDebugInfo()