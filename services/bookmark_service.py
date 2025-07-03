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
        
        # Auto-fetch title if not provided
        if not title.strip():
            title = self._fetch_page_title(url) or "Untitled"
        
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
    
    def _fetch_page_title(self, url: str) -> Optional[str]:
        """Fetch page title from URL."""
        try:
            response = requests.get(url, timeout=5, headers={
                'User-Agent': 'StupidBookmarks/1.0'
            })
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    return title_tag.get_text().strip()
        except Exception:
            pass
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
