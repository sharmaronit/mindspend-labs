"""
Simple script to start the FastAPI server
Run: python run_server.py
"""

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

# Get configuration
host = os.getenv("API_HOST", "127.0.0.1")
port = int(os.getenv("API_PORT", "8001"))

print(f"🔧 Starting Personal Behavioral Analyst API")
print(f"📍 Running on http://{host}:{port}")
print(f"📚 API docs available at http://{host}:{port}/docs")
print("Press CTRL+C to stop the server\n")

# Import app after printing startup message
from main import app

# Start the server
uvicorn.run(
    app,
    host=host,
    port=port,
    reload=False,
    log_level="info"
)
