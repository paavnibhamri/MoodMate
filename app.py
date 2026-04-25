import os
import io
import librosa
import numpy as np
from flask import Flask, request, jsonify
from transformers import pipeline
from flask_cors import CORS
from pydub import AudioSegment
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# 1. DEFINE DATA FIRST
mood_data = {
    "positive": {
        "label": "Happy",
        "playlists": [
            "https://open.spotify.com/embed/playlist/37i9dQZF1DXdPecmS3pbvE",
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX3rxm52Sdb67",
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX0UrUEbi9sfM"
        ],
        "quotes": ["Happiness is contagious!", "Keep that energy up!"]
    },
    "neutral": {
        "label": "Neutral",
        "playlists": [
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX4WYpdgoIcnC",
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX8Ueb990u307",
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX6VBr993v97T"
        ],
        "quotes": ["Stay centered.", "Focus on the now."]
    },
    "negative": {
        "label": "Sad",
        "playlists": [
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX3YSRmBhyWM3",
            "https://open.spotify.com/embed/playlist/37i9dQZF1DX7qK8maErh9L",
            "https://open.spotify.com/embed/playlist/37i9dQZF1DWSqWur9S7Sxt"
        ],
        "quotes": ["This too shall pass.", "It's okay to feel."]
    }
}

mood_history = []

# 2. LOAD MODELS
print("⏳ Loading AI Models... Please wait.")
asr_model = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")
sentiment_model = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
print("✅ Models Loaded Successfully!")

@app.route("/analyze", methods=["POST"])
def analyze():
    text = ""
    print("\n--- 🔍 NEW REQUEST ---")
    
    # Handle Audio
    if 'audio' in request.files:
        print("🎙️ Processing Audio...")
        audio_file = request.files['audio']
        try:
            audio_bytes = audio_file.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            audio_np = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
            audio_np /= np.iinfo(audio_segment.array_type).max
            
            asr_result = asr_model(audio_np, generate_kwargs={"task": "transcribe", "language": "en"})
            text = asr_result["text"]
            print(f"📝 TRANSCRIPT: {text}")
        except Exception as e:
            print(f"❌ AUDIO ERROR: {e}")
            return jsonify({"error": str(e)}), 400
    else:
        # Handle Text
        data = request.json
        text = data.get("text", "")
        print(f"⌨️ TEXT INPUT: {text}")

    if not text.strip():
        print("⚠️ EMPTY INPUT")
        return jsonify({"error": "No text detected"}), 400

    # 3. ANALYSIS
    res = sentiment_model(text)[0]
    sentiment = res['label'].lower() # 'positive', 'neutral', 'negative'
    print(f"🎭 SENTIMENT: {sentiment}")
    
    # Get mood info or default to neutral
    info = mood_data.get(sentiment, mood_data["neutral"])
    
    response = {
        "mood": info["label"],
        "quote": random.choice(info["quotes"]),
        "text": text,
        "playlists": info["playlists"],
        "timestamp": datetime.now().strftime("%I:%M %p")
    }
    
    mood_history.append(response)
    return jsonify({**response, "history": mood_history[-10:]})

if __name__ == "__main__":
    app.run(debug=True, port=5000)