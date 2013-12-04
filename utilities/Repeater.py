from dfs import PrintDebugInfo
import util
from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
token = 'fd733b2be1c1f39aa9492ced480b4146185837b7' # my last loss

# 97271fd99afb15258db7bb39248d18f510666b0e -- check why didn't he run away
call([P, token], shell=True)
util.StartSavingDebugDataToDisk()
Runner(31001).run()

PrintDebugInfo()