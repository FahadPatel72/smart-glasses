#!/bin/bash

# Start Ollama in the background
ollama serve &

# Start Flask application
exec python app.py
