import React from 'react';
import { Box, Container } from '@chakra-ui/react';
import { useSelector } from 'react-redux';
import { RootState } from './store/store';
import Header from './components/Header/Header';
import ChatInterface from './components/Chat/ChatInterface';
import DisclaimerModal from './components/Disclaimer/DisclaimerModal';
import FeedbackModal from './components/Feedback/FeedbackModal';
import ReportIssueModal from './components/ReportIssue/ReportIssueModal';

function App() {
    const { disclaimerAccepted, feedbackModalOpen, reportIssueModalOpen } = useSelector(
        (state: RootState) => state.ui
    );

    return (
        <Box minH="100vh" bg="gray.50">
            <Header />
            <Container maxW="container.xl" py={4}>
                <ChatInterface />
            </Container>

            {/* Modals */}
            {!disclaimerAccepted && <DisclaimerModal />}
            {feedbackModalOpen && <FeedbackModal />}
            {reportIssueModalOpen && <ReportIssueModal />}
        </Box>
    );
}

export default App;