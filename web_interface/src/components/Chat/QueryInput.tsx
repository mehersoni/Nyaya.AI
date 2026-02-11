import React, { useState, useRef } from 'react';
import {
    Box,
    Input,
    Button,
    HStack,
    useColorModeValue,
    Textarea,
    IconButton,
    Tooltip,
    Text,
} from '@chakra-ui/react';
import { useDispatch, useSelector } from 'react-redux';
import { MdSend, MdMic, MdMicOff } from 'react-icons/md';
import { RootState } from '../../store/store';
import { sendQuery, addUserMessage } from '../../store/slices/chatSlice';
import { setShowExampleQuestions } from '../../store/slices/uiSlice';

const QueryInput: React.FC = () => {
    const dispatch = useDispatch();
    const { isLoading, selectedLanguage, sessionId } = useSelector((state: RootState) => state.chat);

    const [query, setQuery] = useState('');
    const [isListening, setIsListening] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!query.trim() || isLoading) return;

        const trimmedQuery = query.trim();

        // Add user message to chat
        dispatch(addUserMessage({ content: trimmedQuery, language: selectedLanguage }));

        // Hide example questions after first query
        dispatch(setShowExampleQuestions(false));

        // Clear input
        setQuery('');

        // Send query to backend
        dispatch(sendQuery({
            query: trimmedQuery,
            language: selectedLanguage,
            sessionId: sessionId || undefined
        }));
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleVoiceInput = () => {
        // Voice input functionality would be implemented here
        // For now, just toggle the listening state
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            setIsListening(!isListening);
            // TODO: Implement actual speech recognition
            console.log('Voice input toggled:', !isListening);
        } else {
            alert('Speech recognition is not supported in your browser.');
        }
    };

    const getPlaceholder = () => {
        const placeholders = {
            en: 'Ask about your consumer rights under CPA 2019...',
            hi: 'उपभोक्ता संरक्षण अधिनियम 2019 के तहत अपने अधिकारों के बारे में पूछें...',
            ta: 'CPA 2019 இன் கீழ் உங்கள் நுகர்வோர் உரிமைகளைப் பற்றி கேளுங்கள்...',
            te: 'CPA 2019 కింద మీ వినియోగదారు హక్కుల గురించి అడగండి...',
            bn: 'CPA 2019 এর অধীনে আপনার ভোক্তা অধিকার সম্পর্কে জিজ্ঞাসা করুন...',
            mr: 'CPA 2019 अंतर्गत आपल्या ग्राहक हक्कांबद्दल विचारा...',
            gu: 'CPA 2019 હેઠળ તમારા ગ્રાહક અધિકારો વિશે પૂછો...',
            kn: 'CPA 2019 ರ ಅಡಿಯಲ್ಲಿ ನಿಮ್ಮ ಗ್ರಾಹಕ ಹಕ್ಕುಗಳ ಬಗ್ಗೆ ಕೇಳಿ...',
            ml: 'CPA 2019 പ്രകാരം നിങ്ങളുടെ ഉപഭോക്തൃ അവകാശങ്ങളെക്കുറിച്ച് ചോദിക്കുക...',
            pa: 'CPA 2019 ਦੇ ਤਹਿਤ ਆਪਣੇ ਖਪਤਕਾਰ ਅਧਿਕਾਰਾਂ ਬਾਰੇ ਪੁੱਛੋ...',
            or: 'CPA 2019 ଅଧୀନରେ ଆପଣଙ୍କର ଗ୍ରାହକ ଅଧିକାର ବିଷୟରେ ପଚାରନ୍ତୁ...',
            as: 'CPA 2019 ৰ অধীনত আপোনাৰ গ্ৰাহক অধিকাৰৰ বিষয়ে সোধক...',
        };
        return placeholders[selectedLanguage as keyof typeof placeholders] || placeholders.en;
    };

    return (
        <Box
            bg={bg}
            border="1px"
            borderColor={borderColor}
            borderRadius="lg"
            p={4}
            shadow="sm"
        >
            <form onSubmit={handleSubmit}>
                <HStack spacing={3} align="flex-end">
                    <Box flex={1}>
                        <Textarea
                            ref={textareaRef}
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={getPlaceholder()}
                            resize="none"
                            minH="60px"
                            maxH="120px"
                            disabled={isLoading}
                            aria-label="Enter your legal question"
                            _focus={{
                                borderColor: 'brand.500',
                                boxShadow: '0 0 0 1px #0066cc',
                            }}
                        />
                        <Text fontSize="xs" color="gray.500" mt={1}>
                            Press Enter to send, Shift+Enter for new line
                        </Text>
                    </Box>

                    <HStack spacing={2}>
                        <Tooltip label={isListening ? 'Stop voice input' : 'Start voice input'}>
                            <IconButton
                                aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
                                icon={isListening ? <MdMicOff /> : <MdMic />}
                                variant="outline"
                                colorScheme={isListening ? 'red' : 'gray'}
                                onClick={handleVoiceInput}
                                disabled={isLoading}
                            />
                        </Tooltip>

                        <Button
                            type="submit"
                            leftIcon={<MdSend />}
                            colorScheme="brand"
                            isLoading={isLoading}
                            loadingText="Sending"
                            disabled={!query.trim() || isLoading}
                            aria-label="Send your question"
                        >
                            Send
                        </Button>
                    </HStack>
                </HStack>
            </form>
        </Box>
    );
};

export default QueryInput;