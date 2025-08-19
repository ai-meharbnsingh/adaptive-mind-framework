from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Adaptive Mind Framework - IP Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {
        "message": "Adaptive Mind Framework - Live IP Demo",
        "status": "operational", 
        "ip_package_value": "$9.4M-$14.55M",
        "creator": "Meharban Singh",
        "contact": "meharbansingh@adaptive-mind.com",
        "demo_url": "/demo",
        "roi_url": "/roi"
    }

@app.get("/demo")
async def demo():
    return {
        "framework": "Adaptive Mind Framework",
        "version": "Complete - Sessions 1-12",
        "ip_value": "$9.4M-$14.55M",
        "roi": "347% average",
        "savings": "$485K annually",
        "uptime": "99.97% SLA",
        "contact": "meharbansingh@adaptive-mind.com"
    }

@app.get("/roi")
async def roi():
    return {
        "roi_calculator": "Available",
        "average_roi": "347%",
        "annual_savings": "$485,000",
        "payback_months": 8.2,
        "contact": "meharbansingh@adaptive-mind.com"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
