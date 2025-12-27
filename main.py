import ipaddress
import logging.config
import os
import time

import axiom_py
from axiom_py.logging import AxiomHandler
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# Logging setup
load_dotenv()
client = axiom_py.Client(os.getenv("AXIOM_TOKEN"))
handler = AxiomHandler(client, "pomodoro-timer")
logging.getLogger().addHandler(handler)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


def get_ipv4(ip_address: str) -> str:
    """Convert IPv6 to IPv4 if possible"""

    try:
        ip_obj = ipaddress.ip_address(ip_address)

        # Check if it's an IPv4-mapped IPv6 address
        if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
            return str(ip_obj.ipv4_mapped)

        # Return as-is if already IPv4 or pure IPv6
        return str(ip_obj)

    except ValueError:
        # Invalid IP, return as-is
        return ip_address


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1_000

    # Get the real client IP from proxy headers
    # Since this is behind a reverse proxy, `request.client` keeps coming back as 127.0.0.1
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host

    logger.info(
        "Request received",
        extra={
            "ip": get_ipv4(client_ip),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "response_time_ms": f"{process_time_ms:.2f}",
            "user_agent": request.headers.get("user-agent"),
        },
    )

    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /"
