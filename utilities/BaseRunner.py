import sys
from MyStrategy import MyStrategy
import global_vars
from model.Move import Move
from utilities.RemoteProcessClient import RemoteProcessClient


class Runner:
    def __init__(self):
        if len(sys.argv) >= 4:
            self.remote_process_client = RemoteProcessClient(sys.argv[1], int(sys.argv[2]))
            self.token = sys.argv[3]
            global_vars.FIRST_MOVES_RANDOM = int(sys.argv[4]) if len(sys.argv) >= 5 else 0
        else:
            self.remote_process_client = RemoteProcessClient("localhost", 31001)
            self.token = "0000000000000000"

    def run(self):
        try:
            self.remote_process_client.write_token(self.token)
            team_size = self.remote_process_client.read_team_size()
            self.remote_process_client.write_protocol_version()
            game = self.remote_process_client.read_game_context()

            strategies = []

            for strategy_index in xrange(team_size):
                strategies.append(MyStrategy())

            while True:
                player_context = self.remote_process_client.read_player_context()
                if player_context is None:
                    break

                player_trooper = player_context.trooper

                move = Move()
                strategies[player_trooper.teammate_index].move(player_trooper, player_context.world, game, move)
                self.remote_process_client.write_move(move)
        finally:
            self.remote_process_client.close()
