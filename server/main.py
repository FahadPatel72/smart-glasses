from flask_cors import CORS
from flask import Flask, request, jsonify, make_response
import base64
import requests
import io
import wave
import os
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)

DEEPGRAM_API_KEY = "8d75fcc2828c159f8554d736880d0fe745153b49"
LLM_API_KEY = "43b8a91a67412e1dd709373052ce3ce295531822bccddd77686cf7758b63cbd9"

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

@app.route('/chat/completions', methods=['POST', 'OPTIONS'])
def chat_completions():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    try:
        url = "https://llm.mdb.ai/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        data = request.json

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"Error from LLM API: {response.status_code} - {response.text}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/image/description', methods=['POST', 'OPTIONS'])
def image_description():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    try:
        base64_image = request.json.get('image')

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }

        payload = {
            "model": "gemini-1.5-pro",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What’s in this image?"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = requests.post("https://llm.mdb.ai/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"Error from LLM API: {response.status_code} - {response.text}"}), response.status_code

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
    




