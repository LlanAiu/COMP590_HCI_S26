# builtin
import random
from collections import deque

# external

# internal


def empty_board(n: int = 11) -> list[str]:
    return ["0" * n for _ in range(n)]

def coord_to_index(coord: str) -> tuple[int, int]:
    col = ord(coord[0]) - 65
    row = int(coord[1:]) - 1
    return row, col

def check_win(board: list[str], player: str) -> bool:
    n = len(board)
    visited: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()
    if player == "red":
        for c in range(n):
            if board[0][c] == "R":
                q.append((0, c))
                visited.add((0, c))
        while q:
            r, c = q.popleft()
            if r == n - 1:
                return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == "R" and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
    else:
        for r in range(n):
            if board[r][0] == "B":
                q.append((r, 0))
                visited.add((r, 0))
        while q:
            r, c = q.popleft()
            if c == n - 1:
                return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == "B" and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
    return False

def ai_move(board: list[str], opponent: str) -> str:
    n = len(board)
    opp = "R" if opponent == "blue" else "B"
    empties: list[tuple[int, int]] = []
    adj: list[tuple[int, int]] = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == "0":
                empties.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == opp:
                        adj.append((r, c))
                        break
    choice = random.choice(adj if adj else empties)
    return chr(65 + choice[1]) + str(choice[0] + 1)