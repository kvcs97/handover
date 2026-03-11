from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db, User
from pydantic import BaseModel
from datetime import datetime, timedelta
import bcrypt, jwt, os

router = APIRouter()
SECRET_KEY = os.environ.get("HANDOVER_SECRET", "handover-local-secret-change-in-prod")
ALGORITHM  = "HS256"
TOKEN_EXP  = 8  # Stunden

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Schemas ───────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type:   str
    user_name:    str
    user_role:    str


# ── Helpers ───────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub":  str(user_id),
        "role": role,
        "exp":  datetime.utcnow() + timedelta(hours=TOKEN_EXP)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.active:
            raise HTTPException(status_code=401, detail="Ungültiger Token")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session abgelaufen")
    except Exception:
        raise HTTPException(status_code=401, detail="Nicht autorisiert")

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Nur Admins haben Zugriff")
    return current_user


# ── Endpoints ─────────────────────────────────────────────

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-Mail oder Passwort falsch")
    if not user.active:
        raise HTTPException(status_code=403, detail="Account deaktiviert")
    return Token(
        access_token=create_token(user.id, user.role),
        token_type="bearer",
        user_name=user.name,
        user_role=user.role,
    )

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "role": current_user.role}
