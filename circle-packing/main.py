from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
	app.state.pack_cache = {}
	yield


app = FastAPI(title="Circle Packing", lifespan=lifespan)

# mount static and templates (paths are project-relative)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
	return templates.TemplateResponse("index.html", {"request": request})


app.include_router(router)

app.state.templates = templates


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
