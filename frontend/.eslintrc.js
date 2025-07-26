module.exports = {
    content: ['./src*.{js,ts,jsx,tsx,mdx}'],
    extends: [
        'next/core-web-vitals',
        'next/typescript'
    ],
    rules: {

        'import/no-unused-modules': 'warn',
        'react-hooks/exhaustive-deps': 'warn',

        '@typescript-eslint/no-unused-vars': ['warn', {
            'argsIgnorePattern': '^_',
            'varsIgnorePattern': '^_'
        }],

        'no-console': ['warn', {
            'allow': ['warn', 'error', 'info']
        }],
    }
};
