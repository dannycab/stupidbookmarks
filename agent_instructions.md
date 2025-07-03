# Agent Instructions for StupidBookmarks Project

## Core Principles

### Efficiency & Non-Redundancy
- **Avoid Redundant Operations**: Before suggesting actions, check if they've already been completed
- **Prioritize Batch Operations**: Group similar tasks (e.g., file edits, git operations) to minimize context switching
- **Reuse Existing Code**: Leverage patterns and functions already present in the codebase
- **Minimize Tool Calls**: Use comprehensive queries instead of multiple small ones

### Generic Problem Solving
- **Abstract Solutions**: Design solutions that can be reused for similar problems
- **Follow Existing Patterns**: Maintain consistency with the project's architectural patterns
- **Parameterize Hard-coded Values**: Use configuration or environment variables where appropriate
- **Create Helper Functions/Services**: For operations that might be needed in multiple places

### Performance Optimization
- **Minimize Database Queries**: Use joins, eager loading, and efficient queries
- **Consider Caching**: For frequently accessed, rarely-changed data
- **Optimize Title Fetching**: Use async when appropriate, implement timeouts, handle failures gracefully
- **Monitor Response Times**: Suggest performance improvements for slow endpoints
- **Optimize Frontend**: Minimize DOM operations, use efficient CSS selectors, and lazy-load resources
- **Pagination**: Implement and optimize pagination for large collections of bookmarks
- **Import/Export**: Ensure efficient processing of large bookmark collections during import/export

### Security Best Practices
- **Validate All Inputs**: Server-side validation for all user inputs
- **Prevent SQL Injection**: Always use parameterized queries via SQLAlchemy
- **Secure Authentication**: Implement proper password hashing, session management, CSRF protection
- **API Security**: Validate API keys thoroughly, use rate limiting when necessary
- **XSS Prevention**: Escape user-generated content in templates
- **HTTPS**: Ensure secure connections for production deployments
- **Secure Headers**: Implement security headers for web protection

## Workflow Guidelines

### Development Process
1. **Understand Requirements** completely before implementation
2. **Create Feature Branch** for each distinct feature/fix
3. **Design Solution** considering extensibility and maintainability
4. **Implement Changes** following project patterns
5. **Test Thoroughly** before suggesting merge
6. **Document Changes** in code and project documentation
7. **Clean Up** branches after successful implementation

### Code Quality Standards
- **Type Hints**: Use Python type hints consistently
- **Error Handling**: Implement comprehensive error handling with meaningful messages
- **Logging**: Use appropriate logging levels instead of print statements
- **Comments**: Document complex logic, but prefer self-explanatory code
- **Tests**: Suggest tests for critical functionality

## Feature-Specific Guidelines

### Pagination
- **Consistent Experience**: Ensure pagination works consistently across all views (main, tag-filtered)
- **Efficient Queries**: Use limit/offset for efficient database access
- **Clear Navigation**: Provide intuitive navigation controls (prev/next, page numbers)
- **State Preservation**: Maintain filter states when navigating between pages

### Bookmark Import/Export
- **Standard Formats**: Support standard bookmark formats (Netscape HTML)
- **Error Handling**: Handle malformed input files gracefully
- **Progress Feedback**: Provide user feedback for long-running operations
- **Data Validation**: Validate imported data to ensure consistency
- **Security**: Sanitize imported data to prevent XSS and other security issues

### Project-Specific Guidelines

#### FastAPI Best Practices
- **Dependency Injection**: Use FastAPI's dependency system for services and database sessions
- **Path Operations**: Organize by resource and use appropriate HTTP methods
- **Response Models**: Define and use Pydantic models for API responses
- **Error Handling**: Use FastAPI's exception handlers for consistent error responses

#### Database Operations
- **Use Service Layer**: All database operations should go through service classes
- **Transaction Management**: Ensure proper transaction boundaries
- **Connection Pooling**: Configure appropriate pool sizes for production

#### UI/UX Considerations
- **Maintain Aesthetic**: Follow StupidRSS-inspired design principles
- **Dark/Light Mode**: Test all UI changes in both modes
- **Mobile Responsiveness**: Ensure all UI works on mobile devices
- **Accessibility**: Maintain basic accessibility standards
- **Loading States**: Implement appropriate loading indicators for async operations

## Task Prioritization

### High Priority
- Security issues
- Critical bugs affecting core functionality
- Performance issues affecting user experience

### Medium Priority
- Feature implementations from GitHub issues
- UI/UX improvements
- Documentation updates

### Low Priority
- Code refactoring without functional changes
- Minor styling adjustments
- Development tooling improvements

## Common Tasks Reference

### Adding New API Endpoints
```python
@app.get("/api/resource", tags=["api"])
async def get_resource(
    db: Session = Depends(get_db),
    api_key: str = Depends(api_service.validate_api_key)
):
    # Implementation
    return {"data": result}
```

### Adding New UI Routes
```python
@app.get("/new-page")
async def new_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return templates.TemplateResponse(
        "new_page.html", 
        {"request": request, "context": data}
    )
```

### Database Query Optimization
```python
# Inefficient
bookmarks = db.query(Bookmark).filter(Bookmark.user_id == user_id).all()
for bookmark in bookmarks:
    print(bookmark.tags)  # Triggers N+1 queries

# Efficient
bookmarks = db.query(Bookmark).filter(Bookmark.user_id == user_id).options(
    selectinload(Bookmark.tags)
).all()
```

## Final Reminders
- **Be Proactive**: Identify potential issues before they become problems
- **Consider Edge Cases**: Account for unusual inputs and error conditions
- **Communicate Clearly**: Explain the reasoning behind implementation choices
- **Balance Speed and Quality**: Aim for efficient solutions without sacrificing quality
- **Continuously Learn**: Adapt approach based on project evolution
