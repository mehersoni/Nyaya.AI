#!/usr/bin/env python3
"""
Nyayamrit FastAPI Server Startup Script

This script starts the Nyayamrit FastAPI server with proper configuration
for development and production environments.
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Start the FastAPI server."""
    
    # Environment configuration
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # Check if we're in development mode
    is_development = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.info(f"Starting Nyayamrit API server...")
    logger.info(f"Environment: {'development' if is_development else 'production'}")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Reload: {reload}")
    logger.info(f"Log level: {log_level}")
    
    # Check for required environment variables
    required_env_vars = []
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work correctly.")
    
    # Check for optional environment variables
    optional_env_vars = {
        "OPENAI_API_KEY": "OpenAI GPT-4 integration",
        "JWT_SECRET_KEY": "JWT token security",
        "BHASHINI_API_KEY": "Multilingual translation"
    }
    
    for var, description in optional_env_vars.items():
        if os.getenv(var):
            logger.info(f"✓ {var} configured - {description} enabled")
        else:
            logger.warning(f"✗ {var} not configured - {description} disabled")
    
    try:
        # Start the server
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            reload=reload and is_development,
            log_level=log_level,
            access_log=True,
            use_colors=True,
            app_dir=str(Path(__file__).parent)
        )
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()