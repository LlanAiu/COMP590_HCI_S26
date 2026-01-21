# builtin

# external
from pydantic import BaseModel

# internal


class MoveInput(BaseModel):
    gameId: str
    move: str
    player: str