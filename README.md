# Backend Server

This repository contains the backend logic server used for the conversational AI experiment detailed in our paper submission. The server manages a dynamic, multi-turn dialogue state using a Large Language Model (LLM) and exposes a REST API for integration with frontends (e.g., MetaHuman or Ami).

## Overview
The system acts as an autonomous conversational agent (named "Mara"). The interaction is divided into two phases:
1. Smalltalk Phase: A natural, constrained conversation (max. 3 rounds) using prompt engineering to enforce human-like brevity and avoid AI typical behaviors.
2. Pitch Phase: A scripted informative monologue regarding ocean plastic pollution, seamlessly triggered after the smalltalk rounds are exhausted.

## Prerequisites
To run this project locally, you need:
- Python 3.8+
- Ollama: The server uses Ollama to run the LLM locally. You must install Ollama on your system.

## Installation & Setup

1. Clone the repository:
git clone git [https://github.com/gaji1901/eam-user-study-agent.git](https://github.com/Gajen/eam-user-study-agent.git)
cd eam-user-study-agent
cd YOUR_REPO_NAME

2. Install Python dependencies:
pip install -r requirements.txt

3. Download the required LLM via Ollama:
The script is configured to use the llama3.3 model. Pull the model before starting the server:
ollama pull llama3.3

## Running the Server

Start the FastAPI server by running the python script:
python backend_server.py

Network Configuration Notes:
The server configuration inside backend_server.py should be adapted based on the connected frontend:
- Local setup (e.g., MetaHuman on the same machine): host="127.0.0.1", port=8000
- Network setup (e.g., Ami on a different device): host="0.0.0.0", port=8080

## API Endpoints

Once running, the server provides two main endpoints (accessible via POST requests).
FastAPI automatically generates an interactive API documentation available at http://127.0.0.1:8000/docs

### POST /api/agent/start
Initializes or resets the session state and returns the agent's greeting.

Response Example:
{
  "text": "Hallo, ich bin Mara. Schön, dass du da bist! Hast du gut hierher gefunden?",
  "type": "greeting"
}

### POST /api/agent/chat
Processes user input, queries the local LLM, and manages the transition between the smalltalk and pitch phases.

Request Body Example:
{
  "text": "Ja, ich habe gut hierher gefunden."
}

Response Example:
{
  "text": "Freut mich! Wie war deine Anreise?",
  "type": "smalltalk",
  "session_ended": false
}
