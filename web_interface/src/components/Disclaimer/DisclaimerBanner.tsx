import React from 'react';
import {
    Alert,
    AlertIcon,
    AlertDescription,
    Box,
    Text,
    Link,
    HStack,
    useColorModeValue,
} from '@chakra-ui/react';
import { MdWarning } from 'react-icons/md';

const DisclaimerBanner: React.FC = () => {
    const bg = useColorModeValue('orange.50', 'orange.900');
    const borderColor = useColorModeValue('orange.200', 'orange.700');

    return (
        <Alert
            status="warning"
            bg={bg}
            borderColor={borderColor}
            border="1px"
            borderRadius="md"
            mb={4}
        >
            <AlertIcon as={MdWarning} />
            <Box flex={1}>
                <AlertDescription fontSize="sm" lineHeight="1.5">
                    <Text as="span" fontWeight="semibold">
                        Important Disclaimer:
                    </Text>{' '}
                    Nyayamrit provides legal information, not legal advice. This system is designed to help you understand the Consumer Protection Act, 2019, but should not replace consultation with a qualified legal professional. All information is provided for educational purposes only.
                    {' '}
                    <Link
                        color="orange.600"
                        textDecoration="underline"
                        href="#full-disclaimer"
                        aria-label="Read full disclaimer"
                    >
                        Read full disclaimer
                    </Link>
                </AlertDescription>
            </Box>
        </Alert>
    );
};

export default DisclaimerBanner;