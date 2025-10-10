# QMS Application Architecture

## Overview
This is a professional Quality Management System built with FastAPI, SQLite, and Jinja2 templates following best practices for scalability and maintainability.

## Architecture Layers

### 1. Presentation Layer
- **Jinja2 Templates**: Server-side rendered HTML templates
- **Static Files**: CSS, JavaScript, images
- **Routes**: FastAPI route handlers

### 2. Business Logic Layer (Services)
- **UserService**: User management operations
- **DMTService**: DMT record operations with report numbering
- **AuditService**: Audit logging operations
- **Benefits**: 
  - Separation of concerns
  - Reusable business logic
  - Easier testing
  - Centralized validation

### 3. Data Access Layer
- **Database Connection**: SQLite connection management
- **Models**: Pydantic schemas for validation
- **Benefits**:
  - Type safety
  - Input validation
  - Clear data contracts

### 4. Core Layer
- **Dependencies**: Dependency injection for services
- **Logging**: Centralized logging configuration
- **Config**: Environment-based configuration

## Design Patterns

### Service Layer Pattern
All business logic is encapsulated in service classes:
- `UserService`: User CRUD and authentication
- `DMTService`: DMT record management
- `AuditService`: Audit trail management

### Dependency Injection
FastAPI's dependency injection system provides:
- Database connections
- Service instances
- Current user information
- Role-based access control

### Repository Pattern (Implicit)
Services act as repositories, abstracting database operations.

## Security Features

### Authentication
- Password hashing with bcrypt
- Session-based authentication
- Secure session cookies

### Authorization
- Role-based access control (RBAC)
- Permission checking at route level
- User-specific data filtering

### Audit Trail
- All operations logged
- User tracking
- Timestamp recording

## Scalability Considerations

### Database
- Connection pooling ready
- Prepared statements (SQL injection prevention)
- Transaction management
- Easy migration to PostgreSQL/MySQL

### Code Organization
- Modular structure
- Clear separation of concerns
- Easy to add new features
- Service layer allows for caching

### Configuration
- Environment-based settings
- Easy deployment configuration
- Secrets management ready

### Logging
- Structured logging
- Multiple log levels
- File and console output
- Easy integration with log aggregation tools

## API Structure

\`\`\`
/                       - Home/Dashboard
/auth/login            - Login page
/auth/logout           - Logout
/auth/admin/users      - User management (Admin only)
/dmt/                  - DMT records list
/dmt/new               - Create DMT record
/dmt/{id}/edit         - Edit DMT record
/audit/logs            - Audit logs (Admin/Supervisor)
\`\`\`

## Data Flow

1. **Request** → Route Handler
2. **Route Handler** → Dependency Injection (get user, services)
3. **Service Layer** → Business Logic + Validation
4. **Database Layer** → Data Operations
5. **Response** → Template Rendering or JSON

## Testing Strategy

### Unit Tests
- Service layer methods
- Validation logic
- Business rules

### Integration Tests
- API endpoints
- Database operations
- Authentication flow

### End-to-End Tests
- User workflows
- Role-based access
- DMT tracking

## Future Enhancements

### Performance
- Redis caching for sessions
- Database query optimization
- Connection pooling

### Features
- API versioning
- RESTful API endpoints
- WebSocket for real-time updates
- Export to Excel/PDF

### Deployment
- Docker containerization
- CI/CD pipeline
- Health checks
- Monitoring integration

## Development Guidelines

### Adding New Features
1. Create Pydantic schemas in `app/models/schemas.py`
2. Create service class in `app/services/`
3. Add routes in appropriate module
4. Add templates in `jinja_templates/`
5. Update dependencies if needed

### Code Style
- Follow PEP 8
- Type hints for all functions
- Docstrings for classes and methods
- Meaningful variable names

### Error Handling
- Use try-except blocks
- Log errors appropriately
- Return meaningful error messages
- Use HTTP status codes correctly

### Security
- Never commit secrets
- Use environment variables
- Validate all inputs
- Sanitize user data
- Use parameterized queries
