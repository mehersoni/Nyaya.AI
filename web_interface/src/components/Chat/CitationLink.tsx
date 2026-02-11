import React from 'react';
import {
    Box,
    Text,
    Link,
    HStack,
    Icon,
    useColorModeValue,
    Tooltip,
} from '@chakra-ui/react';
import { MdOpenInNew, MdGavel } from 'react-icons/md';
import { Citation } from '../../store/slices/chatSlice';

interface CitationLinkProps {
    citation: Citation;
}

const CitationLink: React.FC<CitationLinkProps> = ({ citation }) => {
    const bg = useColorModeValue('blue.50', 'blue.900');
    const borderColor = useColorModeValue('blue.200', 'blue.700');
    const linkColor = useColorModeValue('blue.600', 'blue.300');

    const handleCitationClick = () => {
        // In a real implementation, this would navigate to the specific legal provision
        // For now, we'll just scroll to the citation or open a modal with the full text
        console.log('Citation clicked:', citation);

        // If URL is provided, open it
        if (citation.url) {
            // For internal citations, we might want to open a modal or navigate within the app
            // For external citations, open in new tab
            if (citation.url.startsWith('#')) {
                // Internal anchor link - could open a modal with full text
                // For now, just log
                console.log('Internal citation:', citation.url);
            } else {
                window.open(citation.url, '_blank', 'noopener,noreferrer');
            }
        }
    };

    const formatCitationText = () => {
        let text = citation.act;
        if (citation.section) {
            text += `, Section ${citation.section}`;
        }
        if (citation.clause) {
            text += `(${citation.clause})`;
        }
        return text;
    };

    return (
        <Box
            bg={bg}
            border="1px"
            borderColor={borderColor}
            borderRadius="md"
            p={3}
            _hover={{ borderColor: linkColor, shadow: 'sm' }}
            transition="all 0.2s"
        >
            <HStack spacing={2} align="flex-start">
                <Icon as={MdGavel} color={linkColor} mt={0.5} flexShrink={0} />
                <Box flex={1}>
                    <Tooltip label="Click to view full legal provision" placement="top">
                        <Link
                            onClick={handleCitationClick}
                            color={linkColor}
                            fontWeight="medium"
                            _hover={{ textDecoration: 'underline' }}
                            className="citation-link"
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    handleCitationClick();
                                }
                            }}
                            aria-label={`View ${formatCitationText()}`}
                        >
                            <HStack spacing={1}>
                                <Text>{formatCitationText()}</Text>
                                <Icon as={MdOpenInNew} boxSize={3} />
                            </HStack>
                        </Link>
                    </Tooltip>
                    {citation.text && (
                        <Text fontSize="sm" color="gray.600" mt={1} noOfLines={2}>
                            {citation.text}
                        </Text>
                    )}
                </Box>
            </HStack>
        </Box>
    );
};

export default CitationLink;