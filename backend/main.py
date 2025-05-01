"""
Main entry point for the Promora application.

This module provides the main entry point for starting the Promora application.
"""

import uvicorn
import os
from dotenv import load_dotenv

from promora.api.app import app

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
