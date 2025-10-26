import re
from typing import Optional

from ..processor import BaseProcessor
from ..tweet import Tweet


class AwardNameExtractor(BaseProcessor):
    """Extract award names from tweets using comprehensive regex patterns for Golden Globes."""
    
    def __init__(self):
        super().__init__(processor_type="award name extractor")
        
        # Comprehensive patterns for Golden Globes awards
        self.award_patterns = [
            # Motion Picture Awards
            r"Best\s+(?:Motion\s+Picture\s+)?(?:Picture\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Actor\s+in\s+a\s+(?:Motion\s+Picture\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Actress\s+in\s+a\s+(?:Motion\s+Picture\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Supporting\s+Actor\s+in\s+a\s+(?:Motion\s+Picture\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Supporting\s+Actress\s+in\s+a\s+(?:Motion\s+Picture\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Director\s+-\s+(?:Motion\s+Picture\s+)?(?:Picture\s+)?(?:Drama|Musical\s+or\s+Comedy)?",
            r"Best\s+Screenplay\s+-\s+(?:Motion\s+Picture\s+)?(?:Picture\s+)?(?:Drama|Musical\s+or\s+Comedy)?",
            r"Best\s+Original\s+(?:Score|Song)\s+-\s+(?:Motion\s+Picture\s+)?(?:Picture\s+)?(?:Drama|Musical\s+or\s+Comedy)?",
            r"Best\s+Foreign\s+(?:Language\s+)?(?:Motion\s+Picture\s+)?(?:Film\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)?",
            r"Best\s+Animated\s+(?:Motion\s+Picture\s+)?(?:Film\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)?",
            
            # Television Awards
            r"Best\s+(?:Television\s+)?(?:TV\s+)?(?:Series\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Actor\s+in\s+a\s+(?:Television\s+)?(?:TV\s+)?(?:Series\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Actress\s+in\s+a\s+(?:Television\s+)?(?:TV\s+)?(?:Series\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Supporting\s+Actor\s+in\s+a\s+(?:Television\s+)?(?:TV\s+)?(?:Series\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Supporting\s+Actress\s+in\s+a\s+(?:Television\s+)?(?:TV\s+)?(?:Series\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+(?:Television\s+)?(?:TV\s+)?(?:Mini\s+)?(?:Series\s+or\s+)?(?:Motion\s+Picture\s+)?(?:Made\s+for\s+)?(?:TV\s+)?(?:Movie\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)?",
            r"Best\s+Actor\s+in\s+a\s+(?:Television\s+)?(?:TV\s+)?(?:Mini\s+)?(?:Series\s+or\s+)?(?:Motion\s+Picture\s+)?(?:Made\s+for\s+)?(?:TV\s+)?(?:Movie\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)?",
            r"Best\s+Actress\s+in\s+a\s+(?:Television\s+)?(?:TV\s+)?(?:Mini\s+)?(?:Series\s+or\s+)?(?:Motion\s+Picture\s+)?(?:Made\s+for\s+)?(?:TV\s+)?(?:Movie\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)?",
            
            # Special Awards
            r"Best\s+Performance\s+by\s+an\s+Actor\s+in\s+a\s+(?:Motion\s+Picture\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Best\s+Performance\s+by\s+an\s+Actress\s+in\s+a\s+(?:Motion\s+Picture\s+)?(?:-\s*)?(?:Drama|Musical\s+or\s+Comedy)",
            r"Cecil\s+B\.\s+DeMille\s+Award",
            r"Golden\s+Globe\s+Award",
            
            # Generic patterns for flexibility
            r"Best\s+\w+(?:\s+\w+)*\s+(?:in\s+)?(?:a\s+)?(?:Motion\s+Picture|Television|TV)(?:\s+\w+)*(?:\s+-\s+(?:Drama|Musical\s+or\s+Comedy))?",
            r"Best\s+(?:Actor|Actress|Director|Screenplay|Original\s+(?:Score|Song)|Foreign|Animated)",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.award_patterns]
        
        # Common award name variations and abbreviations
        self.award_synonyms = {
            'best picture': ['best motion picture', 'best film', 'best movie'],
            'best actor': ['best performance by an actor', 'best actor in a motion picture'],
            'best actress': ['best performance by an actress', 'best actress in a motion picture'],
            'best tv series': ['best television series', 'best tv show', 'best series'],
            'golden globe': ['golden globes', 'gg', 'golden globe award'],
        }
    
    def process(self, tweet: Tweet) -> Tweet:
        """Extract award names from tweet text and store in tweet metadata."""
        extracted_awards = self.extract_awards(tweet.text)
        
        # Store extracted awards in tweet metadata
        if not hasattr(tweet, 'extracted_awards'):
            tweet.extracted_awards = []
        
        tweet.extracted_awards.extend(extracted_awards)
        
        return tweet
    
    def extract_awards(self, text: str) -> list[str]:
        """Extract award names from text using regex patterns."""
        awards = set()  # Use set to avoid duplicates
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle groups in regex
                    award_name = ' '.join(filter(None, match))
                else:
                    award_name = match
                
                # Clean and normalize the award name
                cleaned_award = self._clean_award_name(award_name)
                if cleaned_award and len(cleaned_award) > 3:  # Filter out very short matches
                    awards.add(cleaned_award)
        
        return list(awards)
    
    def _clean_award_name(self, award_name: str) -> Optional[str]:
        """Clean and normalize award name."""
        if not award_name:
            return None
            
        # Remove extra whitespace and normalize
        cleaned = ' '.join(award_name.split())
        
        # Remove common prefixes/suffixes that don't add value
        cleaned = re.sub(r'^(the\s+|a\s+|an\s+)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+(award|trophy|prize)$', '', cleaned, flags=re.IGNORECASE)
        
        # Capitalize properly
        cleaned = cleaned.title()
        
        return cleaned if cleaned else None