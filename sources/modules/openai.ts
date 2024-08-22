import axios from "axios";
import * as FileSystem from 'expo-file-system';
import { keys } from "../keys";

const BASE_URL= 'http://127.0.0.1:5000';

export async function transcribeAudio(audioPath: string) {
    try {
        const audioBase64 = await FileSystem.readAsStringAsync(audioPath, { encoding: FileSystem.EncodingType.Base64 });
        const response = await axios.post(`http://127.0.0.1:5000/audio/transcriptions`, {
            audio: audioBase64,
        });
        return response.data;
    } catch (error) {
        console.error("Error in transcribeAudio:", error);
        return null; // or handle error differently
    }
}

// let audioContext: AudioContext;

export async function startAudio() {
    audioContext = new AudioContext();
}


let audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

export async function textToSpeech(text: String) {
    try {
        // Request to convert text to speech
        const response = await axios.post("http://127.0.0.1:5000/audio/speech", {
            text: text
        }, {
            headers: {
                'Authorization': `Bearer ${keys.openai}`,  // Replace with your actual OpenAI API key
                'Content-Type': 'application/json'  // Set to application/json for text payload
            },
            responseType: 'arraybuffer'  // Handle binary data correctly
        });

        // Check the Content-Type header to ensure it is an audio format
        const contentType = response.headers['content-type']; 
        if (!contentType || !contentType.startsWith('audio/')) {
            throw new Error(`Unexpected Content-Type: ${contentType}`);
        }

        // Decode the audio data asynchronously
        const audioBuffer = await new Promise<AudioBuffer>((resolve, reject) => {
            audioContext.decodeAudioData(response.data, resolve, reject);
        });

        // Create an audio source
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start();  // Play the audio immediately

        return response.data;
    } catch (error) {
        console.error("Error in textToSpeech:", error);
        return null; // or handle error differently
    }
}

// Function to convert image to base64
async function imageToBase64(path: string) {
    try {
        const imageBase64 = await FileSystem.readAsStringAsync(path, { encoding: FileSystem.EncodingType.Base64 });
        return `data:image/jpeg;base64,${imageBase64}`; // Adjust the MIME type if necessary (e.g., image/png)
    } catch (error) {
        console.error("Error in imageToBase64:", error);
        return null; // or handle error differently
    }
}

export async function describeImage(imagePath: string) {
    const imageBase64 = await imageToBase64(imagePath);
    try {
        const response = await axios.post(`http://127.0.0.1:5000/images/descriptions`, {
            image: imageBase64,
        });
        return response.data;
    } catch (error) {
        console.error("Error in describeImage:", error);
        return null; // or handle error differently
    }
}

export async function gptRequest(systemPrompt: string, userPrompt: string) {
    try {
        const response = await axios.post(`http://127.0.0.1:5000/chat/completions`, {
            model: "gpt-3.5-turbo",
            messages: [
                { role: "system", content: systemPrompt },
                { role: "user", content: userPrompt },
            ],
        });
        return response.data;
    } catch (error) {
        console.error("Error in gptRequest:", error);
        return null; // or handle error differently
    }
}

// Example usage
textToSpeech("Hello I am your assistant, happy to help you");
gptRequest(
    `
        You are a smart AI that needs to read through the description of images and answer users' questions. 
        These are the provided images:
        The image features a woman standing in an open space with a metal roof, possibly at a train station or another large building.
        She is wearing a hat and appears to be looking up towards the sky.
        The scene captures her attention as she gazes upwards, perhaps admiring something above her or simply enjoying the view from this elevated position.

        DO NOT mention the images, scenes, or descriptions in your answer, just answer the question.
        DO NOT try to generalize or provide possible scenarios.
        ONLY use the information in the description of the images to answer the question.
        BE concise and specific.
    `,
    'where is the person?'
).then(response => console.info(response));