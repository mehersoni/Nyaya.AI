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
    Select,
    Input,
    HStack,
    useToast,
    Alert,
    AlertIcon,
    AlertDescription,
    Checkbox,
} from '@chakra-ui/react';
import { useDispatch } from 'react-redux';
import { closeReportIssueModal } from '../../store/slices/uiSlice';

const ReportIssueModal: React.FC = () => {
    const dispatch = useDispatch();
    const toast = useToast();

    const [issueType, setIssueType] = useState('');
    const [issueDescription, setIssueDescription] = useState('');
    const [userEmail, setUserEmail] = useState('');
    const [includeSessionData, setIncludeSessionData] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleClose = () => {
        dispatch(closeReportIssueModal());
        setIssueType('');
        setIssueDescription('');
        setUserEmail('');
        setIncludeSessionData(false);
    };

    const handleSubmit = async () => {
        if (!issueType || !issueDescription.trim()) {
            toast({
                title: 'Required Fields Missing',
                description: 'Please select an issue type and provide a description.',
                status: 'warning',
                duration: 3000,
                isClosable: true,
            });
            return;
        }

        setIsSubmitting(true);

        try {
            // In a real implementation, this would send the issue report to the backend
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call

            console.log('Issue reported:', {
                type: issueType,
                description: issueDescription,
                email: userEmail,
                includeSessionData,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href,
            });

            toast({
                title: 'Issue Reported',
                description: 'Thank you for reporting this issue. Our team will investigate and respond if needed.',
                status: 'success',
                duration: 5000,
                isClosable: true,
            });

            handleClose();
        } catch (error) {
            toast({
                title: 'Submission Failed',
                description: 'Failed to submit issue report. Please try again.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    const issueTypes = [
        { value: 'incorrect-info', label: 'Incorrect legal information' },
        { value: 'missing-citation', label: 'Missing or wrong citation' },
        { value: 'translation-error', label: 'Translation error' },
        { value: 'technical-bug', label: 'Technical bug or error' },
        { value: 'accessibility', label: 'Accessibility issue' },
        { value: 'performance', label: 'Performance problem' },
        { value: 'other', label: 'Other issue' },
    ];

    return (
        <Modal isOpen={true} onClose={handleClose} size="lg">
            <ModalOverlay />
            <ModalContent mx={4}>
                <ModalHeader>
                    <Text fontSize="lg" fontWeight="semibold">
                        Report an Issue
                    </Text>
                </ModalHeader>

                <ModalBody>
                    <VStack spacing={4} align="stretch">
                        <Alert status="info" borderRadius="md">
                            <AlertIcon />
                            <AlertDescription fontSize="sm">
                                Help us improve Nyayamrit by reporting issues you encounter. Your feedback is valuable for maintaining the quality and accuracy of legal information.
                            </AlertDescription>
                        </Alert>

                        <FormControl isRequired>
                            <FormLabel fontSize="sm">Issue Type</FormLabel>
                            <Select
                                value={issueType}
                                onChange={(e) => setIssueType(e.target.value)}
                                placeholder="Select the type of issue"
                            >
                                {issueTypes.map((type) => (
                                    <option key={type.value} value={type.value}>
                                        {type.label}
                                    </option>
                                ))}
                            </Select>
                        </FormControl>

                        <FormControl isRequired>
                            <FormLabel fontSize="sm">
                                Issue Description
                            </FormLabel>
                            <Textarea
                                value={issueDescription}
                                onChange={(e) => setIssueDescription(e.target.value)}
                                placeholder="Please describe the issue in detail. Include what you expected to happen and what actually happened."
                                rows={5}
                                resize="vertical"
                            />
                        </FormControl>

                        <FormControl>
                            <FormLabel fontSize="sm">
                                Email (optional)
                            </FormLabel>
                            <Input
                                type="email"
                                value={userEmail}
                                onChange={(e) => setUserEmail(e.target.value)}
                                placeholder="your.email@example.com"
                            />
                            <Text fontSize="xs" color="gray.500" mt={1}>
                                Provide your email if you'd like us to follow up on this issue.
                            </Text>
                        </FormControl>

                        <FormControl>
                            <Checkbox
                                isChecked={includeSessionData}
                                onChange={(e) => setIncludeSessionData(e.target.checked)}
                            >
                                <Text fontSize="sm">
                                    Include session data to help with debugging
                                </Text>
                            </Checkbox>
                            <Text fontSize="xs" color="gray.500" mt={1}>
                                This includes your recent queries and responses (but not personal information) to help our team understand the context of the issue.
                            </Text>
                        </FormControl>

                        <Alert status="warning" size="sm" borderRadius="md">
                            <AlertIcon />
                            <AlertDescription fontSize="xs">
                                <Text as="span" fontWeight="semibold">Privacy Note:</Text> We do not store personal information unless you provide your email. All issue reports are used solely for improving the system.
                            </AlertDescription>
                        </Alert>
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
                            Submit Report
                        </Button>
                    </HStack>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

export default ReportIssueModal;