# backend/services/database.py
from pymongo import MongoClient

MONGO_URL = "mongodb+srv://iljv:ys020202!@project3.bjdh8mw.mongodb.net/?retryWrites=true&w=majority&appName=Project3"  # 또는 Atlas 클러스터 주소
client = MongoClient(MONGO_URL, tls=True)

db = client["login"]  # DB 이름
users_collection = db["users"]  # 회원정보 저장 컬렉션
