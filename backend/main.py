from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="Regulation Backend API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Regulation Backend API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "port": os.getenv("PORT", "8000")}

# 라우터 import 및 등록 (오류 방지)
try:
    from routers.chat_product import router as chat_router
    app.include_router(chat_router, prefix="/chat")
except ImportError as e:
    print(f"Warning: chat_router import failed: {e}")

try:
    from routers.template_router import router as template_router
    app.include_router(template_router, prefix="/template")
except ImportError as e:
    print(f"Warning: template_router import failed: {e}")

try:
    from routers.auth_router import router as auth_router
    app.include_router(auth_router, prefix="/auth")
except ImportError as e:
    print(f"Warning: auth_router import failed: {e}")

try:
    from routers.user_router import router as user_router
    app.include_router(user_router, prefix="/user")
except ImportError as e:
    print(f"Warning: user_router import failed: {e}")

try:
    from routers.environment_router import router as environment_router
    app.include_router(environment_router, prefix="/environment")
except ImportError as e:
    print(f"Warning: environment_router import failed: {e}")

try:
    from routers.indicator_router import router as indicator_router
    app.include_router(indicator_router, prefix="/indicator")
except ImportError as e:
    print(f"Warning: indicator_router import failed: {e}")

# Static files (디렉토리가 존재할 때만)
try:
    if os.path.exists("extracted"):
        app.mount("/extracted", StaticFiles(directory="extracted"), name="extracted")
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Static files mount failed: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)