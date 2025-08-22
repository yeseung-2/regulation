from pymongo import MongoClient

# ✅ Atlas URI
MONGO_URI = "mongodb+srv://iljv:ys020202!@project3.bjdh8mw.mongodb.net/?retryWrites=true&w=majority&appName=Project3"

# ✅ 데이터베이스명과 컬렉션명
DB_NAME = "project3"
COLLECTION_NAME = "drafts"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
draft_collection = db[COLLECTION_NAME]

input_collection = db["draft_inputs"]  # 또는 "form_inputs"
