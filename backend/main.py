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

app = FastAPI()
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat")
app.include_router(template_router, prefix="/template")
app.include_router(auth_router, prefix="/auth")  
app.include_router(user_router,prefix="/user")
app.include_router(indicator_router, prefix="/indicator")
app.include_router(environment_router, prefix="/environment")

app.mount("/extracted", StaticFiles(directory="extracted"), name="extracted")
app.mount("/extracted", StaticFiles(directory="extracted"), name="extracted")
app.mount("/static", StaticFiles(directory="static"), name="static")