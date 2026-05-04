from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from logging.handlers import RotatingFileHandler
from database import init_db
from routers import auth, handover, carriers, settings, users
from routers import outlook_router, license_router, courier


def _setup_file_logging() -> None:
    """Schreibt Kurier-/Outlook-Logs in `~/.handover/handover.log` (rotierend),
    damit Bugs auch im Tauri-Sidecar-Modus nachvollziehbar sind."""
    log_dir = os.path.join(os.path.expanduser("~"), ".handover")
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(log_dir, "handover.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    handler.setLevel(logging.INFO)

    for name in ("courier.email", "courier.router", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.setLevel(logging.INFO)
        # nicht doppelt anhängen wenn Reload
        if not any(isinstance(h, RotatingFileHandler) for h in lg.handlers):
            lg.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_file_logging()
    init_db()
    yield

app = FastAPI(title="HandOver API", version="1.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,           prefix="/auth",     tags=["Auth"])
app.include_router(users.router,          prefix="/users",    tags=["Users"])
app.include_router(handover.router,       prefix="/handover", tags=["Handover"])
app.include_router(carriers.router,       prefix="/carriers", tags=["Carriers"])
app.include_router(settings.router,       prefix="/settings", tags=["Settings"])
app.include_router(outlook_router.router, prefix="/outlook",  tags=["Outlook"])
app.include_router(license_router.router, prefix="/license",  tags=["License"])
app.include_router(courier.router,        prefix="/api/courier", tags=["Courier"])

@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
