"""
Customer Support Portal Application Runner Script
-------------------------------------------------
Starts the dedicated support portal FastAPI app in development mode.
"""

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "app.support_portal_main:support_portal_app",
        host="0.0.0.0",
        port=int(os.getenv("SUPPORT_PORTAL_PORT", 6050)),
        reload=True,
        workers=1
    )
    print("Customer Support server started successfully")