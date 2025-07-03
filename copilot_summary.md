# StupidBookmarks Project Documentation

## Project Overview

**StupidBookmarks** is a fast, minimalistic single-user bookmark manager built with FastAPI and Tailwind CSS. It's part of the "Stupid Apps" suite (alongside StupidRSS) and follows a "vibe coding" philosophy - freeform, improvisational, and experimental development style.

### Key Features
- 🔖 Single-user bookmark management with auto-title fetching
- 🏷️ Tag-based organization with visual tag cloud
- 🎨 Modern Tailwind CSS UI with dark/light mode toggle
- 📊 Admin dashboard with statistics and management tools
- 🔑 API key system for external integrations
- 📱 Mobile-responsive design
- 🚀 FastAPI backend with async performance

## Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.13)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Jinja2 templates + Tailwind CSS + Vanilla JavaScript
- **Styling**: Tailwind CSS with custom dark/light theme system
- **Deployment**: Uvicorn server

### Project Structure
```
stupidbookmarks/
├── main.py                 # FastAPI application with all routes
├── models/
│   ├── __init__.py
│   ├── database.py         # Database config and session management
│   └── models.py           # SQLAlchemy models (User, Bookmark, Tag, APIKey)
├── services/
│   ├── __init__.py
│   ├── auth_service.py     # Authentication and user management
│   ├── bookmark_service.py # Bookmark CRUD and title fetching
│   └── api_service.py      # API key management and statistics
├── templates/
│   ├── base.html          # Base template with dark/light theme
│   ├── login.html         # Login page
│   ├── index.html         # Main bookmarks page
│   ├── admin.html         # Admin dashboard
│   └── tag.html           # Tag-filtered bookmark view
├── data/                  # SQLite database storage (auto-created)
├── requirements.txt       # Python dependencies
├── README.md             # User documentation
└── .gitignore           # Git ignore rules
```

### Database Models
- **User**: Single admin user with password management
- **Bookmark**: URL, title, description, timestamps, user relationship
- **Tag**: Name, color, user relationship
- **APIKey**: Secure API access tokens with user relationship
- **user_tags**: Many-to-many relationship table

### Services Architecture
- **AuthService**: Password hashing, session management, user authentication
- **BookmarkService**: CRUD operations, title fetching, tag management, statistics
- **APIService**: API key generation, validation, statistics

## Current Status

### ✅ Completed Features
1. **Core Functionality**
   - User authentication (login/logout)
   - Bookmark CRUD operations
   - Auto-title fetching with multiple fallback strategies
   - Tag management and filtering
   - Tag cloud visualization

2. **UI/UX**
   - Dark/light mode toggle (defaults to dark)
   - Responsive Tailwind CSS design
   - Clean, minimalist interface matching StupidRSS aesthetic
   - Mobile-friendly layout

3. **Admin Features**
   - Password change functionality
   - API key generation and management
   - Statistics dashboard
   - User management

4. **API System**
   - RESTful API endpoints for bookmarks
   - API key authentication
   - JSON responses for external integrations

### 🚧 Known Issues & Open GitHub Issues

**GitHub Issues Created:**
1. **#1**: Export bookmarks to Netscape HTML format (Medium, 2-3hrs)
2. **#2**: API documentation at /api/docs (High, 3-4hrs)
3. **#3**: Add StupidRSS-style colors to links/buttons (Medium, 2-3hrs)
4. **#4**: Fix active tag filter visibility in dark mode (High, 1-2hrs) ⭐ **EASIEST**
5. **#5**: Tag autocomplete suggestions (Medium, 3-4hrs)

**Technical Debt:**
- Password change needs must_change_password field implementation
- API documentation endpoint missing
- Static files directory not properly configured
- Some bcrypt compatibility warnings

## Development Context

### Recent Development Session
- Set up complete project structure from scratch
- Implemented auto-title fetching with robust error handling
- Created GitHub repository with initial release
- Fixed dark mode default behavior
- Identified and created GitHub issues for remaining features

### Design Philosophy
- **"Vibe Coding"**: Experimental, improvisational development
- **Minimalism**: Clean, fast, no-frills interface
- **Single User**: Optimized for personal use, not multi-tenant
- **StupidRSS Aesthetic**: Consistent with existing "Stupid Apps" suite

### Key Implementation Details

#### Auto-Title Fetching
- Multi-strategy approach with different browser headers
- Fallback chain: Chrome → Firefox → Bot-friendly headers
- Multiple title sources: `<title>`, `og:title`, `twitter:title`, `<h1>`
- Robust error handling with timeouts
- Handles encoding issues and malformed HTML

#### Authentication
- Single admin user model
- Bcrypt password hashing
- Session-based authentication
- API key system for external access

#### Database
- SQLite for simplicity and portability
- SQLAlchemy ORM with relationships
- Auto-migration on startup
- User-scoped data isolation

## Development Guidelines

### When Working on Issues

**Easiest Starting Point**: Issue #4 (Tag filter visibility)
- Pure CSS/styling fix
- Immediate visual feedback
- No backend changes required
- Good momentum builder

**Code Style**:
- Follow existing FastAPI patterns
- Use type hints consistently
- Service layer for business logic
- Template inheritance for UI consistency

**Testing Approach**:
- Manual testing in browser
- Test both dark/light modes
- Verify mobile responsiveness
- Check API endpoints with different clients

### Common Development Tasks

**Adding New Routes**:
```python
@app.get("/new-route")
async def new_route(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return templates.TemplateResponse("template.html", {"request": request})
```

**Database Operations**:
- Always use service layer methods
- Handle database sessions properly
- Use db.commit() for persistence
- Refresh objects after commits

**Frontend Changes**:
- Extend base.html for consistency
- Use Tailwind classes for styling
- Test dark/light mode variants
- Maintain responsive design

## Environment Setup

### Development Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
# OR
uvicorn main:app --reload --port 8000
```

### Dependencies
- FastAPI, Uvicorn, Jinja2 (web framework)
- SQLAlchemy, sqlite3 (database)
- bcrypt, passlib (authentication)
- requests, beautifulsoup4 (title fetching)
- python-multipart (form handling)

## Future Roadmap

### Short Term (Current Issues)
- Fix tag filter visibility (#4)
- Add colorful button styling (#3)
- Implement API documentation (#2)

### Medium Term
- Export functionality (#1)
- Tag autocomplete (#5)
- Import from browser bookmarks
- Bulk operations

### Long Term
- Search functionality
- Bookmark archiving
- Browser extension
- Mobile app

## Notes for AI Assistant

**When asked to work on this project:**
1. **Start with Issue #4** for quick wins
2. **Check existing code patterns** before implementing
3. **Test both dark/light modes** for UI changes
4. **Use service layer** for business logic
5. **Follow FastAPI conventions** for new endpoints
6. **Maintain StupidRSS aesthetic** for styling
7. **Consider mobile responsiveness** for UI changes

**Key Files to Understand:**
- `main.py`: All routes and FastAPI setup
- `services/bookmark_service.py`: Core bookmark logic
- `templates/base.html`: Theme system and layout
- `models/models.py`: Database schema

**Common Patterns:**
- Service injection via Depends()
- Template response with request context
- User authentication on protected routes
- Database session management