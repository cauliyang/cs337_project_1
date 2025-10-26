import re
from typing import List, Dict

from ..processor import BaseProcessor
from ..tweet import Tweet


class FashionExtractor(BaseProcessor):
    """Extract fashion and red carpet information from tweets."""
    
    def __init__(self):
        super().__init__(processor_type="fashion extractor")
        
        # Patterns for identifying fashion-related content
        self.fashion_patterns = [
            # Red carpet patterns
            r"(?:red\s+carpet|redcarpet)\s+(?:look|looks|style|fashion):\s*(.+)",
            r"(?:arrives?\s+at|arriving\s+at|on\s+the\s+red\s+carpet)\s+(?:wearing|in)\s+(.+)",
            r"(?:wearing|wears?|sporting|sports?)\s+(.+)",
            r"(?:dressed\s+in|outfit|ensemble):\s*(.+)",
            
            # Designer and brand mentions
            r"(?:designed\s+by|designer|couture):\s*(.+)",
            r"(?:by\s+)?(.+?)\s+(?:dress|gown|suit|tuxedo|outfit)",
            r"(?:wearing|wears?)\s+(?:a\s+)?(.+?)(?:\s+dress|\s+gown|\s+suit|\s+tuxedo)",
            
            # Fashion descriptions
            r"(?:stunning|gorgeous|beautiful|elegant|chic|fabulous|amazing)\s+(?:in\s+)?(.+)",
            r"(?:looks?\s+(?:stunning|gorgeous|beautiful|elegant|chic|fabulous|amazing))\s+(?:in\s+)?(.+)",
            r"(?:fashion\s+forward|trendy|stylish):\s*(.+)",
            
            # Color and style descriptions
            r"(?:in\s+)?(.+?)\s+(?:dress|gown|suit|tuxedo|outfit|ensemble)",
            r"(?:color|colored)\s+(?:in\s+)?(.+)",
            r"(?:style|styled)\s+(?:in\s+)?(.+)",
            
            # Accessories and details
            r"(?:accessorized\s+with|accessories?):\s*(.+)",
            r"(?:jewelry|jewels?|necklace|earrings|bracelet|ring):\s*(.+)",
            r"(?:shoes?|heels?|boots?):\s*(.+)",
            r"(?:hair|hairstyle|makeup|make-up):\s*(.+)",
            
            # Fashion events and moments
            r"(?:fashion\s+moment|style\s+moment|best\s+dressed):\s*(.+)",
            r"(?:worst\s+dressed|fashion\s+fail):\s*(.+)",
            r"(?:trend|trending|viral)\s+(?:fashion|style):\s*(.+)",
            
            # Celebrity fashion
            r"(.+?)\s+(?:fashion|style|look|outfit):\s*(.+)",
            r"(.+?)\s+(?:rocks?|pulls\s+off)\s+(.+)",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.fashion_patterns]
        
        # Common fashion-related keywords for context validation
        self.fashion_keywords = {
            'fashion', 'style', 'dress', 'gown', 'suit', 'tuxedo', 'outfit', 'ensemble',
            'red carpet', 'redcarpet', 'designer', 'couture', 'wearing', 'wears', 'sporting',
            'stunning', 'gorgeous', 'beautiful', 'elegant', 'chic', 'fabulous', 'amazing',
            'jewelry', 'jewels', 'necklace', 'earrings', 'bracelet', 'ring', 'accessories',
            'shoes', 'heels', 'boots', 'hair', 'hairstyle', 'makeup', 'make-up',
            'color', 'colored', 'trend', 'trending', 'viral', 'best dressed', 'worst dressed'
        }
        
        # Common fashion brands and designers
        self.designer_brands = {
            'chanel', 'dior', 'versace', 'gucci', 'prada', 'louis vuitton', 'hermes',
            'valentino', 'dolce gabbana', 'giorgio armani', 'tom ford', 'marc jacobs',
            'ralph lauren', 'calvin klein', 'michael kors', 'vera wang', 'oscar de la renta',
            'zac posen', 'marchesa', 'elie saab', 'zuhair murad', 'tadashi shoji',
            'monique lhuillier', 'reem acra', 'j. mendel', 'tony ward'
        }
        
        # Common fashion colors
        self.fashion_colors = {
            'black', 'white', 'red', 'blue', 'green', 'yellow', 'purple', 'pink',
            'orange', 'brown', 'gray', 'grey', 'gold', 'silver', 'navy', 'burgundy',
            'maroon', 'crimson', 'scarlet', 'emerald', 'sapphire', 'ruby', 'pearl',
            'champagne', 'ivory', 'cream', 'beige', 'tan', 'rose', 'coral'
        }
        
        # Words to filter out from extracted fashion descriptions
        self.filter_words = {
            'the', 'a', 'an', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'of', 'with',
            'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that',
            'these', 'those', 'fashion', 'style', 'look', 'outfit', 'ensemble',
            'wearing', 'wears', 'sporting', 'sports', 'dressed', 'arrives', 'arriving'
        }
    
    def process(self, tweet: Tweet) -> Tweet:
        """Extract fashion information from tweet text and store in tweet metadata."""
        extracted_data = self.extract_fashion_info(tweet.text)
        
        # Store extracted data in tweet metadata
        if not hasattr(tweet, 'fashion_descriptions'):
            tweet.fashion_descriptions = []
        if not hasattr(tweet, 'fashion_celebrities'):
            tweet.fashion_celebrities = []
        if not hasattr(tweet, 'designer_brands'):
            tweet.designer_brands = []
        if not hasattr(tweet, 'fashion_colors'):
            tweet.fashion_colors = []
        
        tweet.fashion_descriptions.extend(extracted_data['descriptions'])
        tweet.fashion_celebrities.extend(extracted_data['celebrities'])
        tweet.designer_brands.extend(extracted_data['designers'])
        tweet.fashion_colors.extend(extracted_data['colors'])
        
        return tweet
    
    def extract_fashion_info(self, text: str) -> Dict[str, List[str]]:
        """Extract fashion information from text using regex patterns."""
        result = {
            'descriptions': [],
            'celebrities': [],
            'designers': [],
            'colors': []
        }
        
        # Check if text contains fashion-related context
        if not self._has_fashion_context(text):
            return result
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle multiple groups (celebrity and fashion description)
                    for i, group in enumerate(match):
                        if group and len(group.strip()) > 2:
                            cleaned_text = self._clean_fashion_text(group.strip())
                            if i == 0 and self._looks_like_celebrity_name(group.strip()):
                                # First group might be celebrity name
                                result['celebrities'].append(cleaned_text)
                            else:
                                # Other groups might be fashion descriptions
                                if self._looks_like_fashion_description(cleaned_text):
                                    result['descriptions'].append(cleaned_text)
                                    
                                    # Extract specific elements
                                    designers = self._extract_designers(cleaned_text)
                                    colors = self._extract_colors(cleaned_text)
                                    result['designers'].extend(designers)
                                    result['colors'].extend(colors)
                else:
                    if match and len(match.strip()) > 2:
                        cleaned_text = self._clean_fashion_text(match.strip())
                        if self._looks_like_fashion_description(cleaned_text):
                            result['descriptions'].append(cleaned_text)
                            
                            # Extract specific elements
                            designers = self._extract_designers(cleaned_text)
                            colors = self._extract_colors(cleaned_text)
                            result['designers'].extend(designers)
                            result['colors'].extend(colors)
        
        # Remove duplicates and filter
        result['descriptions'] = list(set([d for d in result['descriptions'] if self._is_valid_fashion_description(d)]))
        result['celebrities'] = list(set([c for c in result['celebrities'] if self._is_valid_celebrity_name(c)]))
        result['designers'] = list(set(result['designers']))
        result['colors'] = list(set(result['colors']))
        
        return result
    
    def _has_fashion_context(self, text: str) -> bool:
        """Check if text contains fashion-related context."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.fashion_keywords)
    
    def _clean_fashion_text(self, text: str) -> str:
        """Clean extracted fashion text."""
        # Remove extra whitespace
        cleaned = ' '.join(text.split())
        
        # Remove leading/trailing punctuation
        cleaned = cleaned.strip('.,!?;:"')
        
        # Capitalize properly
        words = cleaned.split()
        capitalized_words = []
        for word in words:
            if '-' in word:
                # Handle hyphenated words
                parts = word.split('-')
                capitalized_parts = [part.capitalize() for part in parts]
                capitalized_words.append('-'.join(capitalized_parts))
            else:
                capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words)
    
    def _looks_like_fashion_description(self, text: str) -> bool:
        """Check if text looks like a fashion description."""
        if not text or len(text) < 5:
            return False
        
        text_lower = text.lower()
        
        # Check for fashion-related words
        fashion_indicators = [
            'dress', 'gown', 'suit', 'tuxedo', 'outfit', 'ensemble',
            'jewelry', 'shoes', 'heels', 'hair', 'makeup', 'color',
            'designer', 'brand', 'fashion', 'style', 'elegant', 'beautiful'
        ]
        
        return any(indicator in text_lower for indicator in fashion_indicators)
    
    def _looks_like_celebrity_name(self, text: str) -> bool:
        """Check if text looks like a celebrity name."""
        if not text or len(text) > 50:
            return False
        
        # Check for name pattern (capitalized words)
        name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        name_matches = name_pattern.findall(text)
        
        # Should have 1-3 capitalized words
        return 1 <= len(name_matches) <= 3
    
    def _extract_designers(self, text: str) -> List[str]:
        """Extract designer/brand names from text."""
        designers = []
        text_lower = text.lower()
        
        for brand in self.designer_brands:
            if brand in text_lower:
                designers.append(brand.title())
        
        return designers
    
    def _extract_colors(self, text: str) -> List[str]:
        """Extract color names from text."""
        colors = []
        text_lower = text.lower()
        
        for color in self.fashion_colors:
            if color in text_lower:
                colors.append(color.title())
        
        return colors
    
    def _is_valid_fashion_description(self, description: str) -> bool:
        """Check if extracted text is a valid fashion description."""
        if not description or len(description) < 5:
            return False
        
        # Check if it contains mostly filter words
        words = description.lower().split()
        if len(words) < 2:
            return False
        
        filter_word_count = sum(1 for word in words if word in self.filter_words)
        if filter_word_count > len(words) * 0.7:  # More than 70% are filter words
            return False
        
        # Should contain some meaningful content
        meaningful_words = [word for word in words if word not in self.filter_words]
        return len(meaningful_words) >= 1
    
    def _is_valid_celebrity_name(self, name: str) -> bool:
        """Check if extracted text is a valid celebrity name."""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Check for name pattern
        name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        name_matches = name_pattern.findall(name)
        
        # Should have 1-3 capitalized words and not be mostly filter words
        if not (1 <= len(name_matches) <= 3):
            return False
        
        words = name.lower().split()
        filter_word_count = sum(1 for word in words if word in self.filter_words)
        return filter_word_count <= len(words) / 2
