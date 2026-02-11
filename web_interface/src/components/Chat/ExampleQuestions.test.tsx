import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { ChakraProvider } from '@chakra-ui/react';
import { configureStore } from '@reduxjs/toolkit';
import ExampleQuestions from './ExampleQuestions';
import chatReducer from '../../store/slices/chatSlice';
import uiReducer from '../../store/slices/uiSlice';
import theme from '../../theme/theme';

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

describe('ExampleQuestions Component', () => {
    const initialState = {
        chat: {
            messages: [],
            isLoading: false,
            error: null,
            sessionId: null,
            selectedLanguage: 'en',
            conversationHistory: [],
        },
        ui: {
            disclaimerAccepted: true,
            showExampleQuestions: true,
        },
    };

    test('renders example questions', () => {
        renderWithProviders(<ExampleQuestions />, { initialState });

        expect(screen.getByText('Common Questions')).toBeInTheDocument();
        expect(screen.getByText('What are my basic consumer rights under CPA 2019?')).toBeInTheDocument();
        expect(screen.getByText('What can I do if I bought a defective product?')).toBeInTheDocument();
        expect(screen.getByText('What constitutes unfair trade practices?')).toBeInTheDocument();
        expect(screen.getByText('How do I file a consumer complaint?')).toBeInTheDocument();
    });

    test('shows questions in selected language', () => {
        const hindiState = {
            ...initialState,
            chat: {
                ...initialState.chat,
                selectedLanguage: 'hi',
            },
        };

        renderWithProviders(<ExampleQuestions />, { initialState: hindiState });

        expect(screen.getByText('CPA 2019 के तहत मेरे मूलभूत उपभोक्ता अधिकार क्या हैं?')).toBeInTheDocument();
    });

    test('clicking a question dispatches actions', () => {
        const store = createTestStore(initialState);
        renderWithProviders(<ExampleQuestions />, { store });

        const questionButton = screen.getByText('What are my basic consumer rights under CPA 2019?');
        fireEvent.click(questionButton);

        const state = store.getState();
        expect(state.chat.messages).toHaveLength(1);
        expect(state.chat.messages[0].content).toBe('What are my basic consumer rights under CPA 2019?');
        expect(state.ui.showExampleQuestions).toBe(false);
    });

    test('displays category labels', () => {
        renderWithProviders(<ExampleQuestions />, { initialState });

        expect(screen.getByText('Consumer Rights')).toBeInTheDocument();
        expect(screen.getByText('Product Issues')).toBeInTheDocument();
        expect(screen.getByText('Trade Practices')).toBeInTheDocument();
        expect(screen.getByText('Legal Process')).toBeInTheDocument();
    });

    test('has proper accessibility attributes', () => {
        renderWithProviders(<ExampleQuestions />, { initialState });

        const firstQuestion = screen.getByLabelText(/Ask: What are my basic consumer rights/);
        expect(firstQuestion).toBeInTheDocument();
        expect(firstQuestion.tagName).toBe('BUTTON');
    });
});