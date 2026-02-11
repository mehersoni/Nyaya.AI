import React from 'react';
import { Box, VStack, Flex } from '@chakra-ui/react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import ChatWindow from './ChatWindow';
import QueryInput from './QueryInput';
import ExampleQuestions from './ExampleQuestions';
import DisclaimerBanner from '../Disclaimer/DisclaimerBanner';

const ChatInterface: React.FC = () => {
    const { messages, showExampleQuestions } = useSelector((state: RootState) => ({
        messages: state.chat.messages,
        showExampleQuestions: state.ui.showExampleQuestions,
    }));

    const hasMessages = messages.length > 0;

    return (
        <Flex direction="column" h="calc(100vh - 120px)" maxH="800px">
            {/* Disclaimer Banner */}
            <DisclaimerBanner />

            {/* Main Chat Area */}
            <VStack spacing={4} flex={1} align="stretch">
                {/* Example Questions - shown when no messages */}
                {!hasMessages && showExampleQuestions && (
                    <Box>
                        <ExampleQuestions />
                    </Box>
                )}

                {/* Chat Window */}
                <Box flex={1} minH={0}>
                    <ChatWindow />
                </Box>

                {/* Query Input */}
                <Box>
                    <QueryInput />
                </Box>
            </VStack>
        </Flex>
    );
};

export default ChatInterface;