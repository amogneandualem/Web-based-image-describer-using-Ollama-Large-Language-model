#!/bin/bash
# ===========================================
# QUICK OLLAMA SETUP SCRIPT
# ===========================================

echo "🚀 Starting Ollama Server..."

# Start Ollama in background
ollama serve &
OLLAMA_PID=$!

# Wait for server to start
sleep 5

echo "📦 Checking/Downloading models..."

# Check and download required models
for model in "llava:latest" "moondream:1.8b" "qwen2:7b"; do
    if ! ollama list | grep -q "$model"; then
        echo "⬇️  Downloading $model..."
        ollama pull "$model"
    else
        echo "✅ $model already installed"
    fi
done

echo ""
echo "==========================================="
echo "✅ OLLAMA SERVER IS READY!"
echo "==========================================="
echo ""
echo "📊 Installed models:"
ollama list
echo ""
echo "📡 Server running at: http://localhost:11434"
echo ""
echo "👉 Keep this terminal open!"
echo "👉 Open a NEW terminal for ngrok"
echo "==========================================="

# Keep script running
wait $OLLAMA_PID
