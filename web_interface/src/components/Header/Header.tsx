import React from 'react';
import {
    Box,
    Flex,
    Heading,
    Spacer,
    Button,
    useColorModeValue,
    HStack,
    Text,
    Icon,
} from '@chakra-ui/react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { openReportIssueModal } from '../../store/slices/uiSlice';
import LanguageSelector from '../Language/LanguageSelector';
import { MdGavel, MdReport } from 'react-icons/md';

const Header: React.FC = () => {
    const dispatch = useDispatch();
    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    const handleReportIssue = () => {
        dispatch(openReportIssueModal());
    };

    return (
        <Box
            bg={bg}
            borderBottom="1px"
            borderColor={borderColor}
            px={4}
            py={3}
            shadow="sm"
        >
            <Flex align="center" maxW="container.xl" mx="auto">
                <HStack spacing={3}>
                    <Icon as={MdGavel} boxSize={8} color="brand.500" />
                    <Box>
                        <Heading size="lg" color="brand.600">
                            Nyayamrit
                        </Heading>
                        <Text fontSize="sm" color="gray.600">
                            Legal Assistant for Indian Law
                        </Text>
                    </Box>
                </HStack>

                <Spacer />

                <HStack spacing={4}>
                    <LanguageSelector />
                    <Button
                        leftIcon={<MdReport />}
                        variant="outline"
                        size="sm"
                        onClick={handleReportIssue}
                        aria-label="Report an issue with the system"
                    >
                        Report Issue
                    </Button>
                </HStack>
            </Flex>
        </Box>
    );
};

export default Header;