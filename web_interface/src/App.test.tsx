import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { ChakraProvider } from '@chakra-ui/react';
import { configureStore } from '@reduxjs/toolkit';
import App from './App';
import chatReducer from './store/slices/chatSlice';
import uiReducer from './store/slices/uiSlice';
import theme from './theme/theme';

// Create a test store
const createTestStore = (initialState = {}) => {
    return configureStore({
        reducer: {
            chat: chatReducer,
            ui: uiReducer,
        },
        preloadedState: initialState,
    });
};

const renderWithProviders = (
    ui: React.ReactElement,
    {
        initialState = {},
        store = createTestStore(initialState),
        ...renderOptions
    } = {}
) => {
    const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
        <Provider store={store}>
            <ChakraProvider theme={theme}>
                {children}
            </ChakraProvider>
        </Provider>
    );

    return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
};

describe('App Component', () => {
    test('renders Nyayamrit header', () => {
        renderWithProviders(<App />);
        expect(screen.getByText('Nyayamrit')).toBeInTheDocument();
        expect(screen.getByText('Legal Assistant for Indian Law')).toBeInTheDocument();
    });

    test('shows disclaimer modal when not accepted', () => {
        const initialState = {
            ui: {
                disclaimerAccepted: false,
                sidebarOpen: false,
                showExampleQuestions: true,
                feedbackModalOpen: false,
                reportIssueModalOpen: false,
                currentFeedback: { messageId: null, type: null },
            },
        };

        renderWithProviders(<App />, { initialState });
        expect(screen.getByText('Welcome to Nyayamrit')).toBeInTheDocument();
        expect(screen.getByText('Important Legal Disclaimer')).toBeInTheDocument();
    });

    test('shows chat interface when disclaimer is accepted', () => {
        const initialState = {
            ui: {
                disclaimerAccepted: true,
                sidebarOpen: false,
                showExampleQuestions: true,
                feedbackModalOpen: false,
                reportIssueModalOpen: false,
                currentFeedback: { messageId: null, type: null },
            },
            chat: {
                messages: [],
                isLoading: false,
                error: null,
                sessionId: null,
                selectedLanguage: 'en',
                conversationHistory: [],
            },
        };

        renderWithProviders(<App />, { initialState });
        expect(screen.getByText('Common Questions')).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Ask about your consumer rights/)).toBeInTheDocument();
    });

    test('displays language selector', () => {
        const initialState = {
            ui: { disclaimerAccepted: true },
            chat: { selectedLanguage: 'en' },
        };

        renderWithProviders(<App />, { initialState });
        expect(screen.getByLabelText('Select your preferred language')).toBeInTheDocument();
    });

    test('displays report issue button', () => {
        const initialState = {
            ui: { disclaimerAccepted: true },
        };

        renderWithProviders(<App />, { initialState });
        expect(screen.getByLabelText('Report an issue with the system')).toBeInTheDocument();
    });
});