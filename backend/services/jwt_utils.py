
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from services.database import users_collection

import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "eri1")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="토큰에 사용자 정보 없음")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")
    
    return {
        "id": str(user["_id"]),
        "email": user["email"]
    }