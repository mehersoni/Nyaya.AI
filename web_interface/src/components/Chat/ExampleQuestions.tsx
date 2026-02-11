import React from 'react';
import {
    Box,
    Text,
    VStack,
    HStack,
    Button,
    useColorModeValue,
    Icon,
    SimpleGrid,
} from '@chakra-ui/react';
import { useDispatch, useSelector } from 'react-redux';
import { MdQuestionAnswer, MdShoppingCart, MdGavel, MdSecurity } from 'react-icons/md';
import { RootState } from '../../store/store';
import { sendQuery, addUserMessage } from '../../store/slices/chatSlice';
import { setShowExampleQuestions } from '../../store/slices/uiSlice';

interface ExampleQuestion {
    id: string;
    question: string;
    category: string;
    icon: any;
    translations: Record<string, string>;
}

const EXAMPLE_QUESTIONS: ExampleQuestion[] = [
    {
        id: 'consumer-rights',
        question: 'What are my basic consumer rights under CPA 2019?',
        category: 'Consumer Rights',
        icon: MdSecurity,
        translations: {
            hi: 'CPA 2019 के तहत मेरे मूलभूत उपभोक्ता अधिकार क्या हैं?',
            ta: 'CPA 2019 இன் கீழ் எனது அடிப்படை நுகர்வோர் உரிமைகள் என்ன?',
            te: 'CPA 2019 కింద నా ప్రాథమిక వినియోగదారు హక్కులు ఏమిటి?',
            bn: 'CPA 2019 এর অধীনে আমার মৌলিক ভোক্তা অধিকার কী?',
        }
    },
    {
        id: 'defective-product',
        question: 'What can I do if I bought a defective product?',
        category: 'Product Issues',
        icon: MdShoppingCart,
        translations: {
            hi: 'यदि मैंने कोई दोषपूर्ण उत्पाद खरीदा है तो मैं क्या कर सकता हूं?',
            ta: 'குறைபாடுள்ள பொருளை வாங்கினால் என்ன செய்யலாம்?',
            te: 'లోపభూయిష్ట ఉత్పత్తిని కొనుగోలు చేసినట్లయితే నేను ఏమి చేయగలను?',
            bn: 'আমি যদি একটি ত্রুটিপূর্ণ পণ্য কিনে থাকি তাহলে আমি কী করতে পারি?',
        }
    },
    {
        id: 'unfair-trade',
        question: 'What constitutes unfair trade practices?',
        category: 'Trade Practices',
        icon: MdGavel,
        translations: {
            hi: 'अनुचित व्यापार प्रथाओं का क्या मतलब है?',
            ta: 'நியாயமற்ற வர்த்தக நடைமுறைகள் என்றால் என்ன?',
            te: 'అన్యాయమైన వాణిజ్య పద్ధతులు అంటే ఏమిటి?',
            bn: 'অন্যায় বাণিজ্য অনুশীলন কী গঠন করে?',
        }
    },
    {
        id: 'complaint-process',
        question: 'How do I file a consumer complaint?',
        category: 'Legal Process',
        icon: MdQuestionAnswer,
        translations: {
            hi: 'मैं उपभोक्ता शिकायत कैसे दर्ज करूं?',
            ta: 'நுகர்வோர் புகார் எப்படி பதிவு செய்வது?',
            te: 'వినియోగదారు ఫిర్యాదు ఎలా దాఖలు చేయాలి?',
            bn: 'আমি কীভাবে একটি ভোক্তা অভিযোগ দায়ের করব?',
        }
    },
];

const ExampleQuestions: React.FC = () => {
    const dispatch = useDispatch();
    const { selectedLanguage, sessionId } = useSelector((state: RootState) => state.chat);

    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    const handleQuestionClick = (question: ExampleQuestion) => {
        const questionText = question.translations[selectedLanguage] || question.question;

        // Add user message
        dispatch(addUserMessage({ content: questionText, language: selectedLanguage }));

        // Hide example questions
        dispatch(setShowExampleQuestions(false));

        // Send query
        dispatch(sendQuery({
            query: questionText,
            language: selectedLanguage,
            sessionId: sessionId || undefined
        }));
    };

    const getQuestionText = (question: ExampleQuestion) => {
        return question.translations[selectedLanguage] || question.question;
    };

    return (
        <Box
            bg={bg}
            border="1px"
            borderColor={borderColor}
            borderRadius="lg"
            p={6}
            shadow="sm"
        >
            <VStack spacing={4} align="stretch">
                <Box textAlign="center">
                    <Text fontSize="lg" fontWeight="semibold" color="brand.600" mb={2}>
                        Common Questions
                    </Text>
                    <Text fontSize="sm" color="gray.600">
                        Click on any question below to get started
                    </Text>
                </Box>

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                    {EXAMPLE_QUESTIONS.map((question) => (
                        <Button
                            key={question.id}
                            variant="outline"
                            size="md"
                            h="auto"
                            p={4}
                            textAlign="left"
                            justifyContent="flex-start"
                            whiteSpace="normal"
                            onClick={() => handleQuestionClick(question)}
                            _hover={{
                                borderColor: 'brand.300',
                                bg: 'brand.50',
                            }}
                            aria-label={`Ask: ${getQuestionText(question)}`}
                        >
                            <HStack spacing={3} align="flex-start" w="full">
                                <Icon
                                    as={question.icon}
                                    color="brand.500"
                                    boxSize={5}
                                    mt={0.5}
                                    flexShrink={0}
                                />
                                <VStack spacing={1} align="flex-start" flex={1}>
                                    <Text fontSize="sm" fontWeight="medium" lineHeight="1.3">
                                        {getQuestionText(question)}
                                    </Text>
                                    <Text fontSize="xs" color="gray.500">
                                        {question.category}
                                    </Text>
                                </VStack>
                            </HStack>
                        </Button>
                    ))}
                </SimpleGrid>

                <Text fontSize="xs" color="gray.500" textAlign="center" mt={2}>
                    You can also type your own question in the input box below
                </Text>
            </VStack>
        </Box>
    );
};

export default ExampleQuestions;