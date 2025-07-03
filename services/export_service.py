"""Service for importing and exporting bookmarks in various formats."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from models.models import Bookmark, User, Tag
from services.bookmark_service import BookmarkService

class BookmarkExportService:
    """Service for exporting bookmarks to different formats."""
    
    def __init__(self):
        self.bookmark_service = BookmarkService()
    
    def export_netscape_html(self, db: Session, user_id: int) -> str:
        """Export bookmarks to Netscape HTML format."""
        # Get all bookmarks for the user
        bookmarks = self.bookmark_service.get_bookmarks(db, user_id, limit=10000)
        
        # Create HTML template
        html = f"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="{int(datetime.now().timestamp())}" LAST_MODIFIED="{int(datetime.now().timestamp())}" PERSONAL_TOOLBAR_FOLDER="true">StupidBookmarks</H3>
    <DL><p>
"""

        # Group bookmarks by tag
        tags_dict = {}
        for bookmark in bookmarks:
            for tag in bookmark.tags:
                if tag.name not in tags_dict:
                    tags_dict[tag.name] = []
                tags_dict[tag.name].append(bookmark)
        
        # Add bookmarks with no tags first
        untagged_bookmarks = [b for b in bookmarks if not b.tags]
        for bookmark in untagged_bookmarks:
            created_timestamp = int(bookmark.created_at.timestamp()) if bookmark.created_at else int(datetime.now().timestamp())
            html += f'        <DT><A HREF="{bookmark.url}" ADD_DATE="{created_timestamp}" LAST_MODIFIED="{created_timestamp}">{bookmark.title}</A>\n'
            if bookmark.description:
                html += f'        <DD>{bookmark.description}\n'
        
        # Then add bookmarks grouped by tags
        for tag_name, tag_bookmarks in tags_dict.items():
            html += f'        <DT><H3 ADD_DATE="{int(datetime.now().timestamp())}" LAST_MODIFIED="{int(datetime.now().timestamp())}">{tag_name}</H3>\n'
            html += '        <DL><p>\n'
            
            for bookmark in tag_bookmarks:
                created_timestamp = int(bookmark.created_at.timestamp()) if bookmark.created_at else int(datetime.now().timestamp())
                html += f'            <DT><A HREF="{bookmark.url}" ADD_DATE="{created_timestamp}" LAST_MODIFIED="{created_timestamp}">{bookmark.title}</A>\n'
                if bookmark.description:
                    html += f'            <DD>{bookmark.description}\n'
            
            html += '        </DL><p>\n'
        
        # Close the HTML
        html += """    </DL><p>
</DL>
"""
        return html

    def import_netscape_html(self, db: Session, user_id: int, html_content: str) -> Dict[str, Any]:
        """Import bookmarks from Netscape HTML format."""
        imported_count = 0
        skipped_count = 0
        errors = []
        
        try:
            print(f"Starting import process. HTML content length: {len(html_content)}")
            # Parse with html.parser which is more forgiving for malformed HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Basic HTML structure info
            print(f"HTML structure summary:")
            print(f"- Has HTML tag: {bool(soup.find('html'))}")
            print(f"- Has DL tag: {bool(soup.find('dl'))}")
            print(f"- Has TITLE tag: {bool(soup.find('title'))}")
            print(f"- Has H1 tag: {bool(soup.find('h1'))}")
            links = soup.find_all('a')
            print(f"- Total A tags: {len(links)}")
            
            # Process all links directly for simplicity and reliability
            print(f"Processing {len(links)} links found in document")
            for a in links:
                url = a.get('href')
                title = a.text.strip()
                
                if not url or not url.strip():
                    print(f"Skipping bookmark with empty URL")
                    skipped_count += 1
                    continue
                
                if not title:
                    title = url
                
                print(f"Processing bookmark: {title[:30]}... - {url[:30]}...")
                
                # Find potential parent folder (H3) to use as tags
                current_element = a
                folder_tags = []
                description = ""
                
                # Look for description (DD)
                parent_dt = a.parent
                if parent_dt and parent_dt.name == 'dt':
                    next_dd = parent_dt.find_next_sibling()
                    if next_dd and next_dd.name == 'dd':
                        description = next_dd.text.strip()
                        print(f"Found description: {description[:30]}...")
                
                # Try to find parent folder structure by traversing up the DOM
                while current_element:
                    if current_element.name == 'dl':
                        # Look for previous H3
                        prev_dt = current_element.find_previous_sibling('dt')
                        if prev_dt:
                            h3 = prev_dt.find('h3')
                            if h3 and h3.text.strip():
                                folder_name = h3.text.strip()
                                # Skip common browser folder names
                                if folder_name.lower() not in ['bookmarks', 'favorites', 'bookmark bar', 'bookmarks bar', 
                                                             'bookmarks menu', 'other bookmarks', 'personal toolbar folder']:
                                    folder_tags.insert(0, folder_name)
                                    print(f"Found parent folder: {folder_name}")
                    
                    current_element = current_element.parent
                
                # Look for additional metadata in attributes
                private = a.get('private', '0') == '1'
                toread = a.get('toread', '0') == '1'
                
                # Additional tags from attributes
                extra_tags = []
                if 'tags' in a.attrs:
                    tag_attr = a.get('tags', '')
                    if tag_attr:
                        extra_tags = [t.strip() for t in tag_attr.split(',')]
                        print(f"Found tags attribute: {extra_tags}")
                
                # Combine all tags
                all_tags = folder_tags + extra_tags
                tags_str = " ".join(all_tags) if all_tags else ""
                
                try:
                    self.bookmark_service.add_bookmark(
                        db=db,
                        user_id=user_id,
                        url=url,
                        title=title,
                        description=description,
                        tags=tags_str
                    )
                    imported_count += 1
                    print(f"Successfully added bookmark. Import count: {imported_count}")
                except Exception as e:
                    print(f"Error importing bookmark: {str(e)}")
                    errors.append(f"Error importing {url}: {str(e)}")
                    skipped_count += 1
            
        except Exception as e:
            print(f"Exception during import: {str(e)}")
            import traceback
            traceback.print_exc()
            errors.append(f"Error parsing HTML: {str(e)}")
        
        print(f"Import complete: {imported_count} imported, {skipped_count} skipped, {len(errors)} errors")
        if errors:
            print(f"First few errors: {errors[:3]}")
            
        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors
        }
