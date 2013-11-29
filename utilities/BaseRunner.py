from MyStrategy import MyStrategy
from model.Move import Move
from utilities.RemoteProcessClient import RemoteProcessClient


class Runner:
    def __init__(self, port, seed):
      self.remote_process_client = RemoteProcessClient('127.0.0.1', int(port))
      self.token = '0000000000000000' #seed

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
