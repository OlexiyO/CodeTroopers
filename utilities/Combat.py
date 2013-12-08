import util
from utilities import server_util
from utilities.create_config import CreateConfigFile

SHARED_ID = '0000000000000000'
#SHARED_ID = '3513451172593653' -- VERY slow battle on map02
#SHARED_ID = '4247638308748542'

output_filepath = 'C:/Coding/CodeTroopers/Combat/result.txt'
base_port = 31111
my_player_index = 1  #random.randint(0, 3)
print my_player_index
TEAM_SIZE = 4
config_file = CreateConfigFile(output_filepath=output_filepath,
                               base_port=base_port,
                               seed=SHARED_ID,
                               render='true',
                               map_name='map06',
                               team_size=TEAM_SIZE,
                               my_player_index=my_player_index)
import time
time.sleep(.05)
server_util.RunOneCombat(config_file, with_debug=True, first_moves_random='0', my_player_index=my_player_index,
                         output_filepath=output_filepath, seed=SHARED_ID, base_port=base_port,
                         player_count=util.PlayerCountFromTeamSize(TEAM_SIZE))