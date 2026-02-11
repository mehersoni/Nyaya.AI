import React from 'react';
import { Box, Text } from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';

interface ResponseDisplayProps {
    content: string;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({ content }) => {
    // Custom components for markdown rendering
    const components = {
        p: ({ children }: any) => (
            <Text mb={2} lineHeight="1.6">
                {children}
            </Text>
        ),
        strong: ({ children }: any) => (
            <Text as="strong" fontWeight="bold">
                {children}
            </Text>
        ),
        em: ({ children }: any) => (
            <Text as="em" fontStyle="italic">
                {children}
            </Text>
        ),
        blockquote: ({ children }: any) => (
            <Box
                borderLeft="4px solid"
                borderColor="brand.200"
                pl={4}
                py={2}
                my={2}
                bg="gray.50"
                borderRadius="md"
                fontStyle="italic"
            >
                {children}
            </Box>
        ),
        code: ({ children }: any) => (
            <Text
                as="code"
                bg="gray.100"
                px={1}
                py={0.5}
                borderRadius="sm"
                fontSize="sm"
                fontFamily="mono"
            >
                {children}
            </Text>
        ),
        ul: ({ children }: any) => (
            <Box as="ul" pl={4} mb={2}>
                {children}
            </Box>
        ),
        ol: ({ children }: any) => (
            <Box as="ol" pl={4} mb={2}>
                {children}
            </Box>
        ),
        li: ({ children }: any) => (
            <Text as="li" mb={1}>
                {children}
            </Text>
        ),
    };

    // Process content to highlight legal text in quotes
    const processContent = (text: string) => {
        // This regex finds text within quotes and marks it as legal text
        return text.replace(
            /"([^"]+)"/g,
            '<blockquote>**Legal Text:** "$1"</blockquote>'
        );
    };

    return (
        <Box>
            <ReactMarkdown components={components}>
                {processContent(content)}
            </ReactMarkdown>
        </Box>
    );
};

export default ResponseDisplay;