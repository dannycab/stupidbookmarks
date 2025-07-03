# StupidBookmarks

> **Vibe Coding Project Notice**  
> This project is developed in a freeform, improvisational, and experimental style. No pull requests will be honored.

A fast, minimalistic bookmark manager built with FastAPI and Tailwind CSS. Single-user system with API keys for external access.

🌐 **Live Demo**: Coming Soon  
🔗 **GitHub**: https://github.com/user/stupidbookmarks

## Features

• 🚀 **Fast**: Built with FastAPI for high performance  
• 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS  
• 📱 **Mobile-friendly**: Works great on all devices  
• 🔐 **Single User**: Simple authentication system  
• 🔖 **Smart Bookmarking**: Auto-fetch page titles and metadata  
• 🏷️ **Tag System**: Organize bookmarks with tags and tag cloud  
• 📊 **Admin Dashboard**: Statistics, password management, and settings  
• 🔑 **API Keys**: Secure API access for external integrations  
• 🌙 **Dark Mode**: Beautiful dark/light theme toggle  
• 💾 **SQLite**: Lightweight, zero-config storage  
• 📡 **REST API**: Full API for bookmark management  

## Tech Stack

• **Backend**: FastAPI (Python async web framework)  
• **Frontend**: Jinja2 templates + Tailwind CSS  
• **Database**: SQLite with SQLAlchemy ORM  
• **Authentication**: Simple password-based auth with API keys  
• **Styling**: Tailwind CSS with dark mode support  

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

3. **Open your browser** and go to `http://localhost:8000`

4. **Login** with the default password `admin`

5. **Start bookmarking!**

## Docker Deployment

Coming soon! Docker support will be added for easy deployment.

## API Usage

### Authentication

All API endpoints require an API key in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/bookmarks
```

### Endpoints

• `GET /api/bookmarks` - List bookmarks  
• `POST /api/bookmarks` - Add bookmark  
• `GET /api/tags` - Get tag cloud  

Full API documentation available at `/docs` when running the application.

## Features in Detail

### Smart Bookmarking
- Auto-fetch page titles when URL is provided
- Tag-based organization with visual tag cloud
- Rich descriptions and metadata

### Admin Dashboard
- Bookmark statistics and analytics
- Password management
- API key generation and management
- Quick functions and shortcuts

### Tag System
- Dynamic tag cloud with size based on usage
- Easy filtering by tags
- Tag-specific bookmark views

### API Integration
- RESTful API for external access
- Secure API key authentication
- JSON responses for easy integration

## Development

### Running in development mode:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure:
```
stupidbookmarks/
├── main.py              # FastAPI application entry point
├── models/              # Database models
│   ├── database.py      # Database configuration
│   └── models.py        # SQLAlchemy models
├── services/            # Business logic
│   ├── auth_service.py  # Authentication service
│   ├── bookmark_service.py # Bookmark management
│   └── api_service.py   # API key management
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Base template with navigation
│   ├── login.html       # Login page
│   ├── index.html       # Main bookmarks page
│   ├── tag.html         # Tag-specific bookmarks
│   └── admin.html       # Admin dashboard
├── data/                # SQLite database (auto-created)
├── requirements.txt     # Python dependencies
└── version.py          # Version information
```

## Default Setup

- **Default username**: admin
- **Default password**: admin (change this immediately!)
- **Database**: SQLite file in `./data/stupidbookmarks.db`
- **Port**: 8000

## Security Notes

- Change the default password immediately after first login
- Generate unique API keys for different applications
- Consider using HTTPS in production
- The session system is cookie-based (upgrade for production use)

## Contributing

This is a "vibe coding" project - feel free to fork and customize to your heart's content! If you have feature requests or bugs, please open an issue and I'll vibe code it (maybe it works, maybe not). Thanks for understanding!

## License

MIT License - do whatever you want with it!

---

**Made with ❤️ in Michigan**
