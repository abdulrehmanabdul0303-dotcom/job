"""
Job fetcher service.
Fetches jobs from RSS feeds and HTML pages with safety checks.
"""
import feedparser
import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class JobFetcher:
    """Service for fetching jobs from external sources."""
    
    # Whitelisted domains for HTML scraping (safety measure)
    WHITELISTED_DOMAINS = [
        'greenhouse.io',
        'lever.co',
        'workable.com',
        'jobs.ashbyhq.com',
        'boards.greenhouse.io',
    ]
    
    @staticmethod
    def generate_url_hash(url: str) -> str:
        """
        Generate a unique hash for a URL for deduplication.
        Normalizes URL before hashing.
        
        Args:
            url: Job application URL
            
        Returns:
            SHA256 hash of normalized URL
        """
        # Normalize URL: lowercase, remove trailing slash, remove query params for dedup
        parsed = urlparse(url.lower().strip())
        normalized = f"{parsed.netloc}{parsed.path}".rstrip('/')
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    @staticmethod
    async def fetch_rss_jobs(url: str) -> List[Dict[str, Any]]:
        """
        Fetch jobs from RSS feed.
        
        Args:
            url: RSS feed URL
            
        Returns:
            List of job dictionaries
        """
        try:
            logger.info(f"Fetching RSS feed: {url}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"RSS feed has issues: {feed.bozo_exception}")
            
            jobs = []
            for entry in feed.entries:
                job = JobFetcher._parse_rss_entry(entry)
                if job:
                    jobs.append(job)
            
            logger.info(f"Fetched {len(jobs)} jobs from RSS feed")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            raise
    
    @staticmethod
    def _parse_rss_entry(entry: Any) -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS entry into job data.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Job dictionary or None if parsing fails
        """
        try:
            # Extract title
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # Extract link (application URL)
            link = entry.get('link', '').strip()
            if not link:
                return None
            
            # Extract description
            description = entry.get('summary', '') or entry.get('description', '')
            
            # Try to extract company from title or content
            company = JobFetcher._extract_company(entry)
            
            # Try to extract location
            location = JobFetcher._extract_location(entry)
            
            # Try to extract work type
            work_type = JobFetcher._extract_work_type(title, description)
            
            # Parse published date
            posted_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    posted_date = datetime(*entry.published_parsed[:6])
                except:
                    pass
            
            return {
                'title': title,
                'company': company or 'Unknown',
                'location': location,
                'description': description,
                'application_url': link,
                'work_type': work_type,
                'posted_date': posted_date,
                'url_hash': JobFetcher.generate_url_hash(link),
            }
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    @staticmethod
    def _extract_company(entry: Any) -> Optional[str]:
        """Extract company name from RSS entry."""
        # Try author field
        if hasattr(entry, 'author') and entry.author:
            return entry.author.strip()
        
        # Try to extract from title (pattern: "Title at Company")
        title = entry.get('title', '')
        match = re.search(r'\bat\s+([^-|]+)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try tags
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if 'company' in tag.get('term', '').lower():
                    return tag.get('term', '').strip()
        
        return None
    
    @staticmethod
    def _extract_location(entry: Any) -> Optional[str]:
        """Extract location from RSS entry."""
        # Try to find location in title
        title = entry.get('title', '')
        
        # Common patterns: "Title - Location", "Title | Location", "Title (Location)"
        patterns = [
            r'[-|]\s*([^-|]+(?:Remote|USA|UK|Canada|Germany|France|India|Australia))',
            r'\(([^)]+(?:Remote|USA|UK|Canada|Germany|France|India|Australia))\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Try description
        description = entry.get('summary', '') or entry.get('description', '')
        if 'remote' in description.lower():
            return 'Remote'
        
        return None
    
    @staticmethod
    def _extract_work_type(title: str, description: str) -> Optional[str]:
        """Extract work type from title and description."""
        text = f"{title} {description}".lower()
        
        if any(keyword in text for keyword in ['remote', 'work from home', 'wfh']):
            return 'remote'
        elif 'full-time' in text or 'full time' in text:
            return 'full-time'
        elif 'part-time' in text or 'part time' in text:
            return 'part-time'
        elif 'contract' in text or 'contractor' in text:
            return 'contract'
        elif 'hybrid' in text:
            return 'hybrid'
        
        return None
    
    @staticmethod
    def is_domain_whitelisted(url: str) -> bool:
        """
        Check if domain is whitelisted for HTML scraping.
        
        Args:
            url: URL to check
            
        Returns:
            True if domain is whitelisted
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for whitelisted in JobFetcher.WHITELISTED_DOMAINS:
                if whitelisted in domain:
                    return True
            
            return False
        except:
            return False
    
    @staticmethod
    async def fetch_html_jobs(url: str) -> List[Dict[str, Any]]:
        """
        Fetch jobs from HTML page (only whitelisted domains).
        
        Args:
            url: HTML page URL
            
        Returns:
            List of job dictionaries
        """
        if not JobFetcher.is_domain_whitelisted(url):
            raise ValueError(f"Domain not whitelisted for HTML scraping: {url}")
        
        # TODO: Implement HTML parsing for whitelisted domains
        # For now, return empty list
        logger.warning(f"HTML scraping not yet implemented for: {url}")
        return []
