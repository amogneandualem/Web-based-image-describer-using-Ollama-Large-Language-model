# Use a Python base image (adjust version if necessary)
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Hugging Face Spaces requires
EXPOSE 7860

# Command to run the application using Gunicorn (recommended for production)
# Note: Hugging Face Spaces usually proxies traffic to 0.0.0.0:7860
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:app"]
