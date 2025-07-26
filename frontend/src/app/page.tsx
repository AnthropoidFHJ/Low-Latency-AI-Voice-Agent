'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, MessageSquare, Settings } from 'lucide-react';
import { VoiceInterface } from '../components/VoiceInterface';
import { FormManager } from '../components/FormManager';
import { Toaster } from 'react-hot-toast';

const PerformanceStats: React.FC = () => {
    return (
        <div className="glass-panel p-4">
            <h3 className="text-sm font-medium text-text-primary mb-3 flex items-center">
                <Zap className="w-4 h-4 mr-2" />
                Performance
            </h3>
            <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                    <div className="text-text-secondary">Target Latency</div>
                    <div className="text-voice-active font-medium">&lt;500ms</div>
                </div>
                <div>
                    <div className="text-text-secondary">Connection</div>
                    <div className="text-voice-active font-medium">&lt;2s</div>
                </div>
                <div>
                    <div className="text-text-secondary">Audio Quality</div>
                    <div className="text-voice-active font-medium">HD Native</div>
                </div>
                <div>
                    <div className="text-text-secondary">Interruption</div>
                    <div className="text-voice-active font-medium">Real-time</div>
                </div>
            </div>
        </div>
    );
};

const Header: React.FC = () => {
    return (
        <motion.header
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
        >
            <div className="flex items-center justify-center mb-4">
                <Brain className="w-8 h-8 text-voice-active mr-3" />
                <h1 className="text-3xl font-bold text-gradient">
                    Ultra-Fast Voice Agent
                </h1>
            </div>
            <p className="text-text-secondary max-w-2xl mx-auto">
                Experience sub-500ms voice-to-voice AI conversation with native audio streaming,
                real-time interruption, and voice-controlled form filling powered by Google Gemini Live.
            </p>
        </motion.header>
    );
};

const Features: React.FC = () => {
    const features = [
        {
            icon: <Zap className="w-5 h-5" />,
            title: "Ultra-Low Latency",
            description: "Sub-500ms voice-to-voice response time"
        },
        {
            icon: <MessageSquare className="w-5 h-5" />,
            title: "Natural Conversation",
            description: "Real-time interruption and turn-taking"
        },
        {
            icon: <Settings className="w-5 h-5" />,
            title: "Voice-Controlled Forms",
            description: "Fill and submit forms using voice commands"
        }
    ];

    return (
        <div className="grid md:grid-cols-3 gap-4 mb-8">
            {features.map((feature, index) => (
                <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="glass-panel p-4 text-center"
                >
                    <div className="text-voice-active mb-2 flex justify-center">
                        {feature.icon}
                    </div>
                    <h3 className="font-semibold text-text-primary mb-1">
                        {feature.title}
                    </h3>
                    <p className="text-sm text-text-secondary">
                        {feature.description}
                    </p>
                </motion.div>
            ))}
        </div>
    );
};

export default function Home() {
    return (
        <div className="min-h-screen bg-background">
            {}
            <Toaster
                position="top-right"
                toastOptions={{
                    className: 'glass-panel text-text-primary',
                    style: {
                        background: 'rgba(17, 17, 17, 0.9)',
                        backdropFilter: 'blur(12px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        color: '#ffffff',
                    },
                    success: {
                        iconTheme: {
                            primary: '#10b981',
                            secondary: '#ffffff',
                        },
                    },
                    error: {
                        iconTheme: {
                            primary: '#ef4444',
                            secondary: '#ffffff',
                        },
                    },
                }}
            />

            <div className="container mx-auto px-4 py-8">
                <Header />
                <Features />

                <div className="grid lg:grid-cols-3 gap-8">
                    {}
                    <div className="lg:col-span-2">
                        <VoiceInterface />
                    </div>

                    {}
                    <div className="space-y-6">
                        {}
                        <FormManager />

                        {}
                        <PerformanceStats />

                        {}
                        <div className="glass-panel p-4">
                            <h3 className="text-sm font-medium text-text-primary mb-3">
                                Quick Help
                            </h3>
                            <div className="text-xs text-text-secondary space-y-2">
                                <div>
                                    <strong className="text-text-primary">Getting Started:</strong>
                                    <p>Click the microphone to start talking</p>
                                </div>
                                <div>
                                    <strong className="text-text-primary">Form Commands:</strong>
                                    <p>"I want to fill a contact form"</p>
                                    <p>"My name is John Smith"</p>
                                    <p>"Submit the form"</p>
                                </div>
                                <div>
                                    <strong className="text-text-primary">Interruption:</strong>
                                    <p>Start speaking anytime to interrupt</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {}
                <motion.footer
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="mt-12 text-center text-xs text-text-secondary"
                >
                    <p>
                        Powered by Pipecat Framework + Google Gemini Live API
                    </p>
                    <p className="mt-1">
                        Built for ultra-low latency voice interaction
                    </p>
                </motion.footer>
            </div>
        </div>
    );
}
