# builtin
import random

# external

# internal
from .utils import empty_board 


class HexGame: 
    game_id: str
    board: list[str]
    player: str
    last_move: str
    move_number: int
    status: str
    moves: list[str]

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.board = empty_board()
        self.player = "red"
        self.last_move = ""
        self.move_number = 0
        self.status = "ok"
        self.moves = []

    
    def to_json(self) -> dict:
        return {
            "gameId": self.game_id,
            "board": self.board,
            "player": self.player,
            "lastMove": self.last_move,
            "moveNumber": self.move_number,
            "status": self.status,
            "moves": self.moves 
        }