# Use Python 3.9 base image
FROM python:3.9

WORKDIR /server

# Copy application files
COPY . .

# Install Flask requirements
RUN pip install -r requirements.txt

# Install curl
RUN apt-get update && apt-get install -y curl

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

RUN ollama serve &

EXPOSE 5000

# Set the default command to run the application
CMD [ "python", "main.py" ] 

