import React from 'react';
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
    Box,
    List,
    ListItem,
    ListIcon,
    useColorModeValue,
} from '@chakra-ui/react';
import { useDispatch } from 'react-redux';
import { MdWarning, MdCheckCircle } from 'react-icons/md';
import { acceptDisclaimer } from '../../store/slices/uiSlice';

const DisclaimerModal: React.FC = () => {
    const dispatch = useDispatch();
    const bg = useColorModeValue('white', 'gray.800');

    const handleAccept = () => {
        dispatch(acceptDisclaimer());
    };

    return (
        <Modal
            isOpen={true}
            onClose={() => { }} // Cannot close without accepting
            closeOnOverlayClick={false}
            closeOnEsc={false}
            size="lg"
        >
            <ModalOverlay />
            <ModalContent bg={bg} mx={4}>
                <ModalHeader>
                    <Text fontSize="xl" fontWeight="bold" color="brand.600">
                        Welcome to Nyayamrit
                    </Text>
                    <Text fontSize="sm" color="gray.600" fontWeight="normal">
                        Legal Assistant for Indian Law
                    </Text>
                </ModalHeader>

                <ModalBody>
                    <VStack spacing={4} align="stretch">
                        <Box
                            bg="orange.50"
                            border="1px"
                            borderColor="orange.200"
                            borderRadius="md"
                            p={4}
                        >
                            <Text fontWeight="semibold" color="orange.800" mb={2}>
                                <MdWarning style={{ display: 'inline', marginRight: '8px' }} />
                                Important Legal Disclaimer
                            </Text>
                            <Text fontSize="sm" color="orange.700">
                                Please read and understand the following before using Nyayamrit.
                            </Text>
                        </Box>

                        <VStack spacing={3} align="stretch">
                            <Text fontWeight="semibold">What Nyayamrit Provides:</Text>
                            <List spacing={2}>
                                <ListItem>
                                    <ListIcon as={MdCheckCircle} color="green.500" />
                                    <Text as="span" fontSize="sm">
                                        Legal information about the Consumer Protection Act, 2019
                                    </Text>
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={MdCheckCircle} color="green.500" />
                                    <Text as="span" fontSize="sm">
                                        Citations to relevant legal provisions
                                    </Text>
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={MdCheckCircle} color="green.500" />
                                    <Text as="span" fontSize="sm">
                                        Educational explanations in simple language
                                    </Text>
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={MdCheckCircle} color="green.500" />
                                    <Text as="span" fontSize="sm">
                                        Multilingual support for better accessibility
                                    </Text>
                                </ListItem>
                            </List>
                        </VStack>

                        <VStack spacing={3} align="stretch">
                            <Text fontWeight="semibold" color="red.600">What Nyayamrit Does NOT Provide:</Text>
                            <List spacing={2}>
                                <ListItem>
                                    <ListIcon as={MdWarning} color="red.500" />
                                    <Text as="span" fontSize="sm">
                                        Legal advice or recommendations for specific situations
                                    </Text>
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={MdWarning} color="red.500" />
                                    <Text as="span" fontSize="sm">
                                        Binding legal determinations or case outcome predictions
                                    </Text>
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={MdWarning} color="red.500" />
                                    <Text as="span" fontSize="sm">
                                        Substitute for consultation with qualified legal professionals
                                    </Text>
                                </ListItem>
                                <ListItem>
                                    <ListIcon as={MdWarning} color="red.500" />
                                    <Text as="span" fontSize="sm">
                                        Guaranteed accuracy or completeness of information
                                    </Text>
                                </ListItem>
                            </List>
                        </VStack>

                        <Box
                            bg="blue.50"
                            border="1px"
                            borderColor="blue.200"
                            borderRadius="md"
                            p={4}
                        >
                            <Text fontSize="sm" color="blue.800">
                                <Text as="span" fontWeight="semibold">Remember:</Text> Always consult with a qualified lawyer for legal advice specific to your situation. Nyayamrit is an assistive tool designed to improve legal literacy and accessibility, not to replace professional legal counsel.
                            </Text>
                        </Box>

                        <Text fontSize="xs" color="gray.500">
                            By clicking "I Understand and Accept", you acknowledge that you have read and understood this disclaimer.
                        </Text>
                    </VStack>
                </ModalBody>

                <ModalFooter>
                    <Button
                        colorScheme="brand"
                        onClick={handleAccept}
                        size="lg"
                        w="full"
                        aria-label="Accept disclaimer and continue to use Nyayamrit"
                    >
                        I Understand and Accept
                    </Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

export default DisclaimerModal;