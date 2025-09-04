from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers.chat_product import router as chat_router
from routers.template_router import router as template_router
from routers.auth_router import router as auth_router
from routers.user_router import router as user_router
from routers.environment_router import router as environment_router
from routers.indicator_router import router as indicator_router
from dotenv import load_dotenv
import os

app = FastAPI(title="Regulation Backend API", version="1.0.0")
load_dotenv()

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

app.include_router(chat_router, prefix="/chat")
app.include_router(template_router, prefix="/template")
app.include_router(auth_router, prefix="/auth")  
app.include_router(user_router,prefix="/user")
app.include_router(indicator_router, prefix="/indicator")
app.include_router(environment_router, prefix="/environment")

# Static files
app.mount("/extracted", StaticFiles(directory="extracted"), name="extracted")
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)