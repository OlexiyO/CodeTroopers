import util
from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
#token = '343beb9a9f24acd0570f68095f7fc596aa8d85a0' # check why we got stuck
token = '67eb39a780b3277f6bab87c7a3df34353f341ce7'

# 97271fd99afb15258db7bb39248d18f510666b0e -- check why didn't he run away
call([P, token], shell=True)
util.StartSavingDebugDataToDisk()
Runner(31001).run()