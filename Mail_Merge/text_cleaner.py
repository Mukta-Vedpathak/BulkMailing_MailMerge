import unicodedata
import re

class TextCleaner:
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text by replacing problematic characters with safe alternatives"""
        if not isinstance(text, str):
            return str(text)
        
        # Replace non-breaking space with regular space
        text = text.replace('\xa0', ' ')
        text = text.replace('\u00a0', ' ')
        
        # Replace any remaining non-ASCII characters with their closest ASCII equivalent
        text = text.encode('ascii', 'replace').decode('ascii')
        
        return text