from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db, User
from pydantic import BaseModel
from datetime import datetime, timedelta
from collections import defaultdict
import bcrypt, jwt, os, re, secrets, threading

router = APIRouter()
ALGORITHM = "HS256"
TOKEN_EXP = 8  # Stunden

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── JWT Secret (gerätespezifisch, einmalig generiert) ─────

def _load_or_create_secret() -> str:
    key_path = os.path.join(os.path.expanduser("~"), ".handover", "secret.key")
    if os.path.isfile(key_path):
        with open(key_path, "r") as f:
            return f.read().strip()
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    key = secrets.token_hex(32)
    with open(key_path, "w") as f:
        f.write(key)
    return key

SECRET_KEY = os.environ.get("HANDOVER_SECRET") or _load_or_create_secret()


# ── Rate Limiting (In-Memory) ──────────────────────────────

_failed:      dict[str, list] = defaultdict(list)
_locked:      dict[str, datetime] = {}
_rl_lock    = threading.Lock()
_MAX_ATTEMPTS = 5
_LOCKOUT_MIN  = 15

def _check_rate_limit(email: str) -> None:
    now = datetime.utcnow()
    with _rl_lock:
        if email in _locked:
            if now < _locked[email]:
                mins = int((_locked[email] - now).total_seconds() / 60) + 1
                raise HTTPException(status_code=429, detail=f"Zu viele Fehlversuche. Bitte {mins} Minute(n) warten.")
            _locked.pop(email)
            _failed.pop(email, None)

def _record_failure(email: str) -> None:
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=_LOCKOUT_MIN)
    with _rl_lock:
        _failed[email] = [t for t in _failed[email] if t > cutoff]
        _failed[email].append(now)
        if len(_failed[email]) >= _MAX_ATTEMPTS:
            _locked[email] = now + timedelta(minutes=_LOCKOUT_MIN)

def _clear_failures(email: str) -> None:
    with _rl_lock:
        _failed.pop(email, None)
        _locked.pop(email, None)


# ── Passwort-Validierung ───────────────────────────────────

_SPECIAL = re.compile(r'[^A-Za-z0-9]')

def _meets_policy(password: str) -> bool:
    return (
        len(password) >= 12
        and bool(re.search(r'[A-Z]', password))
        and bool(re.search(r'\d', password))
        and bool(_SPECIAL.search(password))
    )

def validate_password(password: str) -> None:
    errors = []
    if len(password) < 12:
        errors.append("mindestens 12 Zeichen")
    if not re.search(r'[A-Z]', password):
        errors.append("mindestens 1 Großbuchstaben")
    if not re.search(r'\d', password):
        errors.append("mindestens 1 Zahl")
    if not _SPECIAL.search(password):
        errors.append("mindestens 1 Sonderzeichen")
    if errors:
        raise HTTPException(status_code=400, detail="Passwort erfordert: " + ", ".join(errors))


# ── Schemas ───────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type:   str
    user_name:    str
    user_role:    str
    user_id:      int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password:     str

class UpgradePasswordRequest(BaseModel):
    email:            str
    current_password: str
    new_password:     str


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

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    _check_rate_limit(form.username)
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        _record_failure(form.username)
        raise HTTPException(status_code=401, detail="E-Mail oder Passwort falsch")
    if not user.active:
        raise HTTPException(status_code=403, detail="Account deaktiviert")
    _clear_failures(form.username)
    if not _meets_policy(form.password):
        return {"requires_password_change": True}
    return Token(
        access_token=create_token(user.id, user.role),
        token_type="bearer",
        user_name=user.name,
        user_role=user.role,
        user_id=user.id,
    )

@router.post("/upgrade-password", response_model=Token)
def upgrade_password(data: UpgradePasswordRequest, db: Session = Depends(get_db)):
    _check_rate_limit(data.email)
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.current_password, user.password_hash):
        _record_failure(data.email)
        raise HTTPException(status_code=401, detail="E-Mail oder Passwort falsch")
    if not user.active:
        raise HTTPException(status_code=403, detail="Account deaktiviert")
    validate_password(data.new_password)
    user.password_hash = hash_password(data.new_password)
    db.commit()
    _clear_failures(data.email)
    return Token(
        access_token=create_token(user.id, user.role),
        token_type="bearer",
        user_name=user.name,
        user_role=user.role,
        user_id=user.id,
    )

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "role": current_user.role}


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Aktuelles Passwort ist falsch")
    validate_password(data.new_password)
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"status": "password_changed"}
