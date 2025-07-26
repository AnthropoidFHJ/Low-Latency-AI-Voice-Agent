module.exports = {
    content: [
        './src/pages*.{js,ts,jsx,tsx,mdx}',
        './src/components*.{js,ts,jsx,tsx,mdx}',
        './src/app*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {

                background: {
                    DEFAULT: '#0a0a0a',
                    secondary: '#111111',
                    accent: '#1a1a1a',
                },
                text: {
                    primary: '#ffffff',
                    secondary: '#a1a1aa',
                    accent: '#fbbf24',
                },
                voice: {
                    active: '#10b981',
                    inactive: '#6b7280',
                    speaking: '#f59e0b',
                    listening: '#3b82f6',
                    error: '#ef4444',
                },
                form: {
                    bg: '#1f2937',
                    border: '#374151',
                    focus: '#3b82f6',
                    success: '#10b981',
                    error: '#ef4444',
                },
                border: {
                    DEFAULT: '#374151',
                },
            },
            animation: {
                'pulse-soft': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'bounce-gentle': 'bounce 1s ease-in-out infinite',
                'fade-in': 'fadeIn 0.3s ease-in-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'voice-wave': 'voiceWave 1.2s ease-in-out infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(10px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                voiceWave: {
                    '0%, 100%': { transform: 'scaleY(1)' },
                    '50%': { transform: 'scaleY(1.5)' },
                }
            },
            boxShadow: {
                'voice-active': '0 0 20px rgba(16, 185, 129, 0.5)',
                'voice-speaking': '0 0 25px rgba(245, 158, 11, 0.6)',
                'voice-listening': '0 0 20px rgba(59, 130, 246, 0.5)',
                'form-focus': '0 0 0 3px rgba(59, 130, 246, 0.1)',
            },
            backdropBlur: {
                xs: '2px',
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
    ],
};
