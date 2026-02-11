import React, { useState } from 'react';
import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Button,
    Text,
    VStack,
    Textarea,
    FormControl,
    FormLabel,
    RadioGroup,
    Radio,
    HStack,
    useToast,
    Alert,
    AlertIcon,
    AlertDescription,
} from '@chakra-ui/react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { closeFeedbackModal } from '../../store/slices/uiSlice';

const FeedbackModal: React.FC = () => {
    const dispatch = useDispatch();
    const toast = useToast();
    const { currentFeedback } = useSelector((state: RootState) => state.ui);

    const [feedbackText, setFeedbackText] = useState('');
    const [feedbackCategory, setFeedbackCategory] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleClose = () => {
        dispatch(closeFeedbackModal());
        setFeedbackText('');
        setFeedbackCategory('');
    };

    const handleSubmit = async () => {
        if (!feedbackText.trim()) {
            toast({
                title: 'Feedback Required',
                description: 'Please provide your feedback before submitting.',
                status: 'warning',
                duration: 3000,
                isClosable: true,
            });
            return;
        }

        setIsSubmitting(true);

        try {
            // In a real implementation, this would send feedback to the backend
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call

            console.log('Feedback submitted:', {
                messageId: currentFeedback.messageId,
                type: currentFeedback.type,
                category: feedbackCategory,
                text: feedbackText,
                timestamp: new Date().toISOString(),
            });

            toast({
                title: 'Feedback Submitted',
                description: 'Thank you for your feedback! It helps us improve Nyayamrit.',
                status: 'success',
                duration: 5000,
                isClosable: true,
            });

            handleClose();
        } catch (error) {
            toast({
                title: 'Submission Failed',
                description: 'Failed to submit feedback. Please try again.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    const getFeedbackTitle = () => {
        return currentFeedback.type === 'positive'
            ? 'Tell us what was helpful'
            : 'Help us improve';
    };

    const getFeedbackDescription = () => {
        return currentFeedback.type === 'positive'
            ? 'We\'re glad this response was helpful! Please let us know what worked well.'
            : 'We\'re sorry this response wasn\'t helpful. Please tell us how we can improve.';
    };

    const getCategoryOptions = () => {
        if (currentFeedback.type === 'positive') {
            return [
                { value: 'accurate', label: 'Information was accurate' },
                { value: 'clear', label: 'Explanation was clear' },
                { value: 'citations', label: 'Citations were helpful' },
                { value: 'comprehensive', label: 'Response was comprehensive' },
                { value: 'other', label: 'Other' },
            ];
        } else {
            return [
                { value: 'inaccurate', label: 'Information was inaccurate' },
                { value: 'unclear', label: 'Explanation was unclear' },
                { value: 'incomplete', label: 'Response was incomplete' },
                { value: 'irrelevant', label: 'Response was not relevant' },
                { value: 'citations', label: 'Citations were missing or wrong' },
                { value: 'other', label: 'Other' },
            ];
        }
    };

    return (
        <Modal isOpen={true} onClose={handleClose} size="lg">
            <ModalOverlay />
            <ModalContent mx={4}>
                <ModalHeader>
                    <Text fontSize="lg" fontWeight="semibold">
                        {getFeedbackTitle()}
                    </Text>
                </ModalHeader>

                <ModalBody>
                    <VStack spacing={4} align="stretch">
                        <Alert
                            status={currentFeedback.type === 'positive' ? 'success' : 'info'}
                            borderRadius="md"
                        >
                            <AlertIcon />
                            <AlertDescription fontSize="sm">
                                {getFeedbackDescription()}
                            </AlertDescription>
                        </Alert>

                        <FormControl>
                            <FormLabel fontSize="sm">What specifically would you like to mention?</FormLabel>
                            <RadioGroup value={feedbackCategory} onChange={setFeedbackCategory}>
                                <VStack spacing={2} align="stretch">
                                    {getCategoryOptions().map((option) => (
                                        <Radio key={option.value} value={option.value} size="sm">
                                            <Text fontSize="sm">{option.label}</Text>
                                        </Radio>
                                    ))}
                                </VStack>
                            </RadioGroup>
                        </FormControl>

                        <FormControl>
                            <FormLabel fontSize="sm">
                                Additional comments (optional)
                            </FormLabel>
                            <Textarea
                                value={feedbackText}
                                onChange={(e) => setFeedbackText(e.target.value)}
                                placeholder="Please provide any additional details that would help us improve..."
                                rows={4}
                                resize="vertical"
                            />
                        </FormControl>

                        <Text fontSize="xs" color="gray.500">
                            Your feedback is anonymous and helps us improve the quality of legal information provided by Nyayamrit.
                        </Text>
                    </VStack>
                </ModalBody>

                <ModalFooter>
                    <HStack spacing={3}>
                        <Button variant="outline" onClick={handleClose}>
                            Cancel
                        </Button>
                        <Button
                            colorScheme="brand"
                            onClick={handleSubmit}
                            isLoading={isSubmitting}
                            loadingText="Submitting"
                        >
                            Submit Feedback
                        </Button>
                    </HStack>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

export default FeedbackModal;