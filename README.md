# Agent LLM Logic Server

This repository contains the backend logic server used for the conversational AI experiment detailed in our paper submission. The server manages a dynamic, multi-turn dialogue state using a Large Language Model (LLM) and exposes a REST API for integration with frontends (e.g., MetaHuman or Ami).

## Overview
The system acts as an autonomous conversational agent (named "Mara"). The interaction is divided into two phases:
1. **Smalltalk Phase:** A natural, constrained conversation (max. 3 rounds) using prompt engineering to enforce human-like brevity and avoid AI typical behaviors.
2. **Pitch Phase:** A scripted informative monologue regarding ocean plastic pollution, seamlessly triggered after the smalltalk rounds are exhausted.

## Prerequisites
To run this project locally, you need:
- **Python 3.8+**
- **Ollama:** The server uses [Ollama](https://ollama.com/) to run the LLM locally. You must install Ollama on your system.
