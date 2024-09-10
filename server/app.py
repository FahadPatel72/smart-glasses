from flask_cors import CORS
from flask import Flask, request, jsonify, make_response
import base64
import requests
import io
import wave
import os
import google.generativeai as genai
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME")

genai.configure(api_key=GEMINI_API_KEY)

@app.route('/', methods=['GET'])
def index():
    return "Hi, I am working (server) "

@app.route('/audio/transcriptions', methods=['POST'])
def transcribe_audio():
    try:
        # Check if the request contains the audio file
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']

        # Ensure the file is in WAV format
        if audio_file.filename.split('.')[-1] not in ['wav']:
            return jsonify({"error": "Unsupported file format. Only WAV files are supported."}), 400

        # Prepare headers
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav"
        }

        # Prepare data to send
        data = audio_file.read()

        # Make POST request to Deepgram API
        url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
        response = requests.post(url, headers=headers, data=data)

        # Check if the request was successful
        if response.status_code == 200:
            transcript = response.json()
            return jsonify(transcript), 200
        else:
            return jsonify({"error": f"Error from Deepgram API: {response.status_code} - {response.text}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/audio/speech', methods=['POST', 'OPTIONS'])
def text_to_speech():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    try:
        # Define the API endpoint
        url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"

        # Define the headers
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }

        # Get text input from the request
        text = request.json['text']

        # Define the payload
        payload = {
            "text": text
        }

        # Make the POST request to Deepgram API
        response = requests.post(url, headers=headers, json=payload)
        print("Deepgram Response Status Code:", response.status_code)
        print("Deepgram Response Headers:", response.headers)
        print("Deepgram Response Content:", response.text[:500])  # Log only the first 500 characters for safety
        # Check if the request was successful
        if response.status_code == 200:
            # Return the audio content as response
            return response.content, 200, {'Content-Type': 'audio/mpeg'}
        else:
            return jsonify({"error": f"Error from Deepgram API: {response.status_code} - {response.text}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def image_description():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    try:
        # Set generation configuration
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        # Initialize the generative model
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config,
        )
        
        # Extract base64 image from the request
        image_data = request.data
        
        # if not base64_image:
        #     return jsonify({"error": "No image provided"}), 400

        # Decode base64 image and save it temporarily
        # image_data = base64.b64decode(base64_image)
        image_path = "uploaded_image.png"
        with open(image_path, "wb") as f:
            f.write(image_data)

        # Upload image to Gemini
        uploaded_file = upload_to_gemini(image_path, mime_type="image/png")

        # Start a chat session with the image to describe it
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        uploaded_file,
                        "describe image",
                    ],
                }
            ]
        )

        # Generate the description by sending the message
        response = chat_session.send_message("What's in this image?")
        
        # Return the description
        if response:
            return jsonify({"description": response.text}), 200
        else:
            return jsonify({"error": "Failed to generate description"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST', 'OPTIONS'])
def ollama_generate():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    try:    
        data = request.json
        model = data['model']
        messages = data['messages']

        converted = []
        for message in messages:
            converted_message = {
                'role': message['role'],
                'content': trim_ident(message['content']),
                'images': [to_base64(image) for image in message.get('images', [])]
            }
            converted.append(converted_message)

        response = requests.post(f"{os.getenv('OLLAMA_URL')}/api/generate", json={
        'stream': False,
        'model': model,
        'messages': converted
    })

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"Error from LLM API: {response.status_code} - {response.text}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def trim_ident(content):
    # Add your trimIdent logic here
    return content

def to_base64(image):
    return base64.b64encode(image).decode('utf-8')
  
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)