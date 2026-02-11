import React from 'react';
import {
    Box,
    Text,
    HStack,
    VStack,
    Badge,
    Button,
    useColorModeValue,
    Flex,
    Spacer,
    Icon,
    Tooltip,
    Alert,
    AlertIcon,
    AlertDescription,
} from '@chakra-ui/react';
import { useDispatch } from 'react-redux';
import { MdThumbUp, MdThumbDown, MdPerson, MdSmartToy, MdWarning } from 'react-icons/md';
import { Message } from '../../store/slices/chatSlice';
import { openFeedbackModal } from '../../store/slices/uiSlice';
import CitationLink from './CitationLink';
import ResponseDisplay from './ResponseDisplay';

interface MessageBubbleProps {
    message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    const dispatch = useDispatch();

    const userBg = useColorModeValue('brand.500', 'brand.600');
    const assistantBg = useColorModeValue('gray.100', 'gray.700');
    const userColor = 'white';
    const assistantColor = useColorModeValue('gray.800', 'white');

    const handleFeedback = (type: 'positive' | 'negative') => {
        dispatch(openFeedbackModal({ messageId: message.id, type }));
    };

    const formatTime = (date: Date) => {
        return new Date(date).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getConfidenceColor = (confidence?: number) => {
        if (!confidence) return 'gray';
        if (confidence >= 0.8) return 'green';
        if (confidence >= 0.6) return 'yellow';
        return 'red';
    };

    const getConfidenceLabel = (confidence?: number) => {
        if (!confidence) return 'Unknown';
        if (confidence >= 0.8) return 'High Confidence';
        if (confidence >= 0.6) return 'Medium Confidence';
        return 'Low Confidence';
    };

    return (
        <Flex
            justify={message.type === 'user' ? 'flex-end' : 'flex-start'}
            align="flex-start"
            w="full"
        >
            <Box maxW="80%" minW="200px">
                <HStack spacing={2} mb={2}>
                    <Icon
                        as={message.type === 'user' ? MdPerson : MdSmartToy}
                        color={message.type === 'user' ? 'brand.500' : 'gray.500'}
                    />
                    <Text fontSize="sm" color="gray.600">
                        {message.type === 'user' ? 'You' : 'Nyayamrit'}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                        {formatTime(message.timestamp)}
                    </Text>
                    {message.type === 'assistant' && message.confidence && (
                        <Badge
                            colorScheme={getConfidenceColor(message.confidence)}
                            size="sm"
                        >
                            {getConfidenceLabel(message.confidence)}
                        </Badge>
                    )}
                </HStack>

                <Box
                    bg={message.type === 'user' ? userBg : assistantBg}
                    color={message.type === 'user' ? userColor : assistantColor}
                    p={4}
                    borderRadius="lg"
                    borderTopLeftRadius={message.type === 'user' ? 'lg' : 'sm'}
                    borderTopRightRadius={message.type === 'user' ? 'sm' : 'lg'}
                    shadow="sm"
                >
                    {message.type === 'user' ? (
                        <Text>{message.content}</Text>
                    ) : (
                        <VStack spacing={3} align="stretch">
                            <ResponseDisplay content={message.content} />

                            {/* Citations */}
                            {message.citations && message.citations.length > 0 && (
                                <Box>
                                    <Text fontSize="sm" fontWeight="semibold" mb={2} color="gray.600">
                                        Legal Citations:
                                    </Text>
                                    <VStack spacing={1} align="stretch">
                                        {message.citations.map((citation) => (
                                            <CitationLink key={citation.id} citation={citation} />
                                        ))}
                                    </VStack>
                                </Box>
                            )}

                            {/* Low confidence warning */}
                            {message.requiresReview && (
                                <Alert status="warning" size="sm" borderRadius="md">
                                    <AlertIcon />
                                    <AlertDescription fontSize="sm">
                                        This response has low confidence and should be reviewed by a legal expert.
                                    </AlertDescription>
                                </Alert>
                            )}

                            {/* Feedback buttons */}
                            <Flex justify="flex-end" pt={2}>
                                <HStack spacing={2}>
                                    <Tooltip label="This response was helpful">
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            leftIcon={<MdThumbUp />}
                                            onClick={() => handleFeedback('positive')}
                                            aria-label="Mark response as helpful"
                                        >
                                            Helpful
                                        </Button>
                                    </Tooltip>
                                    <Tooltip label="This response was not helpful">
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            leftIcon={<MdThumbDown />}
                                            onClick={() => handleFeedback('negative')}
                                            aria-label="Mark response as not helpful"
                                        >
                                            Not Helpful
                                        </Button>
                                    </Tooltip>
                                </HStack>
                            </Flex>
                        </VStack>
                    )}
                </Box>
            </Box>
        </Flex>
    );
};

export default MessageBubble;