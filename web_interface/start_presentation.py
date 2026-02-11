#!/usr/bin/env python3
"""
Nyayamrit Presentation Startup Script

This script starts both the main Nyayamrit API server and the deployment demo
dashboard for presentations and demonstrations.
"""

import os
import sys
import time
import subprocess
import threading
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_main_api():
    """Start the main Nyayamrit API server."""
    logger.info("Starting main Nyayamrit API server on port 8000...")
    
    try:
        # Change to web_interface directory
        os.chdir(Path(__file__).parent)
        
        # Start the main API server
        subprocess.run([
            sys.executable, "app.py"
        ], check=True)
        
    except KeyboardInterrupt:
        logger.info("Main API server stopped by user")
    except Exception as e:
        logger.error(f"Main API server failed: {e}")


def start_demo_dashboard():
    """Start the deployment demo dashboard."""
    logger.info("Starting deployment demo dashboard on port 8080...")
    
    try:
        # Wait a moment for main API to start
        time.sleep(3)
        
        # Change to web_interface directory
        os.chdir(Path(__file__).parent)
        
        # Start the demo dashboard
        subprocess.run([
            sys.executable, "deployment_demo.py"
        ], check=True)
        
    except KeyboardInterrupt:
        logger.info("Demo dashboard stopped by user")
    except Exception as e:
        logger.error(f"Demo dashboard failed: {e}")


def main():
    """Start both servers for presentation."""
    
    print("=" * 80)
    print("🎯 NYAYAMRIT PRESENTATION SETUP")
    print("=" * 80)
    print("Starting GraphRAG-based Judicial Assistant for demonstration...")
    print()
    print("📊 Main API Server: http://127.0.0.1:8000")
    print("   • REST API endpoints")
    print("   • Interactive documentation at /docs")
    print("   • Health check at /health")
    print()
    print("🖥️  Demo Dashboard: http://127.0.0.1:8080")
    print("   • System overview and statistics")
    print("   • Live interactive demo")
    print("   • Real-time performance metrics")
    print()
    print("🚀 Live Demo Interface: http://127.0.0.1:8080/demo/live")
    print("   • Try queries as citizen, lawyer, or judge")
    print("   • See real-time responses with citations")
    print("   • Explore example questions")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 80)
    
    try:
        # Start main API server in a separate thread
        api_thread = threading.Thread(target=start_main_api, daemon=True)
        api_thread.start()
        
        # Wait a moment for API to start
        time.sleep(5)
        
        # Start demo dashboard in main thread
        start_demo_dashboard()
        
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("🛑 Shutting down presentation servers...")
        print("=" * 80)
        logger.info("Presentation stopped by user")
    except Exception as e:
        logger.error(f"Presentation startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()