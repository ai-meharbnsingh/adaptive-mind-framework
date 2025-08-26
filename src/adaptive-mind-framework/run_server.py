# run_server.py
import uvicorn

# The .env file is now loaded automatically by the application and pytest.
# This script is just a convenience launcher.

if __name__ == "__main__":
    print("--- 🚀 LAUNCHING ADAPTIVE MIND SERVER 🚀 ---")
    print("Reading configuration from .env file...")
    uvicorn.run("antifragile_framework.api.framework_api:app",
                host="127.0.0.1", port=8000, reload=True)