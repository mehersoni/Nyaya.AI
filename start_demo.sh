#!/bin/bash

echo "==============================================================================="
echo "                    NYAYAMRIT DEPLOYMENT DEMONSTRATION"
echo "==============================================================================="
echo ""
echo "Starting GraphRAG-based Judicial Assistant for presentation..."
echo ""
echo "Main API Server will start on: http://127.0.0.1:8000"
echo "Demo Dashboard will start on:  http://127.0.0.1:8080"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""
echo "==============================================================================="

cd web_interface
python3 start_presentation.py