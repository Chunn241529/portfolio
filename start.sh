#!/bin/bash

# Start the FastAPI server in the background
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 &

# Wait a few seconds for the server to start
sleep 5

# Start ngrok with the config file
ngrok start --config ngrok.yml portfolio
