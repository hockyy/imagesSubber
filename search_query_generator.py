"""
Search query generator module for timeline generation.
Generates search queries from keywords for image searching.
"""

from typing import List


class SearchQueryGenerator:
    """Generates search queries from keywords."""
    
    @staticmethod
    def generate_search_queries(keywords: List[str]) -> List[str]:
        """
        Generate search queries from keywords.
        
        Args:
            keywords: List of keywords
            
        Returns:
            List of search queries in order of preference
        """
        if not keywords:
            return ["abstract art"]
        
        queries = []
        
        # Single important keywords (longer ones first)
        important_keywords = sorted([kw for kw in keywords if len(kw) > 3], 
                                  key=len, reverse=True)
        queries.extend(important_keywords[:3])
        
        # Combinations of 2-3 keywords
        if len(keywords) >= 2:
            # Best 2-word combinations
            for i in range(min(2, len(keywords))):
                for j in range(i + 1, min(4, len(keywords))):
                    queries.append(f"{keywords[i]} {keywords[j]}")
        
        # Fallback queries
        if not queries:
            queries = ["nature", "landscape", "abstract"]
        
        return queries[:5]  # Limit to 5 queries max
