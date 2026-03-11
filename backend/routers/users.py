from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, User
from routers.auth import require_admin, hash_password
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UserCreate(BaseModel):
    name:     str
    email:    str
    password: str
    role:     str  # admin | operator | viewer

class UserUpdate(BaseModel):
    name:     Optional[str] = None
    role:     Optional[str] = None
    active:   Optional[bool] = None
    password: Optional[str] = None

@router.get("/")
def list_users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return db.query(User).all()

@router.post("/")
def create_user(data: UserCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="E-Mail bereits vergeben")
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "role": user.role}

@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if data.name:     user.name = data.name
    if data.role:     user.role = data.role
    if data.active is not None: user.active = data.active
    if data.password: user.password_hash = hash_password(data.password)
    db.commit()
    return {"status": "updated"}

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    user.active = False  # Soft-Delete
    db.commit()
    return {"status": "deactivated"}
