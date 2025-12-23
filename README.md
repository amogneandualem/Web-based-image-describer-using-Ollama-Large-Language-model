# LLM Object Detection with Ollama

A web-based application for object detection using Vision Language Models (VLMs) through Ollama.

## Features
- Image upload for object detection
- Multiple VLM model support (Moondream, LLaVA)
- Multi-language description output
- Real-time translation capabilities

## Setup

1. Install Ollama: https://ollama.com/
2. Pull required models:
```bash
ollama pull moondream:1.8b
ollama pull llava:latest
ollama pull qwen2:7b
