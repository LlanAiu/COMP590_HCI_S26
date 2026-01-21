# builtin

# external
from pydantic import BaseModel

# internal


class GameMove(BaseModel):
    move: str
    player: str
    