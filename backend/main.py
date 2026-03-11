from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import auth, handover, carriers, settings, users

app = FastAPI(title="HandOver API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Tauri / Vite Dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datenbank beim Start initialisieren
@app.on_event("startup")
async def startup():
    init_db()

# Routers einbinden
app.include_router(auth.router,      prefix="/auth",     tags=["Auth"])
app.include_router(users.router,     prefix="/users",    tags=["Users"])
app.include_router(handover.router,  prefix="/handover", tags=["Handover"])
app.include_router(carriers.router,  prefix="/carriers", tags=["Carriers"])
app.include_router(settings.router,  prefix="/settings", tags=["Settings"])

@app.get("/health")
def health():
    return {"status": "ok"}
