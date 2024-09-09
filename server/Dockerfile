
# Use Python 3.9 base image
FROM python:3.9

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl ffmpeg

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set up working directory
WORKDIR /server

# Copy application files
COPY . .

# Install Python requirements
RUN pip install -r requirements.txt

# Expose the ports for both services
EXPOSE 5000 11432

# Copy the startup script into the container
COPY start_services.sh /start_services.sh
RUN chmod +x /start_services.sh

# Set the default command to run the startup script
CMD ["/start_services.sh"]
