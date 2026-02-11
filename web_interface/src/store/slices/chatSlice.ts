import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export interface Citation {
    id: string;
    text: string;
    section: string;
    clause?: string;
    act: string;
    url?: string;
}

export interface Message {
    id: string;
    type: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    citations?: Citation[];
    confidence?: number;
    requiresReview?: boolean;
    language: string;
    originalLanguage?: string;
}

export interface ChatState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    sessionId: string | null;
    selectedLanguage: string;
    conversationHistory: Message[];
}

const initialState: ChatState = {
    messages: [],
    isLoading: false,
    error: null,
    sessionId: null,
    selectedLanguage: 'en',
    conversationHistory: [],
};

// Async thunk for sending queries to the backend
export const sendQuery = createAsyncThunk(
    'chat/sendQuery',
    async (payload: { query: string; language: string; sessionId?: string }) => {
        // This will be implemented when the backend is ready
        // For now, return a mock response
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay

        return {
            response: `This is a mock response to: "${payload.query}". The actual implementation will connect to the GraphRAG backend to provide accurate legal information from the Consumer Protection Act, 2019.`,
            citations: [
                {
                    id: 'cpa2019_2_1',
                    text: 'Consumer Protection Act, 2019, Section 2(1)',
                    section: '2',
                    clause: '1',
                    act: 'Consumer Protection Act, 2019',
                    url: '#section-2-1'
                }
            ] as Citation[],
            confidence: 0.85,
            requiresReview: false,
            sessionId: payload.sessionId || 'mock-session-' + Date.now(),
        };
    }
);

const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        setLanguage: (state, action: PayloadAction<string>) => {
            state.selectedLanguage = action.payload;
        },
        clearMessages: (state) => {
            state.messages = [];
            state.conversationHistory = [];
        },
        addUserMessage: (state, action: PayloadAction<{ content: string; language: string }>) => {
            const message: Message = {
                id: Date.now().toString(),
                type: 'user',
                content: action.payload.content,
                timestamp: new Date(),
                language: action.payload.language,
            };
            state.messages.push(message);
            state.conversationHistory.push(message);
        },
        clearError: (state) => {
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(sendQuery.pending, (state) => {
                state.isLoading = true;
                state.error = null;
            })
            .addCase(sendQuery.fulfilled, (state, action) => {
                state.isLoading = false;
                state.sessionId = action.payload.sessionId;

                const assistantMessage: Message = {
                    id: Date.now().toString(),
                    type: 'assistant',
                    content: action.payload.response,
                    timestamp: new Date(),
                    citations: action.payload.citations,
                    confidence: action.payload.confidence,
                    requiresReview: action.payload.requiresReview,
                    language: state.selectedLanguage,
                };

                state.messages.push(assistantMessage);
                state.conversationHistory.push(assistantMessage);
            })
            .addCase(sendQuery.rejected, (state, action) => {
                state.isLoading = false;
                state.error = action.error.message || 'Failed to send query';
            });
    },
});

export const { setLanguage, clearMessages, addUserMessage, clearError } = chatSlice.actions;
export default chatSlice.reducer;