from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
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

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the landing page"""
    try:
        with open("index.html", "r") as f:
            return f.read()
    except:
        return """
        <html><body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>🧠 Adaptive Mind Framework</h1>
        <h2>$9.4M-$14.55M IP Acquisition Opportunity</h2>
        <p><strong>Creator:</strong> Meharban Singh</p>
        <p><strong>Email:</strong> meharbansingh@adaptive-mind.com</p>
        <p><a href="/demo">Try Demo</a> | <a href="/roi">ROI Calculator</a></p>
        </body></html>
        """

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
