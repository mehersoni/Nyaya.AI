import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
    colors: {
        brand: {
            50: '#e6f3ff',
            100: '#b3d9ff',
            200: '#80bfff',
            300: '#4da6ff',
            400: '#1a8cff',
            500: '#0066cc', // Primary brand color
            600: '#0052a3',
            700: '#003d7a',
            800: '#002952',
            900: '#001429',
        },
        legal: {
            50: '#f7fafc',
            100: '#edf2f7',
            200: '#e2e8f0',
            300: '#cbd5e0',
            400: '#a0aec0',
            500: '#718096',
            600: '#4a5568',
            700: '#2d3748',
            800: '#1a202c',
            900: '#171923',
        }
    },
    fonts: {
        heading: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
        body: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
    },
    components: {
        Button: {
            defaultProps: {
                colorScheme: 'brand',
            },
            variants: {
                solid: {
                    _focus: {
                        boxShadow: '0 0 0 3px rgba(1, 102, 204, 0.6)',
                    },
                },
            },
        },
        Input: {
            variants: {
                outline: {
                    field: {
                        _focus: {
                            borderColor: 'brand.500',
                            boxShadow: '0 0 0 1px #0066cc',
                        },
                    },
                },
            },
        },
    },
    config: {
        initialColorMode: 'light',
        useSystemColorMode: false,
    },
});

export default theme;