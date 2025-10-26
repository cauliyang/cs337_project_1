import re
from typing import Optional, List

from ..processor import BaseProcessor
from ..tweet import Tweet


class HostExtractor(BaseProcessor):
    """Extract award ceremony hosts from tweets."""
    
    def __init__(self):
        super().__init__(processor_type="host extractor")
        
        # Patterns for identifying hosts
        self.host_patterns = [
            # Direct host mentions
            r"(?:hosted\s+by|hosts?\s+are|hosting\s+the)\s+(.+)",
            r"(?:hosted\s+by|hosts?\s+are|hosting\s+the)\s+(.+?)(?:\s+and\s+|\s*,|\s*$)",
            r"(?:co-hosted\s+by|co-hosts?\s+are)\s+(.+)",
            r"(?:hosting|hosts?)\s+(?:the\s+)?(?:golden\s+globes?|gg)\s+(?:are\s+)?(.+)",
            r"(?:hosting|hosts?)\s+(?:tonight|tonight's)\s+(?:show\s+is\s+)?(.+)",
            
            # Host introductions
            r"(?:tonight's\s+hosts?\s+are|tonight's\s+show\s+is\s+hosted\s+by)\s+(.+)",
            r"(?:your\s+hosts?\s+for\s+tonight\s+are|your\s+hosts?\s+are)\s+(.+)",
            r"(?:introducing\s+our\s+hosts?|meet\s+our\s+hosts?)\s+(.+)",
            
            # Host actions
            r"(?:opening\s+the\s+show|kicking\s+off\s+the\s+show)\s+(.+)",
            r"(?:welcoming\s+everyone|opening\s+remarks\s+from)\s+(.+)",
            r"(?:first\s+up|starting\s+things\s+off)\s+(.+)",
            
            # Specific host references
            r"(.+?)\s+(?:is\s+hosting|will\s+host|hosts?)\s+(?:the\s+)?(?:golden\s+globes?|gg|show)",
            r"(.+?)\s+(?:takes\s+the\s+stage|opens\s+the\s+show|kicks\s+off)",
            r"(.+?)\s+(?:co-hosts?|co-hosted)\s+(?:with\s+)?(.+)",
            
            # Multiple hosts
            r"(?:hosted\s+by|hosts?\s+are)\s+(.+?)\s+and\s+(.+)",
            r"(?:hosted\s+by|hosts?\s+are)\s+(.+?)\s*,\s*(.+?)(?:\s*,\s*|\s+and\s+)",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.host_patterns]
        
        # Common host-related keywords for context validation
        self.host_keywords = {
            'host', 'hosting', 'hosted', 'co-host', 'co-hosting', 'co-hosted',
            'opening', 'welcome', 'introduce', 'stage', 'show', 'ceremony',
            'tonight', 'golden', 'globes', 'gg'
        }
        
        # Words to filter out from extracted names
        self.filter_words = {
            'the', 'a', 'an', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'of', 'with',
            'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that',
            'these', 'those', 'host', 'hosts', 'hosting', 'hosted', 'show', 'tonight',
            'golden', 'globes', 'gg', 'ceremony', 'award', 'awards', 'opening',
            'welcome', 'introducing', 'meet', 'our', 'your', 'co-host'
        }
        
        # Name pattern for validation
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
    
    def process(self, tweet: Tweet) -> Tweet:
        """Extract hosts from tweet text and store in tweet metadata."""
        extracted_hosts = self.extract_hosts(tweet.text)
        
        # Store extracted hosts in tweet metadata
        if not hasattr(tweet, 'extracted_hosts'):
            tweet.extracted_hosts = []
        
        tweet.extracted_hosts.extend(extracted_hosts)
        
        return tweet
    
    def extract_hosts(self, text: str) -> List[str]:
        """Extract host names from text using regex patterns."""
        hosts = set()  # Use set to avoid duplicates
        
        # Check if text contains host-related context
        if not self._has_host_context(text):
            return []
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle multiple groups (for co-hosts)
                    for group in match:
                        if group and len(group.strip()) > 2:
                            cleaned_hosts = self._clean_and_split_names(group.strip())
                            hosts.update(cleaned_hosts)
                else:
                    if match and len(match.strip()) > 2:
                        cleaned_hosts = self._clean_and_split_names(match.strip())
                        hosts.update(cleaned_hosts)
        
        # Filter and validate hosts
        valid_hosts = [host for host in hosts if self._is_valid_host_name(host)]
        
        return list(valid_hosts)
    
    def _has_host_context(self, text: str) -> bool:
        """Check if text contains host-related context."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.host_keywords)
    
    def _clean_and_split_names(self, text: str) -> List[str]:
        """Clean and split multiple names from text."""
        names = []
        
        # Remove extra whitespace and punctuation
        cleaned = ' '.join(text.split()).strip('.,!?;:"')
        
        # Split on common separators for multiple hosts
        parts = re.split(r'\s+and\s+|\s*,\s*|\s*&\s*|\s+with\s+', cleaned, flags=re.IGNORECASE)
        
        for part in parts:
            cleaned_name = self._clean_single_name(part.strip())
            if cleaned_name:
                names.append(cleaned_name)
        
        return names
    
    def _clean_single_name(self, name: str) -> Optional[str]:
        """Clean a single host name."""
        if not name or len(name) < 3:
            return None
        
        # Remove common suffixes and prefixes
        cleaned = re.sub(r'\s+(host|hosts|hosting|hosted|co-host|show|tonight|golden|globes|gg|ceremony)$', '', name, flags=re.IGNORECASE)
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
    
    def _is_valid_host_name(self, name: str) -> bool:
        """Check if extracted text looks like a valid host name."""
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
            r'\b(host|hosts|hosting|hosted|show|tonight|golden|globes|gg|ceremony|award|awards)\b',
            r'\b(the|a|an|and|or|for|in|on|at|to|of|with|by|from|as|is|was|are|were)\b'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                # If the name is mostly made up of these words, it's invalid
                if len(re.findall(pattern, name, re.IGNORECASE)) >= len(words) / 2:
                    return False
        
        return True
