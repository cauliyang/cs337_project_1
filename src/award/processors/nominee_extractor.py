import re
from typing import Dict, List, Optional

from ..processor import BaseProcessor
from ..tweet import Tweet


class NomineeExtractor(BaseProcessor):
    """Extract nominees and winners from tweets using comprehensive patterns."""
    
    def __init__(self):
        super().__init__(processor_type="nominee extractor")
        
        # Patterns for winners
        self.winner_patterns = [
            # Direct winner announcements
            r"(?:winner\s+is|wins?)\s+(?:the\s+)?(.+?)(?:\s+for\s+|\s+award|\s*$)",
            r"(?:congratulations\s+to|congrats\s+to)\s+(.+?)(?:\s+for\s+|\s*$)",
            r"(?:takes\s+home|takes\s+the)\s+(?:the\s+)?(.+?)(?:\s+award|\s*$)",
            r"(?:wins\s+the\s+)?(.+?)(?:\s+for\s+best\s+|\s*award|\s*$)",
            r"(?:receives|receiving)\s+(?:the\s+)?(.+?)(?:\s+award|\s*$)",
            r"(?:award\s+goes\s+to)\s+(.+)",
            r"(?:golden\s+globe\s+goes\s+to)\s+(.+)",
            r"(?:and\s+the\s+winner\s+is)\s+(.+)",
            r"(?:presenting\s+the\s+award\s+to)\s+(.+)",
            
            # Patterns with award category
            r"(.+?)\s+wins\s+(?:best\s+|the\s+)?(.+?)(?:\s+award|\s*$)",
            r"(.+?)\s+takes\s+(?:best\s+|the\s+)?(.+?)(?:\s+award|\s*$)",
            r"(.+?)\s+receives\s+(?:best\s+|the\s+)?(.+?)(?:\s+award|\s*$)",
        ]
        
        # Patterns for nominees
        self.nominee_patterns = [
            # Direct nomination mentions
            r"(?:nominated\s+for|nomination\s+for)\s+(?:best\s+)?(.+)",
            r"(?:nominees?\s+(?:for\s+)?|nominees?\s+include)\s*(.+)",
            r"(?:up\s+for|in\s+the\s+running\s+for)\s+(?:best\s+)?(.+)",
            r"(?:contending\s+for|competing\s+for)\s+(?:best\s+)?(.+)",
            r"(?:shortlisted\s+for|finalist\s+for)\s+(?:best\s+)?(.+)",
            
            # Lists of nominees
            r"(?:nominees?\s+are|nominees?\s+include)\s+(.+)",
            r"(?:contenders?\s+are|contenders?\s+include)\s+(.+)",
            r"(?:candidates?\s+are|candidates?\s+include)\s+(.+)",
            
            # Nominee with person/entity
            r"(.+?)\s+(?:nominated\s+for|up\s+for|contending\s+for)\s+(?:best\s+)?(.+)",
            r"(.+?)\s+(?:is\s+)?(?:nominated|a\s+nominee)\s+(?:for\s+best\s+)?(.+)",
        ]
        
        # Patterns for both winners and nominees in lists
        self.list_patterns = [
            r"(?:nominees?\s+are|nominees?\s+include|contenders?\s+are)\s+(.+?)(?:\s+and\s+|\s*,?\s*$)",
            r"(?:winner\s+is|winner)\s+(.+?)(?:\s+over\s+|\s*,?\s*$)",
            r"(?:beating|defeating)\s+(.+?)(?:\s+for\s+|\s*$)",
        ]
        
        # Compile patterns for efficiency
        self.compiled_winner_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.winner_patterns]
        self.compiled_nominee_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.nominee_patterns]
        self.compiled_list_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.list_patterns]
        
        # Common name patterns for validation
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        
        # Common words to filter out from names
        self.filter_words = {
            'the', 'a', 'an', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'of', 'with',
            'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that',
            'these', 'those', 'best', 'award', 'winner', 'nominee', 'golden',
            'globe', 'globes', 'gg', 'tv', 'movie', 'film', 'series', 'actor',
            'actress', 'director', 'picture', 'drama', 'comedy', 'musical'
        }
    
    def process(self, tweet: Tweet) -> Tweet:
        """Extract nominees and winners from tweet text and store in tweet metadata."""
        extracted_data = self.extract_nominees_and_winners(tweet.text)
        
        # Store extracted data in tweet metadata
        if not hasattr(tweet, 'extracted_winners'):
            tweet.extracted_winners = []
        if not hasattr(tweet, 'extracted_nominees'):
            tweet.extracted_nominees = []
        
        tweet.extracted_winners.extend(extracted_data['winners'])
        tweet.extracted_nominees.extend(extracted_data['nominees'])
        
        return tweet
    
    def extract_nominees_and_winners(self, text: str) -> Dict[str, List[str]]:
        """Extract nominees and winners from text using regex patterns."""
        result = {'winners': [], 'nominees': []}
        
        # Extract winners
        for pattern in self.compiled_winner_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle multiple groups
                    for group in match:
                        if group and len(group.strip()) > 2:
                            cleaned = self._clean_name(group.strip())
                            if cleaned and self._is_valid_name(cleaned):
                                result['winners'].append(cleaned)
                else:
                    if match and len(match.strip()) > 2:
                        cleaned = self._clean_name(match.strip())
                        if cleaned and self._is_valid_name(cleaned):
                            result['winners'].append(cleaned)
        
        # Extract nominees
        for pattern in self.compiled_nominee_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle multiple groups
                    for group in match:
                        if group and len(group.strip()) > 2:
                            cleaned = self._clean_name(group.strip())
                            if cleaned and self._is_valid_name(cleaned):
                                result['nominees'].append(cleaned)
                else:
                    if match and len(match.strip()) > 2:
                        cleaned = self._clean_name(match.strip())
                        if cleaned and self._is_valid_name(cleaned):
                            result['nominees'].append(cleaned)
        
        # Remove duplicates
        result['winners'] = list(set(result['winners']))
        result['nominees'] = list(set(result['nominees']))
        
        return result
    
    def _clean_name(self, name: str) -> Optional[str]:
        """Clean and normalize extracted name."""
        if not name:
            return None
        
        # Remove extra whitespace
        cleaned = ' '.join(name.split())
        
        # Remove common suffixes
        cleaned = re.sub(r'\s+(award|trophy|prize|nominee|winner|for|in|the)$', '', cleaned, flags=re.IGNORECASE)
        
        # Remove leading/trailing punctuation
        cleaned = cleaned.strip('.,!?;:"')
        
        # Capitalize properly (handle names like "Daniel Day-Lewis")
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
        
        return ' '.join(capitalized_words)
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if extracted text looks like a valid name."""
        if not name or len(name) < 3:
            return False
        
        # Check if it contains mostly common filter words
        words = name.lower().split()
        if len(words) > 5:  # Too long to be a typical name
            return False
        
        filter_word_count = sum(1 for word in words if word in self.filter_words)
        if filter_word_count > len(words) / 2:  # More than half are filter words
            return False
        
        # Must contain at least one capitalized word that looks like a name
        name_matches = self.name_pattern.findall(name)
        return len(name_matches) > 0
    
    def extract_names_from_list(self, text: str) -> List[str]:
        """Extract multiple names from a list-like text."""
        names = []
        
        # Split on common separators
        parts = re.split(r'\s+and\s+|\s*,\s*|\s*&\s*', text, flags=re.IGNORECASE)
        
        for part in parts:
            cleaned = self._clean_name(part.strip())
            if cleaned and self._is_valid_name(cleaned):
                names.append(cleaned)
        
        return names