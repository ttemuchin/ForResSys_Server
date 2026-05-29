from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.v1.routes import router as api_router
from db.session import engine
from config import config
import os

app = FastAPI(title=config.APP_NAME, debug=config.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
os.makedirs(config.UPLOAD_DIR, exist_ok=True)
os.makedirs(config.RESULTS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

app.include_router(api_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        print("Database connected")
    print("Application STARTUP complete")
    yield
    await engine.dispose()
    print("Application SHUTDOWN")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
