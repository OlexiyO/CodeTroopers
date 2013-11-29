import socket
import struct
from model.Bonus import Bonus
from model.BonusType import BonusType
from model.CellType import CellType
from model.Game import Game
from model.Player import Player
from model.PlayerContext import PlayerContext
from model.Trooper import Trooper
from model.TrooperStance import TrooperStance
from model.TrooperType import TrooperType
from model.World import World


class RemoteProcessClient:
    LITTLE_ENDIAN_BYTE_ORDER = True

    BYTE_ORDER_FORMAT_STRING = "<" if LITTLE_ENDIAN_BYTE_ORDER else ">"

    SIGNED_BYTE_SIZE_BYTES = 1
    INTEGER_SIZE_BYTES = 4
    LONG_SIZE_BYTES = 8
    DOUBLE_SIZE_BYTES = 8

    def __init__(self, host, port):
        self.socket = socket.socket()
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.socket.connect((host, port))
        self.cells = None
        self.cell_visibilities = None

    def write_token(self, token):
        self.write_enum(RemoteProcessClient.MessageType.AUTHENTICATION_TOKEN)
        self.write_string(token)

    def read_team_size(self):
        message_type = self.read_enum(RemoteProcessClient.MessageType)
        self.ensure_message_type(message_type, RemoteProcessClient.MessageType.TEAM_SIZE)
        return self.read_int()

    def write_protocol_version(self):
        self.write_enum(RemoteProcessClient.MessageType.PROTOCOL_VERSION)
        self.write_int(2)

    def read_game_context(self):
        message_type = self.read_enum(RemoteProcessClient.MessageType)
        self.ensure_message_type(message_type, RemoteProcessClient.MessageType.GAME_CONTEXT)
        if not self.read_boolean():
            return None

        return Game(
            self.read_int(),
            self.read_int(), self.read_int(),
            self.read_int(), self.read_double(),
            self.read_int(), self.read_int(), self.read_int(), self.read_int(),
            self.read_int(), self.read_double(),
            self.read_int(), self.read_int(),
            self.read_int(), self.read_int(), self.read_int(),
            self.read_double(), self.read_double(), self.read_double(),
            self.read_double(), self.read_double(),
            self.read_double(), self.read_double(),
            self.read_int(), self.read_double(), self.read_int(), self.read_int(),
            self.read_int(), self.read_int(), self.read_int(),
            self.read_int(), self.read_int()
        )

    def read_player_context(self):
        message_type = self.read_enum(RemoteProcessClient.MessageType)
        if message_type == RemoteProcessClient.MessageType.GAME_OVER:
            return None

        self.ensure_message_type(message_type, RemoteProcessClient.MessageType.PLAYER_CONTEXT)
        return PlayerContext(self.read_trooper(), self.read_world()) if self.read_boolean() else None

    def write_move(self, move):
        self.write_enum(RemoteProcessClient.MessageType.MOVE)

        if move is None:
            self.write_boolean(False)
        else:
            self.write_boolean(True)

            self.write_enum(move.action)
            self.write_enum(move.direction)
            self.write_int(move.x)
            self.write_int(move.y)

    def close(self):
        self.socket.close()

    def read_world(self):
        if not self.read_boolean():
            return None

        return World(
            self.read_int(), self.read_int(), self.read_int(), self.read_players(),
            self.read_troopers(), self.read_bonuses(), self.read_cells(), self.read_cell_visibilities()
        )

    def read_players(self):
        player_count = self.read_int()
        if player_count < 0:
            return None

        players = []

        for player_index in xrange(player_count):
            if self.read_boolean():
                player = Player(
                    self.read_long(), self.read_string(), self.read_int(), self.read_boolean(),
                    self.read_int(), self.read_int()
                )
                players.append(player)
            else:
                players.append(None)

        return players

    def read_troopers(self):
        trooper_count = self.read_int()
        if trooper_count < 0:
            return None

        troopers = []

        for trooper_index in xrange(trooper_count):
            troopers.append(self.read_trooper())

        return troopers

    def read_trooper(self):
        if not self.read_boolean():
            return None

        return Trooper(
            self.read_long(), self.read_int(), self.read_int(), self.read_long(),
            self.read_int(), self.read_boolean(), self.read_enum(TrooperType), self.read_enum(TrooperStance),
            self.read_int(), self.read_int(), self.read_int(), self.read_int(),
            self.read_double(), self.read_double(), self.read_int(),
            self.read_int(), self.read_int(), self.read_int(), self.read_int(),
            self.read_boolean(), self.read_boolean(), self.read_boolean()
        )

    def read_bonuses(self):
        bonus_count = self.read_int()
        if bonus_count < 0:
            return None

        bonuses = []

        for bonus_index in xrange(bonus_count):
            if self.read_boolean():
                bonus = Bonus(
                    self.read_long(), self.read_int(), self.read_int(), self.read_enum(BonusType)
                )
                bonuses.append(bonus)
            else:
                bonuses.append(None)

        return bonuses

    def read_cells(self):
        if self.cells is not None:
            return self.cells

        width = self.read_int()
        if width < 0:
            return None

        self.cells = []

        for x in xrange(width):
            height = self.read_int()
            if height < 0:
                self.cells.append(None)
                continue

            self.cells.append([])

            for y in xrange(height):
                self.cells[x].append(self.read_enum(CellType))

        return self.cells

    def read_cell_visibilities(self):
        if self.cell_visibilities is not None:
            return self.cell_visibilities

        world_width = self.read_int()
        if world_width < 0:
            return None

        world_height = self.read_int()
        if world_height < 0:
            return None

        stance_count = self.read_int()
        if stance_count < 0:
            return None

        self.cell_visibilities = self.read_bytes(world_width * world_height * world_width * world_height * stance_count)

        return self.cell_visibilities

    def ensure_message_type(self, actual_type, expected_type):
        if actual_type != expected_type:
            raise ValueError("Received wrong message [actual=%s, expected=%s]." % (actual_type, expected_type))

    def read_enum(self, enum_class):
        byte_array = self.read_bytes(RemoteProcessClient.SIGNED_BYTE_SIZE_BYTES)
        value = struct.unpack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "b", byte_array)[0]

        for enum_key, enum_value in enum_class.__dict__.iteritems():
            if not str(enum_key).startswith("__") and value == enum_value:
                return enum_value

        return None

    def write_enum(self, value):
        self.write_bytes(struct.pack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "b", -1 if value is None else value))

    def read_string(self):
        length = self.read_int()
        if length == -1:
            return None

        byte_array = self.read_bytes(length)
        return byte_array.decode("utf-8")

    def write_string(self, value):
        if value is None:
            self.write_int(-1)
            return

        byte_array = value.encode("utf-8")

        self.write_int(len(byte_array))
        self.write_bytes(byte_array)

    def read_boolean(self):
        byte_array = self.read_bytes(RemoteProcessClient.SIGNED_BYTE_SIZE_BYTES)
        return struct.unpack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "b", byte_array)[0] != 0

    def read_boolean_array(self, count):
        byte_array = self.read_bytes(count * RemoteProcessClient.SIGNED_BYTE_SIZE_BYTES)
        unpacked_bytes = struct.unpack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + str(count) + "b", byte_array)

        return [unpacked_bytes[i] != 0 for i in xrange(count)]

    def write_boolean(self, value):
        self.write_bytes(struct.pack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "b", 1 if value else 0))

    def read_int(self):
        byte_array = self.read_bytes(RemoteProcessClient.INTEGER_SIZE_BYTES)
        return struct.unpack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "i", byte_array)[0]

    def write_int(self, value):
        self.write_bytes(struct.pack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "i", value))

    def read_long(self):
        byte_array = self.read_bytes(RemoteProcessClient.LONG_SIZE_BYTES)
        return struct.unpack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "q", byte_array)[0]

    def write_long(self, value):
        self.write_bytes(struct.pack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "q", value))

    def read_double(self):
        byte_array = self.read_bytes(RemoteProcessClient.DOUBLE_SIZE_BYTES)
        return struct.unpack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "d", byte_array)[0]

    def write_double(self, value):
        self.write_bytes(struct.pack(RemoteProcessClient.BYTE_ORDER_FORMAT_STRING + "d", value))

    def read_bytes(self, byte_count):
        byte_array = ''

        while len(byte_array) < byte_count:
            chunk = self.socket.recv(byte_count - len(byte_array))

            if not len(chunk):
                raise IOError("Can't read %s bytes from input stream." % str(byte_count))

            byte_array += chunk

        return byte_array

    def write_bytes(self, byte_array):
        self.socket.sendall(byte_array)

    class MessageType:
        UNKNOWN = 0
        GAME_OVER = 1
        AUTHENTICATION_TOKEN = 2
        TEAM_SIZE = 3
        PROTOCOL_VERSION = 4
        GAME_CONTEXT = 5
        PLAYER_CONTEXT = 6
        MOVE = 7