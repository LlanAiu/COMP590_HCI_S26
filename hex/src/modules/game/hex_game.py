# builtin

# external

# internal
from .utils import ai_move, check_win, coord_to_index, empty_board 
from .types import GameMove


class HexGame: 
    game_id: str
    board: list[str]
    player: str
    last_move: str
    move_number: int
    status: str
    winner: str
    moves: list[dict]

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.board = empty_board()
        self.player = "red"
        self.last_move = ""
        self.move_number = 0
        self.status = "ok"
        self.winner = ""
        self.moves = []
        
    def process_move(self, input: GameMove):
        move = input.move
        player = input.player
        try:
            r, c = coord_to_index(move)
        except Exception:
            self.status = "invalid"
            return

        if not (0 <= r < len(self.board) and 0 <= c < len(self.board)):
            self.status = "invalid"
            return

        if self.board[r][c] != "0" or self.player != player or self.status == "win":
            self.status = "invalid"
            return

        row = list(self.board[r])
        row[c] = "R" if player == "red" else "B"
        self.board[r] = "".join(row)
        self.last_move = move
        self.move_number += 1
        self.moves.append({"move": move, "player": "R" if player == "red" else "B"})

        if check_win(self.board, player):
            self.status = "win"
            self.winner = player
            return

        self.player = "blue" if player == "red" else "red"

        if self.player == "blue":
            ai = ai_move(self.board, "red")
            r_ai, c_ai = coord_to_index(ai)
            row = list(self.board[r_ai])
            row[c_ai] = "B"
            self.board[r_ai] = "".join(row)
            self.last_move = ai
            self.move_number += 1
            self.moves.append({"move": ai, "player": "B"})
            if check_win(self.board, "blue"):
                self.status = "win"
                self.winner = "blue"
            else:
                self.player = "red"
    
    def to_json(self) -> dict:
        return {
            "gameId": self.game_id,
            "board": self.board,
            "player": self.player,
            "lastMove": self.last_move,
            "moveNumber": self.move_number,
            "status": self.status,
            "moves": self.moves,
            "winner": self.winner
        }