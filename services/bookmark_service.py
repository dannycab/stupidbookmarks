"""Bookmark management service for StupidBookmarks."""

import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from models.models import Bookmark, Tag, user_tags

class BookmarkService:
    """Service for handling bookmark operations."""
    
    def get_bookmarks(
        self, 
        db: Session, 
        user_id: int, 
        tag_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Bookmark]:
        """Get bookmarks with optional tag filtering."""
        query = db.query(Bookmark).filter(Bookmark.user_id == user_id)
        
        if tag_filter:
            query = query.join(Bookmark.tags).filter(Tag.name == tag_filter)
        
        return query.order_by(desc(Bookmark.created_at)).offset(offset).limit(limit).all()
    
    def add_bookmark(
        self, 
        db: Session, 
        user_id: int, 
        url: str, 
        title: str, 
        description: str = "", 
        tags: str = ""
    ) -> Bookmark:
        """Add a new bookmark."""
        # Clean and validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Auto-fetch title if not provided or title is just whitespace
        if not title or not title.strip():
            print(f"Auto-fetching title for URL: {url}")  # Debug log
            fetched_title = self._fetch_page_title(url)
            title = fetched_title or "Untitled"
            print(f"Fetched title: {title}")  # Debug log
        
        # Create bookmark
        bookmark = Bookmark(
            url=url,
            title=title.strip(),
            description=description.strip(),
            user_id=user_id
        )
        
        db.add(bookmark)
        db.flush()  # Get the bookmark ID
        
        # Process tags
        if tags.strip():
            self._add_tags_to_bookmark(db, bookmark, tags, user_id)
        
        db.commit()
        db.refresh(bookmark)
        return bookmark
    
    def delete_bookmark(self, db: Session, bookmark_id: int, user_id: int) -> bool:
        """Delete a bookmark."""
        bookmark = db.query(Bookmark).filter(
            Bookmark.id == bookmark_id, 
            Bookmark.user_id == user_id
        ).first()
        
        if bookmark:
            db.delete(bookmark)
            db.commit()
            return True
        return False
    
    def delete_all_bookmarks(self, db: Session, user_id: int) -> int:
        """Delete all bookmarks for a user.
        
        Returns:
            int: Number of bookmarks deleted
        """
        # Get the count before deletion for return value
        bookmark_count = db.query(Bookmark).filter(Bookmark.user_id == user_id).count()
        
        # Delete all bookmarks for the user
        db.query(Bookmark).filter(Bookmark.user_id == user_id).delete()
        db.commit()
        
        return bookmark_count
    
    def get_tag_cloud(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get tag cloud with bookmark counts."""
        tag_counts = (
            db.query(Tag.name, Tag.color, func.count(user_tags.c.bookmark_id).label('count'))
            .join(user_tags, Tag.id == user_tags.c.tag_id)
            .join(Bookmark, user_tags.c.bookmark_id == Bookmark.id)
            .filter(Bookmark.user_id == user_id)
            .group_by(Tag.id, Tag.name, Tag.color)
            .order_by(desc('count'))
            .all()
        )
        
        return [
            {
                "name": name,
                "color": color,
                "count": count,
                "size": min(count * 2 + 12, 24)  # Scale font size based on count
            }
            for name, color, count in tag_counts
        ]
    
    def get_statistics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get bookmark statistics."""
        total_bookmarks = db.query(Bookmark).filter(Bookmark.user_id == user_id).count()
        total_tags = (
            db.query(Tag.id)
            .join(user_tags, Tag.id == user_tags.c.tag_id)
            .join(Bookmark, user_tags.c.bookmark_id == Bookmark.id)
            .filter(Bookmark.user_id == user_id)
            .distinct()
            .count()
        )
        
        # Recent bookmarks (last 7 days)
        from datetime import datetime, timedelta
        recent_date = datetime.now() - timedelta(days=7)
        recent_bookmarks = (
            db.query(Bookmark)
            .filter(Bookmark.user_id == user_id, Bookmark.created_at >= recent_date)
            .count()
        )
        
        # Top domains
        domain_query = (
            db.query(func.count(Bookmark.id).label('count'))
            .filter(Bookmark.user_id == user_id)
            .group_by(
                func.substr(
                    Bookmark.url,
                    func.instr(Bookmark.url, '//') + 2,
                    func.instr(func.substr(Bookmark.url, func.instr(Bookmark.url, '//') + 2), '/') - 1
                )
            )
            .order_by(desc('count'))
            .limit(5)
            .all()
        )
        
        return {
            "total_bookmarks": total_bookmarks,
            "total_tags": total_tags,
            "recent_bookmarks": recent_bookmarks,
            "top_domains_count": len(domain_query)
        }
    
    def bookmark_to_dict(self, bookmark: Bookmark) -> Dict[str, Any]:
        """Convert bookmark to dictionary for API responses."""
        return {
            "id": bookmark.id,
            "url": bookmark.url,
            "title": bookmark.title,
            "description": bookmark.description,
            "tags": [tag.name for tag in bookmark.tags],
            "created_at": bookmark.created_at.isoformat() if bookmark.created_at else None,
            "updated_at": bookmark.updated_at.isoformat() if bookmark.updated_at else None
        }
    
    def count_bookmarks(self, db: Session, user_id: int, tag_filter: Optional[str] = None) -> int:
        """Count bookmarks with optional tag filtering."""
        query = db.query(func.count(Bookmark.id)).filter(Bookmark.user_id == user_id)
        
        if tag_filter:
            query = query.join(Bookmark.tags).filter(Tag.name == tag_filter)
        
        return query.scalar() or 0
    
    def _fetch_page_title(self, url: str) -> Optional[str]:
        """Fetch page title from URL with multiple fallback strategies."""
        headers_list = [
            # Chrome on macOS
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            # Firefox on macOS
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            # Simple bot-friendly headers
            {
                'User-Agent': 'StupidBookmarks/1.0 (+https://github.com/dannycab/stupidbookmarks)',
                'Accept': 'text/html,application/xhtml+xml',
            }
        ]
        
        for i, headers in enumerate(headers_list):
            try:
                print(f"Attempting to fetch title from: {url} (strategy {i+1}/{len(headers_list)})")
                
                # Use different timeouts for different strategies
                timeout = 15 if i == 0 else (10 if i == 1 else 5)
                
                response = requests.get(
                    url, 
                    timeout=timeout, 
                    headers=headers,
                    allow_redirects=True,
                    verify=True
                )
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Try different encodings if needed
                    content = response.content
                    if response.encoding:
                        try:
                            content = response.content.decode(response.encoding)
                        except:
                            content = response.content.decode('utf-8', errors='ignore')
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Try multiple ways to get the title
                    title = None
                    
                    # 1. Standard <title> tag
                    title_tag = soup.find('title')
                    if title_tag and title_tag.get_text().strip():
                        title = title_tag.get_text().strip()
                        print(f"Found title in <title> tag: {title}")
                    
                    # 2. Open Graph title
                    if not title:
                        og_title = soup.find('meta', property='og:title')
                        if og_title and og_title.get('content'):
                            title = og_title['content'].strip()
                            print(f"Found title in og:title: {title}")
                    
                    # 3. Twitter title
                    if not title:
                        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
                        if twitter_title and twitter_title.get('content'):
                            title = twitter_title['content'].strip()
                            print(f"Found title in twitter:title: {title}")
                    
                    # 4. First h1 tag
                    if not title:
                        h1_tag = soup.find('h1')
                        if h1_tag and h1_tag.get_text().strip():
                            title = h1_tag.get_text().strip()
                            print(f"Found title in h1: {title}")
                    
                    if title:
                        # Clean up the title
                        title = ' '.join(title.split())  # Remove extra whitespace
                        title = title.replace('\n', ' ').replace('\r', ' ')
                        
                        # Limit title length
                        if len(title) > 200:
                            title = title[:197] + "..."
                        
                        print(f"Successfully fetched title: {title}")
                        return title
                    else:
                        print("No title found in any meta tags")
                
                print(f"Failed to fetch title: HTTP {response.status_code}")
                
            except requests.exceptions.Timeout:
                print(f"Timeout fetching title (strategy {i+1})")
                continue
            except requests.exceptions.RequestException as e:
                print(f"Request error fetching title (strategy {i+1}): {e}")
                continue
            except Exception as e:
                print(f"Unexpected error fetching title (strategy {i+1}): {e}")
                continue
        
        print("All title fetching strategies failed")
        return None
    
    def _add_tags_to_bookmark(self, db: Session, bookmark: Bookmark, tags_str: str, user_id: int):
        """Add tags to a bookmark."""
        # Parse tags (comma or space separated)
        tag_names = [
            tag.strip().lower() 
            for tag in re.split(r'[,\s]+', tags_str) 
            if tag.strip()
        ]
        
        for tag_name in tag_names:
            # Get or create tag
            tag = db.query(Tag).filter(Tag.name == tag_name, Tag.user_id == user_id).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=user_id)
                db.add(tag)
                db.flush()
            
            # Add to bookmark if not already added
            if tag not in bookmark.tags:
                bookmark.tags.append(tag)
