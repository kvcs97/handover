from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routers import auth, handover, carriers, settings, users
from routers import outlook_router, license_router, courier

@asynccontextmanager
async def lifespan(app: FastAPI):
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
