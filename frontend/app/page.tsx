'use client';

import { useState, useEffect, useRef } from 'react';

type FormData = {
  name: string;
  phone: string;
  jobTitle: string;
};

type ChatMessage = {
  type: 'user' | 'assistant';
  message: string;
  timestamp: Date;
};

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';
type RecordingStatus = 'idle' | 'recording' | 'processing';

export default function Home() {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    phone: '',
    jobTitle: ''
  });
  
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [recordingStatus, setRecordingStatus] = useState<RecordingStatus>('idle');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [isAISpeaking, setIsAISpeaking] = useState<boolean>(false);
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);

  const [recognition, setRecognition] = useState<any>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const speechSynthesisRef = useRef<SpeechSynthesisUtterance | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const speechRecognition = new (window as any).webkitSpeechRecognition();
      speechRecognition.continuous = false;
      speechRecognition.interimResults = false;
      speechRecognition.lang = 'en-US';
      
      speechRecognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        console.log('Speech recognition result:', transcript);
        
        // Send transcript through WebSocket
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'chat',
            message: transcript,
            timestamp: new Date().toISOString()
          }));
        }
        
        setRecordingStatus('idle');
      };
      
      speechRecognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setRecordingStatus('idle');
      };
      
      speechRecognition.onend = () => {
        setRecordingStatus('idle');
      };
      
      setRecognition(speechRecognition);
    }
  }, []);
  useEffect(() => {
    const cleanup = () => {
      if (speechSynthesisRef.current) {
        speechSynthesis.cancel();
        speechSynthesisRef.current = null;
      }
    };

    return cleanup;
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      setConnectionStatus('connecting');
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        console.log('Connected to WebSocket');
        setConnectionStatus('connected');
        wsRef.current = ws;
        
        // Send connection message
        ws.send(JSON.stringify({
          type: 'connect',
          timestamp: new Date().toISOString()
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received:', data);

          // Handle different message types from backend
          if (data.type === 'welcome') {
            const welcomeMessage = "Hello! I'll collect your name, phone number, and job title. Can you please provide your information?";
            setChatHistory(prev => [...prev, {
              type: 'assistant',
              message: welcomeMessage,
              timestamp: new Date()
            }]);
            // Speak the welcome message
            setTimeout(() => speakText(welcomeMessage), 500);
          } else if (data.type === 'chat_response') {
            if (data.user_message) {
              setChatHistory(prev => [...prev, {
                type: 'user',
                message: data.user_message,
                timestamp: new Date()
              }]);
            }
            if (data.ai_response) {
              setChatHistory(prev => [...prev, {
                type: 'assistant',
                message: data.ai_response,
                timestamp: new Date()
              }]);
              speakText(data.ai_response);
            }
          } else if (data.type === 'form_update' || data.action === 'field_updated') {
            if (data.action === 'form_submitted') {
              // Handle form submission
              setIsSubmitted(true);
              setChatHistory(prev => [...prev, {
                type: 'assistant',
                message: "Form submitted successfully! Thank you for providing your information.",
                timestamp: new Date()
              }]);
              speakText("Form submitted successfully! Thank you for providing your information.");
            } else {
              // Handle field updates
              setFormData(prev => ({
                ...prev,
                [data.field]: data.value
              }));
            }
          } else if (data.action === 'form_submitted') {
            // Handle form submission
            setIsSubmitted(true);
            setChatHistory(prev => [...prev, {
              type: 'assistant',
              message: "Form submitted successfully! Thank you for providing your information.",
              timestamp: new Date()
            }]);
            speakText("Form submitted successfully! Thank you for providing your information.");
          } else if (data.action === 'assistant_response') {
            setChatHistory(prev => [...prev, {
              type: 'assistant',
              message: data.message,
              timestamp: new Date()
            }]);
            
            if (data.message) {
              speakText(data.message);
            }
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        wsRef.current = null;
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
      };

    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setConnectionStatus('disconnected');
      setTimeout(connectWebSocket, 3000);
    }
  };

  const speakText = (text: string) => {
    if (speechSynthesisRef.current) {
      speechSynthesis.cancel();
      speechSynthesisRef.current = null;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    utterance.onstart = () => {
      setIsAISpeaking(true);
    };
    
    utterance.onend = () => {
      setIsAISpeaking(false);
      speechSynthesisRef.current = null;
    };
    
    utterance.onerror = () => {
      setIsAISpeaking(false);
      speechSynthesisRef.current = null;
    };

    speechSynthesisRef.current = utterance;
    speechSynthesis.speak(utterance);
  };

  const setupAudioAnalysis = (stream: MediaStream) => {
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(stream);
    
    analyser.smoothingTimeConstant = 0.8;
    analyser.fftSize = 512;
    
    microphone.connect(analyser);
    audioContextRef.current = audioContext;
    analyserRef.current = analyser;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const updateAudioLevel = () => {
      if (recordingStatus === 'recording' && analyserRef.current) {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / bufferLength;
        setAudioLevel(average / 255);
        requestAnimationFrame(updateAudioLevel);
      }
    };

    updateAudioLevel();
  };

  const startRecording = async () => {
    if (recordingStatus !== 'idle' || connectionStatus !== 'connected' || isSubmitted || !recognition) return;

    try {
      setRecordingStatus('recording');
      recognition.start();
      
      // Start visual feedback for recording
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        }
      });
      
      setupAudioAnalysis(stream);
    } catch (error) {
      console.error('Error starting recording:', error);
      setRecordingStatus('idle');
      setAudioLevel(0);
    }
  };

  const stopRecording = () => {
    if (recordingStatus !== 'recording') return;

    setRecordingStatus('processing');
    
    if (recognition) {
      recognition.stop();
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close().then(() => {
        audioContextRef.current = null;
        analyserRef.current = null;
      });
    }
  };

  const submitForm = () => {
    if (formData.name && formData.phone && formData.jobTitle) {
      setIsSubmitted(true);
      setChatHistory(prev => [...prev, {
        type: 'assistant',
        message: `Thank you ${formData.name}! Your information has been submitted successfully. Phone: ${formData.phone}, Job: ${formData.jobTitle}`,
        timestamp: new Date()
      }]);
      
      setTimeout(() => {
        speakText(`Thank you ${formData.name}! Your information has been submitted successfully.`);
      }, 100);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800">
      <div className="flex min-h-screen">
        {/* Left Column - Form Section */}
        <div className="w-1/3 p-6 border-r border-gray-700/50">
          <div className="h-full flex flex-col">
            {/* Form Header */}
            <div className="text-center mb-6">
              <h2 className="text-xl font-bold text-white mb-3">
                Information Form
              </h2>
              <p className="text-gray-400 text-sm">
                Fill in your details
              </p>
            </div>

            {/* Form Data */}
            <div className="flex-1 space-y-4">
              <div className="space-y-4">
                <div className="p-6 bg-gray-800/60 border border-gray-700/50 rounded-2xl backdrop-blur-sm hover:bg-gray-700/60 transition-all duration-300">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-300">Name</p>
                        <p className="text-xs text-gray-500">Full name</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${
                        formData.name ? 'text-white text-lg' : 'text-gray-500 text-sm'
                      }`}>
                        {formData.name || 'Not provided'}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="p-6 bg-gray-800/60 border border-gray-700/50 rounded-2xl backdrop-blur-sm hover:bg-gray-700/60 transition-all duration-300">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-300">Phone Number</p>
                        <p className="text-xs text-gray-500">11 digits (01XXX-XXXXXX)</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${
                        formData.phone ? 'text-white text-lg' : 'text-gray-500 text-sm'
                      }`}>
                        {formData.phone || 'Not provided'}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="p-6 bg-gray-800/60 border border-gray-700/50 rounded-2xl backdrop-blur-sm hover:bg-gray-700/60 transition-all duration-300">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2h2zm4-3a1 1 0 00-1 1v1h2V4a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-300">Job Title</p>
                        <p className="text-xs text-gray-500">Your profession</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${
                        formData.jobTitle ? 'text-white text-lg' : 'text-gray-500 text-sm'
                      }`}>
                        {formData.jobTitle || 'Not provided'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              {formData.name && formData.phone && formData.jobTitle && !isSubmitted && (
                <button
                  onClick={submitForm}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-4 px-6 rounded-2xl transition-all duration-300 transform hover:scale-[1.02] shadow-lg shadow-green-500/30 hover:shadow-green-500/50"
                >
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Submit Form
                  </span>
                </button>
              )}

              {/* Success Message */}
              {isSubmitted && (
                <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/50 rounded-2xl p-6 text-center backdrop-blur-sm">
                  <div className="text-green-400 text-3xl mb-2">✅</div>
                  <p className="text-green-300 font-semibold text-lg mb-1">Form submitted successfully!</p>
                  <p className="text-green-400 text-sm">Thank you for providing your information.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Middle Column - Voice Controls */}
        <div className="w-1/3 p-6 border-r border-gray-700/50 flex flex-col justify-center">
          <div className="text-center">
            {/* Main Logo and Title */}
            <div className="mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl mb-6 shadow-xl">
                <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              </div>
              
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
                Voice Assistant
              </h1>
              <p className="text-gray-300 text-lg leading-relaxed mb-6">
                Tell me your information
              </p>
              
              {/* Connection Status */}
              <div className="flex items-center justify-center mb-8">
                <div className={`flex items-center space-x-3 px-6 py-3 rounded-full border ${
                  connectionStatus === 'connected' 
                    ? 'bg-green-500/20 border-green-500/50 text-green-400' :
                  connectionStatus === 'connecting' 
                    ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400' : 
                    'bg-red-500/20 border-red-500/50 text-red-400'
                }`}>
                  <div className={`w-3 h-3 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-green-400 animate-pulse' :
                    connectionStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'
                  }`}></div>
                  <span className="text-base font-medium capitalize">{connectionStatus}</span>
                </div>
              </div>
            </div>

            {/* Voice Control Button */}
            <div className="mb-8">
              <div className="relative inline-block mb-6">
                {/* Animated ring for recording */}
                {recordingStatus === 'recording' && (
                  <div className="absolute inset-0 rounded-full border-4 border-red-400/50 animate-ping"></div>
                )}
                
                <button
                  onMouseDown={startRecording}
                  onMouseUp={stopRecording}
                  onTouchStart={startRecording}
                  onTouchEnd={stopRecording}
                  disabled={connectionStatus !== 'connected' || isSubmitted}
                  className={`relative w-40 h-40 rounded-full font-medium text-white transition-all duration-300 shadow-2xl ${
                    recordingStatus === 'recording' 
                      ? 'bg-gradient-to-r from-red-500 to-red-600 scale-110 shadow-red-500/50' 
                      : recordingStatus === 'processing'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse shadow-blue-500/50'
                      : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 hover:scale-105 shadow-blue-500/30'
                  } disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100`}
                >
                  <span className="text-5xl">
                    {recordingStatus === 'recording' ? '🔴' : 
                     recordingStatus === 'processing' ? '⏳' : '🎤'}
                  </span>
                </button>
              </div>
              
              <p className={`text-lg font-medium mb-6 ${
                recordingStatus === 'recording' ? 'text-red-400' :
                recordingStatus === 'processing' ? 'text-blue-400' :
                connectionStatus !== 'connected' ? 'text-gray-500' :
                isSubmitted ? 'text-green-400' : 'text-gray-400'
              }`}>
                {connectionStatus !== 'connected' ? 'Connecting...' : 
                 recordingStatus === 'recording' ? '🎵 Listening...' :
                 recordingStatus === 'processing' ? '🤔 Processing...' :
                 isSubmitted ? '✅ Form submitted!' : '🎤 Hold to speak'}
              </p>
            </div>

            {/* Audio Visualization */}
            <div className="flex items-center justify-center space-x-4 h-20">
              {/* User Voice Bars */}
              <div className="flex items-end space-x-1">
                <div className="text-sm text-gray-400 mb-2 mr-3">You:</div>
                {[...Array(10)].map((_, i) => (
                  <div
                    key={`user-${i}`}
                    className="w-2 bg-gradient-to-t from-blue-400 to-blue-600 rounded-full transition-all duration-100"
                    style={{
                      height: recordingStatus === 'recording' 
                        ? `${Math.max(6, audioLevel * 60 + Math.random() * 12)}px`
                        : '6px'
                    }}
                  ></div>
                ))}
              </div>
              
              <div className="w-px h-12 bg-gray-600 mx-6"></div>
              
              {/* AI Voice Bars */}
              <div className="flex items-end space-x-1">
                <div className="text-sm text-gray-400 mb-2 mr-3">AI:</div>
                {[...Array(10)].map((_, i) => (
                  <div
                    key={`ai-${i}`}
                    className="w-2 bg-gradient-to-t from-purple-400 to-purple-600 rounded-full transition-all duration-100"
                    style={{
                      height: isAISpeaking 
                        ? `${Math.max(6, Math.random() * 40 + 12)}px`
                        : '6px'
                    }}
                  ></div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Chat History */}
        <div className="w-1/3 p-6 flex flex-col">
          <div className="flex-1 bg-gray-900/60 border border-gray-700/50 rounded-2xl backdrop-blur-sm p-4">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
              Conversation History
            </h3>
            
            <div className="h-full overflow-y-auto space-y-4 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
              {chatHistory.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7z" clipRule="evenodd" />
                  </svg>
                  <p>Start speaking to begin the conversation</p>
                </div>
              ) : (
                <>
                  {chatHistory.map((msg, index) => (
                    <div
                      key={index}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                          msg.type === 'user'
                            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                            : 'bg-gray-700 text-gray-200'
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{msg.message}</p>
                        <p className={`text-xs mt-1 ${
                          msg.type === 'user' ? 'text-blue-100' : 'text-gray-400'
                        }`}>
                          {msg.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                  <div ref={chatEndRef}></div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}