# 🌍 Web-based Image Describer & Multilingual Translator (Ollama LLM/VLM Chain)

This project provides a local, web-based tool for multimodal tasks. It uses an **Ollama-powered chain** to perform two key steps:
1.  **Image Analysis (VLM):** Generate a detailed English description of an uploaded image.
2.  **Multilingual Translation (LLM):** Translate the generated English description into a low-resource language (like Amharic) or a high-resource language (like Chinese) using a specialized multilingual LLM.

The application is built using **Flask** and communicates with a local **Ollama** server via its REST API.

---

## ⚙️ Prerequisites

You must have **Ollama** installed and running on your system to serve the models.

### 1. Install Ollama and Required Models

Run the following commands in your terminal to download the necessary models:

| Model Name | Purpose | Role in Chain |
| :--- | :--- | :--- |
| `moondream:1.8b` | Fast Image Captioning | VLM (User Selectable) |
| `llava:latest` | Detailed Image Analysis | VLM (User Selectable) |
| `qwen2:7b` | Robust Multilingual Translation | LLM (Fixed Translator) |

```bash
# Pull the VLM models for image analysis
ollama pull moondream:1.8b
ollama pull llava:latest

# Pull the specialized LLM for translation
ollama pull qwen2:7b
