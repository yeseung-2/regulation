from fastapi import APIRouter, HTTPException, status, Depends
from .models.user_schema import UserCreate, UserLogin, UserOut
from services.database import users_collection
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from bson import ObjectId
from services.jwt_utils import get_current_user  # ✅ 중요: 현재 사용자 추출 함수

SECRET_KEY = "eri1"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

# ✅ 회원가입
@router.post("/register", response_model=UserOut)
def register(user: UserCreate):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    hashed_pw = pwd_context.hash(user.password)
    result = users_collection.insert_one({
        "email": user.email,
        "password": hashed_pw
    })
    return {"id": str(result.inserted_id), "email": user.email}

# ✅ 로그인
@router.post("/login")
def login(user: UserLogin):
    found = users_collection.find_one({"email": user.email})
    if not found or not pwd_context.verify(user.password, found["password"]):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    
    token_data = {
        "sub": str(found["_id"]),
        "exp": datetime.utcnow() + timedelta(minutes=60)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# ✅ 로그인 사용자 조회
@router.get("/me", response_model=UserOut)
def read_current_user(user: dict = Depends(get_current_user)):
    return user
