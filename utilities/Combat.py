import random
from utilities import server_util
from utilities.create_config import CreateConfigFile

SHARED_ID = '0000000000000000'
#SHARED_ID = '3479362486062050'

output_filepath = 'C:/Coding/CodeTroopers/Combat/result.txt'
base_port = 31111
my_player_index = 2  #random.randint(0, 3)
print my_player_index
config_file = CreateConfigFile(output_filepath=output_filepath,
                               base_port=base_port,
                               seed=SHARED_ID,
                               render='true',
                               map_name='cheeser',
                               my_player_index=my_player_index)
import time
time.sleep(.05)
server_util.RunOneCombat(config_file, with_debug=True, first_moves_random='0', my_player_index=my_player_index,
                         output_filepath=output_filepath, seed=SHARED_ID, base_port=base_port)
