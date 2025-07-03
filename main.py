#!/usr/bin/env python3
"""
StupidBookmarks - A fast, minimalistic bookmark manager built with FastAPI and Tailwind CSS.

Vibe Coding Project Notice:
This project is developed in a freeform, improvisational, and experimental style.
"""

import os
from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from typing import Optional, List
import secrets
import hashlib
from datetime import datetime

from models.database import get_db, init_db
from models.models import User, Bookmark, Tag, APIKey, user_tags
from services.bookmark_service import BookmarkService
from services.auth_service import AuthService
from services.api_service import APIService
import version

# Initialize FastAPI app
app = FastAPI(
    title="StupidBookmarks", 
    description="A fast, minimalistic bookmark manager built with FastAPI and Tailwind CSS",
    version=version.__version__
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Services
bookmark_service = BookmarkService()
auth_service = AuthService()
api_service = APIService()

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
async def index(request: Request, tag: Optional[str] = None, db: Session = Depends(get_db)):
    """Main bookmarks page with optional tag filtering."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    bookmarks = bookmark_service.get_bookmarks(db, user.id, tag_filter=tag)
    tags = bookmark_service.get_tag_cloud(db, user.id)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "bookmarks": bookmarks,
        "tags": tags,
        "current_tag": tag,
        "user": user
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
async def tag_page(request: Request, tag_name: str, db: Session = Depends(get_db)):
    """Show bookmarks for a specific tag."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    bookmarks = bookmark_service.get_bookmarks(db, user.id, tag_filter=tag_name)
    tags = bookmark_service.get_tag_cloud(db, user.id)
    
    return templates.TemplateResponse("tag.html", {
        "request": request,
        "bookmarks": bookmarks,
        "tags": tags,
        "tag_name": tag_name,
        "user": user
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
    
    api_service.create_api_key(db, user.id, name)
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/api-keys/{key_id}/delete")
async def delete_api_key(key_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete an API key."""
    user = auth_service.get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    api_service.delete_api_key(db, key_id, user.id)
    return RedirectResponse(url="/admin", status_code=302)

# API routes
@app.get("/api/bookmarks")
async def api_get_bookmarks(
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """API endpoint to get bookmarks."""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    user = api_service.authenticate_api_key(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    bookmarks = bookmark_service.get_bookmarks(db, user.id, tag_filter=tag, limit=limit, offset=offset)
    return [bookmark_service.bookmark_to_dict(bookmark) for bookmark in bookmarks]

@app.post("/api/bookmarks")
async def api_add_bookmark(
    bookmark_data: dict,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """API endpoint to add a bookmark."""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    user = api_service.authenticate_api_key(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    bookmark = bookmark_service.add_bookmark(
        db, user.id,
        bookmark_data.get("url"),
        bookmark_data.get("title"),
        bookmark_data.get("description", ""),
        bookmark_data.get("tags", "")
    )
    
    return bookmark_service.bookmark_to_dict(bookmark)

@app.get("/api/tags")
async def api_get_tags(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """API endpoint to get tag cloud."""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    user = api_service.authenticate_api_key(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return bookmark_service.get_tag_cloud(db, user.id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
