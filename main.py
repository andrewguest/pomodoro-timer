import os

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


# Logging setup
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Enable sending logs to Sentry
    enable_logs=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=0.1,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
)


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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /"
