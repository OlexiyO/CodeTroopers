import sys
from MyStrategy import MyStrategy
from RemoteProcessClient import RemoteProcessClient
from model.Move import Move


class Repeater:
    def __init__(self):
        if sys.argv.__len__() == 4:
            self.remote_process_client = RemoteProcessClient(sys.argv[1], int(sys.argv[2]))
            self.token = sys.argv[3]
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


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
token = None
call([P, token], shell=True)
Repeater().run()