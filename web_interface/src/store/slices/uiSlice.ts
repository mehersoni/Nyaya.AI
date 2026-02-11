import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface UIState {
    sidebarOpen: boolean;
    disclaimerAccepted: boolean;
    showExampleQuestions: boolean;
    feedbackModalOpen: boolean;
    reportIssueModalOpen: boolean;
    currentFeedback: {
        messageId: string | null;
        type: 'positive' | 'negative' | null;
    };
}

const initialState: UIState = {
    sidebarOpen: false,
    disclaimerAccepted: localStorage.getItem('nyayamrit-disclaimer-accepted') === 'true',
    showExampleQuestions: true,
    feedbackModalOpen: false,
    reportIssueModalOpen: false,
    currentFeedback: {
        messageId: null,
        type: null,
    },
};

const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        toggleSidebar: (state) => {
            state.sidebarOpen = !state.sidebarOpen;
        },
        setSidebarOpen: (state, action: PayloadAction<boolean>) => {
            state.sidebarOpen = action.payload;
        },
        acceptDisclaimer: (state) => {
            state.disclaimerAccepted = true;
            localStorage.setItem('nyayamrit-disclaimer-accepted', 'true');
        },
        setShowExampleQuestions: (state, action: PayloadAction<boolean>) => {
            state.showExampleQuestions = action.payload;
        },
        openFeedbackModal: (state, action: PayloadAction<{ messageId: string; type: 'positive' | 'negative' }>) => {
            state.feedbackModalOpen = true;
            state.currentFeedback = action.payload;
        },
        closeFeedbackModal: (state) => {
            state.feedbackModalOpen = false;
            state.currentFeedback = { messageId: null, type: null };
        },
        openReportIssueModal: (state) => {
            state.reportIssueModalOpen = true;
        },
        closeReportIssueModal: (state) => {
            state.reportIssueModalOpen = false;
        },
    },
});

export const {
    toggleSidebar,
    setSidebarOpen,
    acceptDisclaimer,
    setShowExampleQuestions,
    openFeedbackModal,
    closeFeedbackModal,
    openReportIssueModal,
    closeReportIssueModal,
} = uiSlice.actions;

export default uiSlice.reducer;