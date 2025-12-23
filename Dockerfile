FROM python:3.9-slim
# Install Ollama
RUN curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/bin/ollama && chmod +x /usr/bin/ollama
# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Start Ollama and Streamlit together
CMD ollama serve & sleep 5 && ollama pull llava && streamlit run app.py
