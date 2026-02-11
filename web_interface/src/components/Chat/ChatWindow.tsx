import React, { useEffect, useRef } from 'react';
import {
    Box,
    VStack,
    Text,
    Spinner,
    Center,
    useColorModeValue,
} from '@chakra-ui/react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import MessageBubble from './MessageBubble';

const ChatWindow: React.FC = () => {
    const { messages, isLoading } = useSelector((state: RootState) => state.chat);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <Box
            bg={bg}
            border="1px"
            borderColor={borderColor}
            borderRadius="lg"
            h="full"
            overflow="hidden"
            display="flex"
            flexDirection="column"
        >
            <Box
                flex={1}
                overflowY="auto"
                p={4}
                css={{
                    '&::-webkit-scrollbar': {
                        width: '8px',
                    },
                    '&::-webkit-scrollbar-track': {
                        background: '#f1f1f1',
                        borderRadius: '4px',
                    },
                    '&::-webkit-scrollbar-thumb': {
                        background: '#c1c1c1',
                        borderRadius: '4px',
                    },
                    '&::-webkit-scrollbar-thumb:hover': {
                        background: '#a8a8a8',
                    },
                }}
            >
                {messages.length === 0 ? (
                    <Center h="full">
                        <Text color="gray.500" textAlign="center">
                            Welcome to Nyayamrit! Ask me any question about the Consumer Protection Act, 2019.
                            <br />
                            <Text as="span" fontSize="sm">
                                I'll provide accurate information with proper citations.
                            </Text>
                        </Text>
                    </Center>
                ) : (
                    <VStack spacing={4} align="stretch">
                        {messages.map((message) => (
                            <MessageBubble key={message.id} message={message} />
                        ))}
                        {isLoading && (
                            <Center py={4}>
                                <Spinner size="md" color="brand.500" />
                                <Text ml={3} color="gray.600">
                                    Searching legal provisions...
                                </Text>
                            </Center>
                        )}
                    </VStack>
                )}
                <div ref={messagesEndRef} />
            </Box>
        </Box>
    );
};

export default ChatWindow;