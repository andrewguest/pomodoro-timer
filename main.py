import json
import logging.config
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# Logging setup
with open("logging_conf.json", "r") as f:
    logging_conf = json.load(f)

logging.config.dictConfig(logging_conf)
fastapi_logger = logging.getLogger("fastapi")


# FastAPI setup
templates = Jinja2Templates(directory="templates")
app = FastAPI(
    title="Pomodoro timer",
    description="Web-based pomodoro timers.",
    version="0.0.1",
)

# This needs to be BEFORE the static files are mounted to allow for HTTPS redirection to work
#   url_for() in the HTML templates needs to know that the request can through HTTPS
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")  # ty:ignore[invalid-argument-type]
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middleware
app.add_middleware(
    CORSMiddleware,  # noqa  # ty:ignore[invalid-argument-type]
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    fastapi_logger.info(
        f"{request.client.host} - {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}s)"  # ty:ignore[possibly-missing-attribute]
    )

    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
