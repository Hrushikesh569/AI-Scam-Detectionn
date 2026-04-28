from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import analyze
from utils.database import init_db

app = FastAPI(title="AI Scam Detection API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes; in production specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database when app starts
@app.on_event("startup")
def on_startup():
    init_db()
    print("Database initialized successfully.")

# Register Routers
app.include_router(analyze.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Scam Detection System with Behavioral Context API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
