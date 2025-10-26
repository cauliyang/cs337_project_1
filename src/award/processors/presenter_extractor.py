import re
from typing import List, Optional

from ..processor import BaseProcessor
from ..tweet import Tweet


class PresenterExtractor(BaseProcessor):
    """Extract award presenters from tweets."""
    
    def __init__(self):
        super().__init__(processor_type="presenter extractor")
        
        # Patterns for identifying presenters
        self.presenter_patterns = [
            # Direct presenter mentions
            r"(?:presented\s+by|presenters?\s+are|presenting)\s+(.+)",
            r"(?:presented\s+by|presenters?\s+are|presenting)\s+(.+?)(?:\s+and\s+|\s*,|\s*$)",
            r"(?:co-presented\s+by|co-presenters?\s+are)\s+(.+)",
            r"(?:presenting|presenters?)\s+(?:the\s+)?(.+?)(?:\s+award|\s*$)",
            r"(?:presenting|presenters?)\s+(?:best\s+)?(.+?)(?:\s+award|\s*$)",
            
            # Presenter introductions
            r"(?:to\s+present|will\s+present|presents?)\s+(?:the\s+)?(.+?)(?:\s+award|\s*$)",
            r"(?:introducing|meet)\s+(?:our\s+)?(?:presenters?\s+for\s+)?(.+)",
            r"(?:next\s+up\s+to\s+present|coming\s+up\s+to\s+present)\s+(.+)",
            
            # Presenter actions
            r"(.+?)\s+(?:presents?|will\s+present|presented)\s+(?:the\s+)?(.+?)(?:\s+award|\s*$)",
            r"(.+?)\s+(?:takes\s+the\s+stage\s+to\s+present|steps\s+up\s+to\s+present)\s+(.+)",
            r"(.+?)\s+(?:co-presents?|co-presented)\s+(?:with\s+)?(.+)",
            
            # Award-specific presenter mentions
            r"(?:for\s+best\s+.+?,\s+)?(.+?)\s+(?:presents?|will\s+present)",
            r"(?:the\s+.+?\s+award\s+is\s+presented\s+by)\s+(.+)",
            r"(?:presenting\s+the\s+.+?\s+award\s+is)\s+(.+)",
            
            # Multiple presenters
            r"(?:presented\s+by|presenters?\s+are)\s+(.+?)\s+and\s+(.+)",
            r"(?:presented\s+by|presenters?\s+are)\s+(.+?)\s*,\s*(.+?)(?:\s*,\s*|\s+and\s+)",
            
            # Special presentation moments
            r"(?:handing\s+out|giving\s+out)\s+(?:the\s+)?(.+?)(?:\s+award|\s*$)\s+(?:is\s+)?(.+)",
            r"(?:announcing|revealing)\s+(?:the\s+)?(.+?)(?:\s+award|\s*$)\s+(?:is\s+)?(.+)",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.presenter_patterns]
        
        # Common presenter-related keywords for context validation
        self.presenter_keywords = {
            'present', 'presents', 'presented', 'presenter', 'presenters', 'presenting',
            'co-present', 'co-presents', 'co-presented', 'co-presenter', 'co-presenters',
            'handing', 'giving', 'announcing', 'revealing', 'stage', 'award'
        }
        
        # Words to filter out from extracted names
        self.filter_words = {
            'the', 'a', 'an', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'of', 'with',
            'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that',
            'these', 'those', 'present', 'presents', 'presented', 'presenter', 'presenters',
            'presenting', 'award', 'awards', 'best', 'golden', 'globes', 'gg',
            'handing', 'giving', 'announcing', 'revealing', 'stage', 'next', 'up',
            'coming', 'introducing', 'meet', 'our', 'co-present'
        }
        
        # Name pattern for validation
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
    
    def process(self, tweet: Tweet) -> Tweet:
        """Extract presenters from tweet text and store in tweet metadata."""
        extracted_data = self.extract_presenters(tweet.text)
        
        # Store extracted data in tweet metadata
        if not hasattr(tweet, 'extracted_presenters'):
            tweet.extracted_presenters = []
        if not hasattr(tweet, 'presented_awards'):
            tweet.presented_awards = []
        
        tweet.extracted_presenters.extend(extracted_data['presenters'])
        tweet.presented_awards.extend(extracted_data['awards'])
        
        return tweet
    
    def extract_presenters(self, text: str) -> dict:
        """Extract presenter names and awards from text using regex patterns."""
        result = {'presenters': [], 'awards': []}
        
        # Check if text contains presenter-related context
        if not self._has_presenter_context(text):
            return result
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle multiple groups (presenter and award)
                    for i, group in enumerate(match):
                        if group and len(group.strip()) > 2:
                            cleaned_text = self._clean_text(group.strip())
                            if i == 0:  # First group is usually the presenter
                                cleaned_presenters = self._clean_and_split_names(cleaned_text)
                                result['presenters'].extend(cleaned_presenters)
                            else:  # Other groups might be awards
                                if self._looks_like_award(cleaned_text):
                                    result['awards'].append(cleaned_text)
                else:
                    if match and len(match.strip()) > 2:
                        cleaned_text = self._clean_text(match.strip())
                        cleaned_presenters = self._clean_and_split_names(cleaned_text)
                        result['presenters'].extend(cleaned_presenters)
        
        # Filter and validate presenters
        result['presenters'] = list(set([p for p in result['presenters'] if self._is_valid_presenter_name(p)]))
        result['awards'] = list(set(result['awards']))
        
        return result
    
    def _has_presenter_context(self, text: str) -> bool:
        """Check if text contains presenter-related context."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.presenter_keywords)
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and punctuation."""
        return ' '.join(text.split()).strip('.,!?;:"')
    
    def _clean_and_split_names(self, text: str) -> List[str]:
        """Clean and split multiple names from text."""
        names = []
        
        # Split on common separators for multiple presenters
        parts = re.split(r'\s+and\s+|\s*,\s*|\s*&\s*|\s+with\s+', text, flags=re.IGNORECASE)
        
        for part in parts:
            cleaned_name = self._clean_single_name(part.strip())
            if cleaned_name:
                names.append(cleaned_name)
        
        return names
    
    def _clean_single_name(self, name: str) -> Optional[str]:
        """Clean a single presenter name."""
        if not name or len(name) < 3:
            return None
        
        # Remove common suffixes and prefixes
        cleaned = re.sub(r'\s+(present|presents|presented|presenter|presenters|presenting|award|awards|best|golden|globes|gg|stage)$', '', name, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(the\s+|a\s+|an\s+)', '', cleaned, flags=re.IGNORECASE)
        
        # Remove leading/trailing punctuation
        cleaned = cleaned.strip('.,!?;:"')
        
        # Capitalize properly (handle names like "Tina Fey")
        words = cleaned.split()
        capitalized_words = []
        for word in words:
            if '-' in word:
                # Handle hyphenated names
                parts = word.split('-')
                capitalized_parts = [part.capitalize() for part in parts]
                capitalized_words.append('-'.join(capitalized_parts))
            else:
                capitalized_words.append(word.capitalize())
        
        result = ' '.join(capitalized_words)
        return result if result else None
    
    def _looks_like_award(self, text: str) -> bool:
        """Check if text looks like an award name."""
        text_lower = text.lower()
        award_indicators = ['best', 'award', 'golden', 'globe', 'actor', 'actress', 'director', 'picture', 'series', 'tv', 'movie', 'film']
        return any(indicator in text_lower for indicator in award_indicators)
    
    def _is_valid_presenter_name(self, name: str) -> bool:
        """Check if extracted text looks like a valid presenter name."""
        if not name or len(name) < 3:
            return False
        
        # Check if it contains mostly filter words
        words = name.lower().split()
        if len(words) > 4:  # Too long to be a typical name
            return False
        
        filter_word_count = sum(1 for word in words if word in self.filter_words)
        if filter_word_count > len(words) / 2:  # More than half are filter words
            return False
        
        # Must contain at least one capitalized word that looks like a name
        name_matches = self.name_pattern.findall(name)
        if len(name_matches) == 0:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'\b(present|presents|presented|presenter|presenters|presenting|award|awards|best|golden|globes|gg|stage)\b',
            r'\b(the|a|an|and|or|for|in|on|at|to|of|with|by|from|as|is|was|are|were)\b'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                # If the name is mostly made up of these words, it's invalid
                if len(re.findall(pattern, name, re.IGNORECASE)) >= len(words) / 2:
                    return False
        
        return True
