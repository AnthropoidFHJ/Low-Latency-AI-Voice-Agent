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
import { useRTVIClient, VoiceClientCallbacks, NativeRTVIClient } from '../lib/rtvi-client';
import { useVoiceState, useConnectionStatus, useMetrics, usePerformanceAlerts } from '../lib/store';

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

export const RTVIVoiceInterface: React.FC = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [amplitude, setAmplitude] = useState(0);
    const [metrics, setMetrics] = useState<any>({});
    const [error, setError] = useState<string | null>(null);
    const [micPermission, setMicPermission] = useState<boolean | null>(null);

    const callbacks: VoiceClientCallbacks = {
        onConnected: () => {
            console.log('RTVI client connected');
            setIsConnected(true);
            setError(null);
        },
        onDisconnected: () => {
            console.log('RTVI client disconnected');
            setIsConnected(false);
            setIsListening(false);
            setIsProcessing(false);
        },
        onMessage: (message) => {
            console.log('RTVI message:', message);

            switch (message.type) {
                case 'rtvi-transcript':

                    break;
                case 'rtvi-audio-out':

                    setIsProcessing(false);
                    break;
            }
        },
        onAudioInput: (audio) => {

            const audioArray = new Float32Array(audio);
            const sum = audioArray.reduce((acc, val) => acc + Math.abs(val), 0);
            const avgAmplitude = sum / audioArray.length;
            setAmplitude(avgAmplitude * 10);
        },
        onAudioOutput: (audio) => {

            setIsProcessing(false);
        },
        onError: (error) => {
            console.error('RTVI error:', error);
            setError(error.message);
            setIsProcessing(false);
        },
        onMetrics: (newMetrics) => {
            setMetrics(newMetrics);
        }
    };

    const rtviClient = useRTVIClient(callbacks);

    useEffect(() => {

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(() => setMicPermission(true))
            .catch(() => setMicPermission(false));
    }, []);

    const handleConnect = async () => {
        if (!rtviClient) return;

        try {
            const success = await rtviClient.connect();
            if (!success) {
                setError('Failed to connect to voice agent');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Connection failed');
        }
    };

    const handleDisconnect = async () => {
        if (!rtviClient) return;

        try {
            await rtviClient.disconnect();
        } catch (err) {
            console.error('Disconnect error:', err);
        }
    };

    const handleVoiceToggle = async () => {
        if (!rtviClient) return;

        if (isListening) {
            try {
                await rtviClient.stopListening();
                setIsListening(false);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to stop listening');
            }
        } else {
            if (micPermission === false) {
                setError('Microphone permission required');
                return;
            }

            try {
                await rtviClient.startListening();
                setIsListening(true);
                setIsProcessing(true);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to start listening');
            }
        }
    };

    const handleOpenForm = async (formType: string) => {
        if (!rtviClient) return;

        try {
            const result = await rtviClient.openForm(formType);
            console.log('Form opened:', result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to open form');
        }
    };

    const handleGetMetrics = async () => {
        if (!rtviClient) return;

        try {
            const currentMetrics = await rtviClient.getMetrics();
            setMetrics(currentMetrics || {});
        } catch (err) {
            console.error('Failed to get metrics:', err);
        }
    };

    const getConnectionStatus = () => {
        if (isProcessing) return 'processing';
        if (isConnected) return 'connected';
        return 'disconnected';
    };

    const getStatusLabel = () => {
        if (isProcessing) return 'Processing...';
        if (isListening) return 'Listening...';
        if (isConnected) return 'Connected';
        return 'Disconnected';
    };

    return (
        <div className="rtvi-voice-interface w-full max-w-md mx-auto">
            <div className="glass-panel p-6 text-center">
                <h2 className="text-lg font-semibold mb-4 text-text-primary">
                    RTVI Voice Agent
                </h2>

                {}
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-4 p-3 bg-voice-error/10 border border-voice-error/20 rounded-lg"
                    >
                        <div className="flex items-center space-x-2 text-voice-error">
                            <AlertTriangle className="w-4 h-4" />
                            <span className="text-sm">{error}</span>
                        </div>
                    </motion.div>
                )}

                {}
                <div className="mb-6">
                    <StatusIndicator
                        status={getConnectionStatus()}
                        label={getStatusLabel()}
                    />
                </div>

                {}
                <div className="mb-8">
                    <VoiceWaveform
                        isActive={isListening || isProcessing}
                        amplitude={amplitude}
                    />
                </div>

                {}
                <div className="space-y-4">
                    {}
                    <div className="flex space-x-3">
                        <motion.button
                            onClick={isConnected ? handleDisconnect : handleConnect}
                            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${isConnected
                                    ? 'bg-voice-error hover:bg-voice-error/80 text-white'
                                    : 'bg-voice-active hover:bg-voice-active/80 text-white'
                                }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <div className="flex items-center justify-center space-x-2">
                                {isConnected ? <WifiOff className="w-4 h-4" /> : <Wifi className="w-4 h-4" />}
                                <span>{isConnected ? 'Disconnect' : 'Connect'}</span>
                            </div>
                        </motion.button>
                    </div>

                    {}
                    {isConnected && (
                        <motion.button
                            onClick={handleVoiceToggle}
                            className={`w-full py-4 px-6 rounded-lg font-medium transition-all ${isListening
                                    ? 'bg-voice-speaking hover:bg-voice-speaking/80 text-white'
                                    : 'bg-voice-idle hover:bg-voice-idle/80 text-white'
                                }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            disabled={micPermission === false}
                        >
                            <div className="flex items-center justify-center space-x-2">
                                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                                <span>{isListening ? 'Stop Listening' : 'Start Voice Chat'}</span>
                            </div>
                        </motion.button>
                    )}

                    {}
                    {isConnected && (
                        <div className="pt-4 border-t border-white/10">
                            <p className="text-xs text-text-secondary mb-3">Form Management</p>
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={() => handleOpenForm('contact')}
                                    className="py-2 px-3 text-xs bg-white/5 hover:bg-white/10 rounded transition-colors"
                                >
                                    Contact Form
                                </button>
                                <button
                                    onClick={() => handleOpenForm('feedback')}
                                    className="py-2 px-3 text-xs bg-white/5 hover:bg-white/10 rounded transition-colors"
                                >
                                    Feedback Form
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {}
                <div className="mt-6 pt-4 border-t border-white/10 text-xs">
                    {micPermission === true && (
                        <p className="text-voice-active">
                            ✅ Microphone access granted
                        </p>
                    )}

                    {micPermission === false && (
                        <p className="text-voice-error">
                            🚫 Microphone permission denied. Please allow access and refresh.
                        </p>
                    )}

                    {micPermission === null && (
                        <p className="text-text-secondary">
                            🎤 Microphone access will be requested when you connect.
                        </p>
                    )}
                </div>

                {}
                {(metrics.avg_voice_to_voice_latency_ms > 0 || amplitude > 0) && (
                    <div className="mt-6 pt-4 border-t border-white/10">
                        <div className="flex justify-center space-x-6 text-xs text-text-secondary">
                            {metrics.avg_voice_to_voice_latency_ms > 0 && (
                                <LatencyIndicator latency={metrics.avg_voice_to_voice_latency_ms} />
                            )}
                            {amplitude > 0 && (
                                <div className="flex items-center space-x-1">
                                    <Activity className="w-3 h-3" />
                                    <span>{Math.round(amplitude * 100)}% volume</span>
                                </div>
                            )}
                        </div>

                        {}
                        <button
                            onClick={handleGetMetrics}
                            className="mt-2 text-xs text-text-secondary hover:text-text-primary transition-colors"
                        >
                            Refresh Metrics
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default RTVIVoiceInterface;
