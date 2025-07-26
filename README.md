# Ultra-Low Latency AI Voice Agent

## Project Overview

**Ultra-Low Latency AI Voice Agent** is a real-time conversational AI system designed for **ultra-fast voice interactions**. This intelligent assistant delivers sub-500ms voice-to-voice response times using advanced technologies including **Google Gemini Live API**, **Pipecat AI framework**, and **RTVI protocol**. The system features a FastAPI backend with Next.js frontend, ensuring natural conversation flow with instant interruption support.

---

🌟 **Key Features**

* **Ultra-Low Latency**: Sub-500ms voice-to-voice response time
* **Real-time Audio Streaming**: Direct audio processing with Pipecat AI framework
* **Natural Interruption**: Instant interruption support for fluid conversations
* **Voice-Controlled Forms**: Fill and submit forms using voice commands
* **WebSocket Architecture**: Optimized real-time bidirectional communication
* **Modern UI**: Next.js 14 with Tailwind CSS and smooth animations
* **Performance Monitoring**: Real-time latency and connection metrics

---

🔧 **Key Technologies**

* **Backend**: Python (FastAPI, Pipecat AI, Google Gemini Live, WebSocket)
* **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Framer Motion
* **AI Framework**: Pipecat AI for real-time voice processing pipeline
* **AI Model**: Google Gemini Live API for conversational intelligence
* **Protocol**: RTVI (Real-Time Voice Interface) for standardized communication

---

📦 **Setup Instructions**

1. **Clone the Repository**
```bash
git clone https://github.com/AnthropoidFHJ/Low-Latency-AI-Voice-Agent.git
cd Low-Latency-AI-Voice-Agent
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Configure Environment Variables**

**Backend (.env):**
```env
GOOGLE_API_KEY="Your_Google_AI_Studio_API_Key"
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_BACKEND_URL=ws://localhost:8000
NEXT_PUBLIC_ENABLE_FORM_FILLING=true
NEXT_PUBLIC_ENABLE_VOICE_INTERRUPTION=true
```

5. **Run the Application**

```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

Visit: [http://localhost:3000](http://localhost:3000)

---

🎤 **Usage**

1. **Start**: Click microphone or say "Hello"
2. **Forms**: "Open contact form", "My name is John", "Submit form"
3. **Interrupt**: Speak anytime to interrupt the AI
4. **Monitor**: Check real-time performance metrics in UI

---

🔍 **API Endpoints**

- `GET /health` - System health and metrics
- `POST /api/voice/session` - Create voice session
- `WS /ws/voice/{client_id}` - Voice WebSocket connection
- `WS /ws/rtvi/{client_id}` - RTVI protocol connection

---

🐛 **Troubleshooting**

**High Latency**: Check network, API key, WebSocket connection
**Audio Issues**: Grant microphone permissions, try Chrome/Edge
**Connection Failed**: Ensure backend on port 8000, check CORS

---

**This project was developed as an intern task for Empowering Energy, demonstrating cutting-edge real-time voice AI technology with ultra-low latency conversational experiences.**

---

**Author:** Ferdous Hasan  
**Date:** July 26, 2025

