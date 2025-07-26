'use client';

import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Mic,
    MicOff,
    Volume2,
    VolumeX,
    Wifi,
    WifiOff,
    Activity,
    AlertTriangle,
    CheckCircle,
    Clock,
    MessageSquare
} from 'lucide-react';
import { useVoiceAgent } from '../lib/voice-client';
import { useRTVIClient, VoiceClientCallbacks } from '../lib/rtvi-client';
import { useVoiceState, useConnectionStatus, useMetrics, usePerformanceAlerts } from '../lib/store';
import { AudioManager } from '../lib/audio-manager';

const VoiceWaveform: React.FC<{ isActive: boolean; amplitude?: number }> = ({
    isActive,
    amplitude = 1
}) => {
    return (
        <div className="flex items-center justify-center space-x-1 h-8">
            {Array.from({ length: 5 }).map((_, i) => (
                <motion.div
                    key={i}
                    className="voice-wave bg-current"
                    animate={isActive ? {
                        height: [4, 20 * amplitude, 4],
                    } : { height: 4 }}
                    transition={{
                        duration: 1.2,
                        repeat: isActive ? Infinity : 0,
                        delay: i * 0.1,
                        ease: "easeInOut"
                    }}
                />
            ))}
        </div>
    );
};

const StatusIndicator: React.FC<{
    status: 'connected' | 'disconnected' | 'processing';
    label: string
}> = ({ status, label }) => {
    const icons = {
        connected: CheckCircle,
        disconnected: WifiOff,
        processing: Activity,
    };

    const colors = {
        connected: 'text-voice-active',
        disconnected: 'text-voice-error',
        processing: 'text-voice-speaking',
    };

    const Icon = icons[status];

    return (
        <div className={`status-indicator ${status} flex items-center space-x-2`}>
            <Icon className={`w-4 h-4 ${colors[status]}`} />
            <span className="text-xs font-medium">{label}</span>
        </div>
    );
};

const LatencyIndicator: React.FC<{ latency: number }> = ({ latency }) => {
    const getLatencyColor = (ms: number) => {
        if (ms < 200) return 'good';
        if (ms < 500) return 'warning';
        return 'poor';
    };

    return (
        <div className={`latency-indicator ${getLatencyColor(latency)}`}>
            <Clock className="w-3 h-3" />
            <span>{Math.round(latency)}ms</span>
        </div>
    );
};

const PerformanceAlerts: React.FC = () => {
    const alerts = usePerformanceAlerts();

    return (
        <AnimatePresence>
            <motion.div
                className="mb-4 space-y-2"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
            >
                <div className="glass-panel p-3">
                    <div className="flex items-center space-x-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-voice-speaking" />
                        <span className="text-xs font-medium text-text-secondary">
                            Performance Alerts
                        </span>
                    </div>
                    <div className="space-y-1">
                        {alerts.slice(-3).map((alert, index) => (
                            <p key={index} className="text-xs text-text-secondary">
                                {alert}
                            </p>
                        ))}
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

export const VoiceInterface: React.FC = () => {
    const voiceState = useVoiceState();
    const { isConnected, error } = useConnectionStatus();
    const metrics = useMetrics();
    const alerts = usePerformanceAlerts();

    const {
        connect,
        disconnect,
        startConversation,
        interrupt,
        isConnected: checkConnection,
        client,
    } = useVoiceAgent();

    const [isMuted, setIsMuted] = useState(false);
    const [volume, setVolume] = useState(1.0);
    const [isInitializing, setIsInitializing] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [amplitude, setAmplitude] = useState(0);
    const [micPermission, setMicPermission] = useState<boolean | null>(null);

    const audioManagerRef = useRef<AudioManager | null>(null);

    useEffect(() => {
        audioManagerRef.current = new AudioManager();

        return () => {
            if (audioManagerRef.current) {
                audioManagerRef.current.cleanup();
            }
        };
    }, []);

    useEffect(() => {
        if (!isConnected && !isInitializing) {
            setIsInitializing(true);
            connect()
                .then((success) => {
                    if (success) {
                        console.log('Voice agent connected successfully');
                    }
                })
                .catch(console.error)
                .finally(() => setIsInitializing(false));
        }
    }, [isConnected, connect, isInitializing]);

    const requestMicrophonePermission = async () => {
        if (!audioManagerRef.current) return false;

        const hasPermission = await audioManagerRef.current.requestMicrophonePermission();
        setMicPermission(hasPermission);
        return hasPermission;
    };

    const handleVoiceButtonClick = async () => {
        if (!isConnected) {
            await connect();
            return;
        }

        if (voiceState === 'listening' || isRecording) {

            if (audioManagerRef.current) {
                audioManagerRef.current.stopRecording();
                setIsRecording(false);
                setAmplitude(0);
            }
            return;
        }

        if (micPermission === null) {
            const hasPermission = await requestMicrophonePermission();
            if (!hasPermission) {
                alert('Microphone permission is required for voice input. Please allow microphone access and try again.');
                return;
            }
        }

        const conversationStarted = startConversation();

        if (conversationStarted && audioManagerRef.current) {
            const recordingStarted = await audioManagerRef.current.startRecording(

                async (audioBlob: Blob) => {
                    if (checkConnection() && audioBlob.size > 0 && client) {
                        try {

                            console.log('Sending audio chunk:', audioBlob.size, 'bytes');
                            const success = await client.sendAudioBlob(audioBlob);
                            if (!success) {
                                console.warn('Failed to send audio data - connection lost');
                            }
                        } catch (error) {
                            console.error('Failed to send audio data:', error);
                        }
                    }
                },

                (newAmplitude: number) => {
                    setAmplitude(newAmplitude);
                }
            );

            if (recordingStarted) {
                setIsRecording(true);
            } else {
                alert('Failed to start microphone recording. Please check your microphone and try again.');
            }
        }
    };

    const toggleMute = () => {
        setIsMuted(!isMuted);
    };

    const getVoiceButtonState = () => {
        switch (voiceState) {
            case 'listening':
                return 'listening';
            case 'speaking':
                return 'speaking';
            case 'connected':
            case 'idle':
                return 'active';
            default:
                return 'inactive';
        }
    };

    const getVoiceButtonText = () => {
        switch (voiceState) {
            case 'connecting':
                return 'Connecting...';
            case 'listening':
                return isRecording ? 'Recording...' : 'Listening';
            case 'speaking':
                return 'Speaking';
            case 'processing':
                return 'Processing...';
            case 'error':
                return 'Error - Retry';
            default:
                return isConnected ? 'Start Talking' : 'Connect';
        }
    };

    const getStatusColor = () => {
        if (error) return 'text-voice-error';
        if (isRecording) return 'text-voice-listening';
        if (isConnected) return 'text-voice-active';
        return 'text-voice-inactive';
    };

    return (
        <div className="relative w-full max-w-2xl mx-auto">
            {}
            {alerts.length > 0 && <PerformanceAlerts />}

            {}
            <div className="glass-panel p-8 text-center">
                {}
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center space-x-3">
                        <StatusIndicator
                            status={isConnected ? 'connected' : error ? 'disconnected' : 'processing'}
                            label={isConnected ? 'Connected' : error ? 'Disconnected' : 'Connecting'}
                        />
                        {metrics.latency > 0 && (
                            <LatencyIndicator latency={metrics.latency} />
                        )}
                    </div>

                    <div className="flex items-center space-x-2">
                        <button
                            onClick={toggleMute}
                            className="p-2 rounded-lg bg-background-accent hover:bg-background-secondary transition-colors"
                            title={isMuted ? 'Unmute' : 'Mute'}
                        >
                            {isMuted ? (
                                <VolumeX className="w-4 h-4 text-voice-error" />
                            ) : (
                                <Volume2 className="w-4 h-4 text-text-secondary" />
                            )}
                        </button>
                    </div>
                </div>

                {}
                <div className="mb-8">
                    <VoiceWaveform
                        isActive={voiceState === 'listening' || voiceState === 'speaking' || isRecording}
                        amplitude={isRecording ? amplitude * 2 : voiceState === 'speaking' ? 1.2 : 0.8}
                    />
                </div>

                {}
                <motion.div
                    className="mb-6"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <button
                        onClick={handleVoiceButtonClick}
                        disabled={isInitializing || voiceState === 'processing'}
                        className={`voice-button ${getVoiceButtonState()} w-24 h-24 text-white ${isRecording ? 'animate-pulse' : ''
                            }`}
                        aria-label={getVoiceButtonText()}
                    >
                        <AnimatePresence mode="wait">
                            {voiceState === 'processing' || isInitializing ? (
                                <motion.div
                                    key="loading"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <Activity className="w-8 h-8 animate-spin" />
                                </motion.div>
                            ) : isMuted ? (
                                <motion.div
                                    key="muted"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <MicOff className="w-8 h-8" />
                                </motion.div>
                            ) : (
                                <motion.div
                                    key="mic"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <Mic className="w-8 h-8" />
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </button>
                </motion.div>

                {}
                <div className="space-y-2">
                    <h2 className={`text-lg font-semibold ${getStatusColor()}`}>
                        {getVoiceButtonText()}
                    </h2>

                    {error && (
                        <p className="text-sm text-voice-error">
                            {error}
                        </p>
                    )}

                    {voiceState === 'listening' && (
                        <p className="text-sm text-text-secondary">
                            {isRecording
                                ? "🎤 Recording... I can hear you speaking!"
                                : "I'm listening. Try saying 'I want to fill a form' or just start talking."
                            }
                        </p>
                    )}

                    {voiceState === 'speaking' && (
                        <p className="text-sm text-text-secondary">
                            Speaking... You can interrupt me anytime.
                        </p>
                    )}

                    {isConnected && voiceState === 'idle' && (
                        <p className="text-sm text-text-secondary">
                            Click the microphone to start a conversation.
                        </p>
                    )}

                    {micPermission === false && (
                        <p className="text-sm text-voice-error">
                            🚫 Microphone permission denied. Please allow access and refresh.
                        </p>
                    )}

                    {micPermission === null && (
                        <p className="text-sm text-text-secondary">
                            🎤 Microphone access will be requested when you start talking.
                        </p>
                    )}
                </div>

                {}
                {(metrics.latency > 0 || amplitude > 0) && (
                    <div className="mt-6 pt-4 border-t border-white/10">
                        <div className="flex justify-center space-x-6 text-xs text-text-secondary">
                            {metrics.latency > 0 && (
                                <div className="flex items-center space-x-1">
                                    <Clock className="w-3 h-3" />
                                    <span>{Math.round(metrics.latency)}ms latency</span>
                                </div>
                            )}
                            {amplitude > 0 && (
                                <div className="flex items-center space-x-1">
                                    <Activity className="w-3 h-3" />
                                    <span>{Math.round(amplitude * 100)}% volume</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
