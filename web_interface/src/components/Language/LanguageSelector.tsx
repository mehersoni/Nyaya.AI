import React from 'react';
import { Select, FormLabel, VStack } from '@chakra-ui/react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { setLanguage } from '../../store/slices/chatSlice';

const SUPPORTED_LANGUAGES = [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
    { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
    { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી' },
    { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
    { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം' },
    { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
    { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ' },
    { code: 'as', name: 'Assamese', nativeName: 'অসমীয়া' },
];

const LanguageSelector: React.FC = () => {
    const dispatch = useDispatch();
    const selectedLanguage = useSelector((state: RootState) => state.chat.selectedLanguage);

    const handleLanguageChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        dispatch(setLanguage(event.target.value));
    };

    return (
        <VStack spacing={1} align="stretch" minW="200px">
            <FormLabel htmlFor="language-select" fontSize="sm" mb={0} color="gray.600">
                Language / भाषा
            </FormLabel>
            <Select
                id="language-select"
                value={selectedLanguage}
                onChange={handleLanguageChange}
                size="sm"
                bg="white"
                aria-label="Select your preferred language"
            >
                {SUPPORTED_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                        {lang.nativeName} ({lang.name})
                    </option>
                ))}
            </Select>
        </VStack>
    );
};

export default LanguageSelector;