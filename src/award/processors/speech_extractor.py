import re
from typing import List, Dict

from ..processor import BaseProcessor
from ..tweet import Tweet


class SpeechExtractor(BaseProcessor):
    """Extract acceptance speeches and memorable quotes from tweets."""
    
    def __init__(self):
        super().__init__(processor_type="speech extractor")
        
        # Patterns for identifying speeches and quotes
        self.speech_patterns = [
            # Direct speech/quote patterns
            r'"([^"]+)"',  # Text in quotes
            r"'([^']+)'",  # Text in single quotes
            r"(?:said|says|speaking|speech):\s*(.+)",  # Direct speech attribution
            r"(?:acceptance\s+speech|accepting\s+the\s+award):\s*(.+)",
            
            # Speech introduction patterns
            r"(?:accepts?\s+the\s+award\s+(?:and\s+)?(?:says|said)):\s*(.+)",
            r"(?:takes\s+the\s+stage\s+(?:and\s+)?(?:says|said)):\s*(.+)",
            r"(?:thank\s+you\s+speech|thank\s+you\s+message):\s*(.+)",
            
            # Quote patterns with attribution
            r"(.+?)\s+(?:says?|said|speaking|speaks?):\s*(.+)",
            r"(.+?)\s+(?:accepts?\s+the\s+award\s+and\s+)?(?:says?|said):\s*(.+)",
            r"(.+?)\s+(?:takes\s+the\s+stage\s+and\s+)?(?:says?|said):\s*(.+)",
            
            # Thank you patterns
            r"(?:thank\s+you\s+speech|thanks?|thanking):\s*(.+)",
            r"(?:grateful|appreciate|honored|blessed):\s*(.+)",
            r"(?:would\s+like\s+to\s+thank|want\s+to\s+thank):\s*(.+)",
            
            # Emotional moments
            r"(?:emotional\s+moment|tearful\s+speech|moving\s+words):\s*(.+)",
            r"(?:chokes\s+up|gets\s+emotional|becomes\s+tearful):\s*(.+)",
            
            # Memorable quotes
            r"(?:memorable\s+quote|unforgettable\s+moment):\s*(.+)",
            r"(?:steals\s+the\s+show|showstopper):\s*(.+)",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.speech_patterns]
        
        # Common speech-related keywords for context validation
        self.speech_keywords = {
            'speech', 'speaks', 'speaking', 'said', 'says', 'quote', 'quotes',
            'acceptance', 'accepting', 'accepts', 'thank', 'thanks', 'thanked',
            'grateful', 'appreciate', 'honored', 'blessed', 'emotional',
            'tearful', 'moving', 'memorable', 'unforgettable', 'chokes',
            'stage', 'award', 'takes', 'steals', 'show', 'showstopper'
        }
        
        # Common speech starters and phrases
        self.speech_starters = [
            'thank you', 'thanks', 'i would like to thank', 'i want to thank',
            'i am honored', 'i am grateful', 'i am blessed', 'i appreciate',
            'this is amazing', 'this is incredible', 'i am speechless',
            'i can\'t believe', 'i don\'t know what to say', 'wow'
        ]
        
        # Words to filter out from extracted quotes
        self.filter_words = {
            'the', 'a', 'an', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'of', 'with',
            'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that',
            'these', 'those', 'said', 'says', 'speaking', 'speech', 'acceptance',
            'award', 'awards', 'golden', 'globes', 'gg', 'stage', 'thank', 'thanks'
        }
    
    def process(self, tweet: Tweet) -> Tweet:
        """Extract speeches and quotes from tweet text and store in tweet metadata."""
        extracted_data = self.extract_speeches(tweet.text)
        
        # Store extracted data in tweet metadata
        if not hasattr(tweet, 'extracted_quotes'):
            tweet.extracted_quotes = []
        if not hasattr(tweet, 'speech_speakers'):
            tweet.speech_speakers = []
        
        tweet.extracted_quotes.extend(extracted_data['quotes'])
        tweet.speech_speakers.extend(extracted_data['speakers'])
        
        return tweet
    
    def extract_speeches(self, text: str) -> Dict[str, List[str]]:
        """Extract speeches, quotes, and speakers from text using regex patterns."""
        result = {'quotes': [], 'speakers': []}
        
        # Check if text contains speech-related context
        if not self._has_speech_context(text):
            return result
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle multiple groups (speaker and quote)
                    for i, group in enumerate(match):
                        if group and len(group.strip()) > 3:
                            cleaned_text = self._clean_quote(group.strip())
                            if i == 0 and self._looks_like_speaker_name(group.strip()):
                                # First group might be speaker name
                                result['speakers'].append(cleaned_text)
                            elif self._looks_like_quote(cleaned_text):
                                # Other groups might be quotes
                                result['quotes'].append(cleaned_text)
                else:
                    if match and len(match.strip()) > 3:
                        cleaned_text = self._clean_quote(match.strip())
                        if self._looks_like_quote(cleaned_text):
                            result['quotes'].append(cleaned_text)
        
        # Remove duplicates and filter
        result['quotes'] = list(set([q for q in result['quotes'] if self._is_valid_quote(q)]))
        result['speakers'] = list(set([s for s in result['speakers'] if self._is_valid_speaker(s)]))
        
        return result
    
    def _has_speech_context(self, text: str) -> bool:
        """Check if text contains speech-related context."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.speech_keywords)
    
    def _clean_quote(self, text: str) -> str:
        """Clean extracted quote text."""
        # Remove extra whitespace
        cleaned = ' '.join(text.split())
        
        # Remove leading/trailing punctuation but preserve internal punctuation
        cleaned = cleaned.strip('.,!?;:"')
        
        return cleaned
    
    def _looks_like_quote(self, text: str) -> bool:
        """Check if text looks like a quote or speech."""
        if not text or len(text) < 10:
            return False
        
        text_lower = text.lower()
        
        # Check for speech starters
        for starter in self.speech_starters:
            if text_lower.startswith(starter):
                return True
        
        # Check for quote indicators
        quote_indicators = [
            'thank', 'thanks', 'grateful', 'honored', 'blessed', 'appreciate',
            'amazing', 'incredible', 'speechless', 'believe', 'wow'
        ]
        
        return any(indicator in text_lower for indicator in quote_indicators)
    
    def _looks_like_speaker_name(self, text: str) -> bool:
        """Check if text looks like a speaker name."""
        if not text or len(text) > 50:  # Names shouldn't be too long
            return False
        
        # Check for name pattern (capitalized words)
        name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        name_matches = name_pattern.findall(text)
        
        # Should have 1-3 capitalized words
        return 1 <= len(name_matches) <= 3
    
    def _is_valid_quote(self, quote: str) -> bool:
        """Check if extracted text is a valid quote."""
        if not quote or len(quote) < 10:
            return False
        
        # Check if it contains mostly filter words
        words = quote.lower().split()
        if len(words) < 3:
            return False
        
        filter_word_count = sum(1 for word in words if word in self.filter_words)
        if filter_word_count > len(words) * 0.7:  # More than 70% are filter words
            return False
        
        # Should contain some meaningful content
        meaningful_words = [word for word in words if word not in self.filter_words]
        return len(meaningful_words) >= 2
    
    def _is_valid_speaker(self, speaker: str) -> bool:
        """Check if extracted text is a valid speaker name."""
        if not speaker or len(speaker) < 3 or len(speaker) > 50:
            return False
        
        # Check for name pattern
        name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        name_matches = name_pattern.findall(speaker)
        
        # Should have 1-3 capitalized words and not be mostly filter words
        if not (1 <= len(name_matches) <= 3):
            return False
        
        words = speaker.lower().split()
        filter_word_count = sum(1 for word in words if word in self.filter_words)
        return filter_word_count <= len(words) / 2
    
    def extract_thank_you_speeches(self, text: str) -> List[str]:
        """Extract specifically thank you speeches."""
        thank_you_patterns = [
            r"(?:thank\s+you|thanks?)(?:\s+speech)?:\s*(.+)",
            r"(?:would\s+like\s+to\s+thank|want\s+to\s+thank):\s*(.+)",
            r"(?:grateful\s+to|appreciate):\s*(.+)",
        ]
        
        quotes = []
        for pattern in thank_you_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = self._clean_quote(match.strip())
                if self._is_valid_quote(cleaned):
                    quotes.append(cleaned)
        
        return quotes
