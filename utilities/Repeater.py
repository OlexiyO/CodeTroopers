import util
from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
#token = '343beb9a9f24acd0570f68095f7fc596aa8d85a0' # check why we got stuck
token = '3a81ca50c93de320c07e79d35f4609c9c14713a6'

# 97271fd99afb15258db7bb39248d18f510666b0e -- check why didn't he run away
call([P, token], shell=True)
util.StartSavingDebugDataToDisk()
Runner(31001).run()