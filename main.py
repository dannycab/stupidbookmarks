#!/usr/bimport os
from fastapi import FastAPI, Request, Depends, HTTPException, Form, status, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from typing import Optional, List, Dict, Any
import secrets
import hashlib
from datetime import datetime
import io
from pydantic import BaseModel, Field, HttpUrl, validator
"""
StupidBookmarks - A fast, minimalistic bookmark manager built with FastAPI and Tailwind CSS.

Vibe Coding Project Notice:
This project is developed in a freeform, improvisational, and experimental style.
"""

import os
from fastapi import FastAPI, Request, Depends, HTTPException, Form, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from typing import Optional, List, Dict, Any
import secrets
import hashlib
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator

from models.database import get_db, init_db
from models.models import User, Bookmark, Tag, APIKey, user_tags
from services.bookmark_service import BookmarkService
from services.auth_service import AuthService
from services.api_service import APIService
from services.export_service import BookmarkExportService
import version

# Initialize FastAPI app
app = FastAPI(
    title="StupidBookmarks API", 
    description="A fast, minimalistic bookmark manager built with FastAPI and Tailwind CSS.\n\n"
                "## Authentication\n\n"
                "This API uses API key authentication. Add your key as a Bearer token in the Authorization header:\n\n"
                "```\nAuthorization: Bearer YOUR_API_KEY\n```\n\n"
                "You can generate API keys in the [Admin Dashboard](/admin).",
    version=version.__version__,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# API Models
class BookmarkCreateRequest(BaseModel):
    url: str = Field(..., description="URL of the bookmark")
    title: Optional[str] = Field(None, description="Title of the bookmark. If not provided, will be auto-fetched from the URL")
    description: Optional[str] = Field("", description="Description of the bookmark")
    tags: Optional[str] = Field("", description="Comma or space separated list of tags")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "title": "Example Website",
                "description": "This is an example bookmark",
                "tags": "example, demo, test"
            }
        }

class TagResponse(BaseModel):
    name: str
    color: Optional[str]
    count: int
    size: int
    
    class Config:
        schema_extra = {
            "example": {
                "name": "python",
                "color": "#3776AB",
                "count": 5,
                "size": 22
            }
        }

class BookmarkResponse(BaseModel):
    id: int
    url: str
    title: str
    description: Optional[str] = ""
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "url": "https://example.com",
                "title": "Example Website",
                "description": "This is an example bookmark",
                "tags": ["example", "demo", "test"],
                "created_at": "2025-07-03T12:34:56.789Z",
                "updated_at": "2025-07-03T12:34:56.789Z"
            }
        }

# Initialize services
bookmark_service = BookmarkService()
auth_service = AuthService()
api_service = APIService()
export_service = BookmarkExportService()

# Security
security = HTTPBearer(auto_error=False)

@app.on_event("startup")
async def startup():
    """Initialize database and create default user if needed."""
    init_db()
    
    # Create default admin user if none exists
    db = next(get_db())
    try:
        if not auth_service.get_user(db):
            auth_service.create_default_user(db)
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request, 
    tag: Optional[str] = None, 
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Main bookmarks page with optional tag filtering and pagination."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Pagination configuration
    page_size = 20  # Number of bookmarks per page - adjust this if you want more bookmarks per page
    offset = (page - 1) * page_size if page > 0 else 0
    
    # Get bookmarks with pagination
    bookmarks = bookmark_service.get_bookmarks(
        db, user.id, tag_filter=tag, limit=page_size, offset=offset
    )
    
    # Get total count for pagination
    total_bookmarks = bookmark_service.count_bookmarks(db, user.id, tag_filter=tag)
    total_pages = (total_bookmarks + page_size - 1) // page_size  # Ceiling division
    
    # Get tag cloud
    tags = bookmark_service.get_tag_cloud(db, user.id)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "bookmarks": bookmarks,
        "tags": tags,
        "current_tag": tag,
        "user": user,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_bookmarks": total_bookmarks
        }
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, password: str = Form(...), db: Session = Depends(get_db)):
    """Handle login."""
    user = auth_service.authenticate(db, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid password"
        })
    
    response = RedirectResponse(url="/", status_code=302)
    auth_service.create_session(response, user.id)
    return response

@app.get("/logout")
async def logout():
    """Handle logout."""
    response = RedirectResponse(url="/login", status_code=302)
    auth_service.clear_session(response)
    return response

@app.get("/tags/{tag_name}", response_class=HTMLResponse)
async def tag_page(request: Request, tag_name: str, page: int = 1, db: Session = Depends(get_db)):
    """Show bookmarks for a specific tag with pagination."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Pagination configuration
    page_size = 20  # Number of bookmarks per page - same as main index
    offset = (page - 1) * page_size if page > 0 else 0
    
    # Get bookmarks with pagination
    bookmarks = bookmark_service.get_bookmarks(
        db, user.id, tag_filter=tag_name, limit=page_size, offset=offset
    )
    
    # Get total count for pagination
    total_bookmarks = bookmark_service.count_bookmarks(db, user.id, tag_filter=tag_name)
    total_pages = (total_bookmarks + page_size - 1) // page_size  # Ceiling division
    
    tags = bookmark_service.get_tag_cloud(db, user.id)
    
    return templates.TemplateResponse("tag.html", {
        "request": request,
        "bookmarks": bookmarks,
        "tags": tags,
        "tag_name": tag_name,
        "user": user,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_bookmarks": total_bookmarks
        }
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    stats = bookmark_service.get_statistics(db, user.id)
    api_keys = api_service.get_api_keys(db, user.id)
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "stats": stats,
        "api_keys": api_keys,
        "user": user
    })

@app.get("/admin/export/netscape", response_class=HTMLResponse)
async def export_bookmarks_netscape(request: Request, db: Session = Depends(get_db)):
    """Export bookmarks in Netscape HTML format."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    html_content = export_service.export_netscape_html(db, user.id)
    
    headers = {
        "Content-Disposition": f"attachment; filename=bookmarks_{datetime.now().strftime('%Y%m%d')}.html"
    }
    
    return HTMLResponse(content=html_content, headers=headers)

@app.post("/admin/import/netscape")
async def import_bookmarks_netscape(
    request: Request,
    bookmark_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import bookmarks from Netscape HTML format."""
    try:
        print(f"Received file upload: {bookmark_file.filename}, content type: {bookmark_file.content_type}")
        
        user = auth_service.get_current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        content = await bookmark_file.read()
        print(f"Read {len(content)} bytes from uploaded file")
        
        # Try to detect encoding, fallback to utf-8
        try:
            html_content = content.decode("utf-8")
        except UnicodeDecodeError:
            print("UTF-8 decoding failed, trying with ISO-8859-1")
            html_content = content.decode("ISO-8859-1")
        
        print(f"Decoded HTML content, length: {len(html_content)}")
        
        # Print first 100 chars to verify content
        print(f"Content preview: {html_content[:100]}...")
        
        result = export_service.import_netscape_html(db, user.id, html_content)
        
        # Log the result
        print(f"Import result: {result}")
        
        return RedirectResponse(
            url=f"/admin?success=bookmarks_imported&imported={result['imported']}&skipped={result['skipped']}",
            status_code=302
        )
    except Exception as e:
        print(f"Error in import endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return RedirectResponse(
            url=f"/admin?error=import_failed&message={str(e)}",
            status_code=302
        )

# Human-friendly API documentation
@app.get("/api/docs/help", response_class=HTMLResponse)
async def api_docs_page(request: Request, db: Session = Depends(get_db)):
    """Human-friendly API documentation page."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("api_docs.html", {
        "request": request,
        "user": user
    })

# User interface routes

# Bookmark management routes
@app.post("/bookmarks/add")
async def add_bookmark(
    request: Request,
    url: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    """Add a new bookmark."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    bookmark_service.add_bookmark(db, user.id, url, title, description, tags)
    return RedirectResponse(url="/", status_code=302)

@app.post("/bookmarks/{bookmark_id}/delete")
async def delete_bookmark(bookmark_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete a bookmark."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    bookmark_service.delete_bookmark(db, bookmark_id, user.id)
    return RedirectResponse(url="/", status_code=302)

# Admin functions
@app.post("/admin/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Change user password."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if not auth_service.verify_password(current_password, user.password_hash):
        return RedirectResponse(url="/admin?error=invalid_password", status_code=302)
    
    auth_service.change_password(db, user.id, new_password)
    return RedirectResponse(url="/admin?success=password_changed", status_code=302)

@app.post("/admin/api-keys/generate")
async def generate_api_key(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Generate a new API key."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    new_api_key = api_service.create_api_key(db, user.id, name)
    
    # Get all API keys and pass the new one for display
    stats = bookmark_service.get_statistics(db, user.id)
    api_keys = api_service.get_api_keys(db, user.id)
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "stats": stats,
        "api_keys": api_keys,
        "user": user,
        "new_api_key": new_api_key  # Pass the new key with raw_key
    })

@app.post("/admin/api-keys/{key_id}/delete")
async def delete_api_key(key_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete an API key."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    api_service.delete_api_key(db, key_id, user.id)
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/bookmarks/delete-all")
async def delete_all_bookmarks(
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete all bookmarks for the current user."""
    user = auth_service.get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    deleted_count = bookmark_service.delete_all_bookmarks(db, user.id)
    
    return RedirectResponse(
        url=f"/admin?success=bookmarks_deleted&count={deleted_count}",
        status_code=302
    )

# API routes
@app.get(
    "/api/bookmarks", 
    response_model=List[BookmarkResponse],
    summary="Get all bookmarks",
    description="Retrieve a list of bookmarks with optional filtering by tag",
    tags=["bookmarks"],
    responses={
        200: {"description": "List of bookmarks"},
        401: {"description": "Authentication failed - Invalid or missing API key"}
    }
)
async def api_get_bookmarks(
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get a list of bookmarks with optional filtering
    
    - **tag**: Filter bookmarks by tag name
    - **limit**: Maximum number of bookmarks to return (default: 50)
    - **offset**: Number of bookmarks to skip (default: 0)
    
    Authentication required: Bearer Token with valid API key
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    user = api_service.authenticate_api_key(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    bookmarks = bookmark_service.get_bookmarks(db, user.id, tag_filter=tag, limit=limit, offset=offset)
    return [bookmark_service.bookmark_to_dict(bookmark) for bookmark in bookmarks]

@app.post(
    "/api/bookmarks", 
    response_model=BookmarkResponse,
    summary="Create a new bookmark",
    description="Add a new bookmark with title, URL and optional tags",
    tags=["bookmarks"],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Bookmark created successfully"},
        401: {"description": "Authentication failed - Invalid or missing API key"},
        422: {"description": "Validation error - Invalid input data"}
    }
)
async def api_add_bookmark(
    bookmark_data: BookmarkCreateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Create a new bookmark
    
    - **url**: URL to bookmark (required)
    - **title**: Title of the bookmark (optional, will be auto-fetched if not provided)
    - **description**: Description of the bookmark (optional)
    - **tags**: Comma or space separated list of tags (optional)
    
    Authentication required: Bearer Token with valid API key
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    user = api_service.authenticate_api_key(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    bookmark = bookmark_service.add_bookmark(
        db, user.id,
        bookmark_data.url,
        bookmark_data.title,
        bookmark_data.description,
        bookmark_data.tags
    )
    
    return bookmark_service.bookmark_to_dict(bookmark)

@app.get(
    "/api/tags", 
    response_model=List[TagResponse],
    summary="Get tag cloud",
    description="Retrieve all tags with usage statistics for tag cloud visualization",
    tags=["tags"],
    responses={
        200: {"description": "List of tags with usage statistics"},
        401: {"description": "Authentication failed - Invalid or missing API key"}
    }
)
async def api_get_tags(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get tag cloud with usage statistics
    
    Returns all tags with their usage count and display size for tag cloud visualization
    
    Authentication required: Bearer Token with valid API key
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    user = api_service.authenticate_api_key(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return bookmark_service.get_tag_cloud(db, user.id)

@app.delete(
    "/api/bookmarks/{bookmark_id}", 
    summary="Delete a bookmark",
    description="Delete a bookmark by its ID",
    tags=["bookmarks"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Bookmark deleted successfully"},
        401: {"description": "Authentication failed - Invalid or missing API key"},
        404: {"description": "Bookmark not found"}
    }
)
async def api_delete_bookmark(
    bookmark_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Delete a bookmark by ID
    
    - **bookmark_id**: ID of the bookmark to delete
    
    Authentication required: Bearer Token with valid API key
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    user = api_service.authenticate_api_key(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    success = bookmark_service.delete_bookmark(db, bookmark_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    return None

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
