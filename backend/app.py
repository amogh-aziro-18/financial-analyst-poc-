from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import finance

app = FastAPI(title="Financial Analyst POC API")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(finance.router)

@app.get("/")
def root():
    return {"message": "Financial Analyst POC Backend is running"}
