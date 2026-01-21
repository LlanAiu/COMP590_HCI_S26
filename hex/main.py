# builtin
from contextlib import asynccontextmanager

# external
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# internal
from src.api import create_game_router, submit_move_router, download_moves_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.games = {}
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.include_router(router=create_game_router)
app.include_router(router=submit_move_router)
app.include_router(router=download_moves_router)