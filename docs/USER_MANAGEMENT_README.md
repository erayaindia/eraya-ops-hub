# User Management System

## Overview

The User Management System is a comprehensive solution for managing users in the Lumen Orders Webapp. It provides a modern, responsive interface for administrators to create, edit, delete, and manage user accounts with full CRUD operations connected to Supabase.

## Features

### 🎯 Core Functionality
- **List Users**: View all users with search, filtering, and pagination
- **Create Users**: Add new users with role-based access control
- **Edit Users**: Modify existing user information and permissions
- **Delete Users**: Remove users from the system (hard delete)
- **User Statistics**: Real-time dashboard with user counts and metrics

### 🔍 Advanced Features
- **Search & Filter**: Search across name, email, and phone fields
- **Role-based Filtering**: Filter by user roles (Owner, Admin, Manager, Employee, Packer)
- **Status Filtering**: Filter by user status (Active, Inactive, Suspended)
- **Sorting**: Sort by creation date, name, email, role, status, or last login
- **Pagination**: Configurable page sizes (10, 25, 50, 100 users per page)

### 🎨 User Experience
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: Optimistic UI updates with background reconciliation
- **Loading States**: Visual feedback during operations
- **Toast Notifications**: Success and error messages
- **Keyboard Shortcuts**: ESC to close modals, Enter to submit forms

## Architecture

### Backend Components

#### 1. Users Service (`app/services/users_service.py`)
- **Supabase Integration**: Uses the centralized Supabase client
- **Password Security**: Argon2 password hashing for secure storage
- **Data Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Graceful error handling with meaningful messages

#### 2. Admin Users Router (`app/routers/admin_users.py`)
- **API Endpoints**: RESTful API for all user operations
- **Authentication**: Role-based access control (Owner/Admin only)
- **CSRF Protection**: Built-in CSRF token validation
- **Input Validation**: Server-side validation of all inputs

#### 3. Database Schema
The system works with the existing `public.users` table in Supabase:
```sql
-- Required columns for user management
id (UUID, Primary Key)
name (Text)
email (Text, Unique)
password_hash (Text)
role (Text: owner, admin, manager, employee, packer)
status (Text: active, inactive, suspended)
phone (Text, Optional)
city (Text, Optional)
state (Text, Optional)
joining_date (Date, Optional)
last_login (Timestamp, Optional)
login_count (Integer, Optional)
created_at (Timestamp)
updated_at (Timestamp)
```

### Frontend Components

#### 1. HTML Template (`templates/admin_users.html`)
- **Modern UI**: Glass morphism design with gradients and animations
- **Responsive Layout**: Mobile-first design approach
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Modal System**: Inline forms for create/edit operations

#### 2. JavaScript (`static/js/admin_users.js`)
- **ES6+ Classes**: Modern JavaScript architecture
- **Optimistic Updates**: Immediate UI feedback with background sync
- **Error Handling**: Comprehensive error handling and user feedback
- **State Management**: URL-based state persistence

## Installation & Setup

### 1. Prerequisites
- Python 3.8+ with FastAPI
- Supabase project with `users` table
- Required Python packages (see `requirements.txt`)

### 2. Environment Variables
Ensure your `.env` file contains:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

### 3. Database Setup
The system automatically works with the existing `users` table. If you need to create it:
```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee' CHECK (role IN ('owner', 'admin', 'manager', 'employee', 'packer')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    phone TEXT,
    city TEXT,
    state TEXT,
    joining_date DATE,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_role ON public.users(role);
CREATE INDEX idx_users_status ON public.users(status);
CREATE INDEX idx_users_created_at ON public.users(created_at);
```

## Usage

### Accessing the System
1. Navigate to `/admin/users` in your browser
2. Ensure you're logged in with Owner or Admin role
3. The system will automatically load existing users

### Creating a New User
1. Click the "Add User" button
2. Fill in the required fields:
   - **Name**: Full name of the user
   - **Email**: Unique email address
   - **Role**: User's role in the system
   - **Status**: Account status (Active/Inactive/Suspended)
   - **Password**: Secure password (minimum 6 characters)
3. Click "Save User"

### Editing a User
1. Click the "Edit" button on any user row
2. Modify the desired fields
3. **Password**: Leave blank to keep existing password
4. Click "Save User"

### Deleting a User
1. Click the "Delete" button on any user row
2. Confirm the deletion in the modal
3. User will be permanently removed from the system

### Searching and Filtering
- **Search**: Type in the search box to find users by name, email, or phone
- **Role Filter**: Select specific roles to filter the user list
- **Status Filter**: Filter by account status
- **Sorting**: Choose how to sort the results
- **Pagination**: Navigate through large user lists

## Security Features

### Authentication & Authorization
- **Session-based Auth**: Uses existing session management system
- **Role-based Access**: Only Owner and Admin users can access
- **CSRF Protection**: Built-in CSRF token validation
- **Input Sanitization**: All inputs are sanitized and validated

### Password Security
- **Argon2 Hashing**: Industry-standard password hashing
- **No Plain Text**: Passwords are never stored or logged in plain text
- **Secure Validation**: Server-side password validation

### Data Protection
- **Selective Fields**: Only necessary user data is exposed
- **Audit Trail**: All operations are logged (optional)
- **Rate Limiting**: Built-in rate limiting for API endpoints

## API Endpoints

### GET `/api/users`
List users with search, filters, and pagination
```bash
GET /api/users?q=john&role=admin&status=active&page=1&limit=25
```

### POST `/api/users`
Create a new user
```bash
POST /api/users
Content-Type: application/x-www-form-urlencoded

name=John Doe&email=john@example.com&role=employee&status=active&password=securepass
```

### GET `/api/users/{id}`
Get a specific user by ID
```bash
GET /api/users/123e4567-e89b-12d3-a456-426614174000
```

### PATCH `/api/users/{id}`
Update an existing user
```bash
PATCH /api/users/123e4567-e89b-12d3-a456-426614174000
Content-Type: application/x-www-form-urlencoded

name=John Smith&role=manager
```

### DELETE `/api/users/{id}`
Delete a user
```bash
DELETE /api/users/123e4567-e89b-12d3-a456-426614174000
```

### GET `/api/users/stats/statistics`
Get user statistics for dashboard
```bash
GET /api/users/stats/statistics
```

## Testing

### Run the Test Suite
```bash
python test_user_management.py
```

This will test:
- Supabase connection
- User listing functionality
- User statistics
- Email existence checking
- Search functionality
- User creation and deletion

### Manual Testing
1. Start your FastAPI server
2. Navigate to `/admin/users`
3. Test all CRUD operations
4. Verify search, filtering, and pagination
5. Check responsive design on different screen sizes

## Troubleshooting

### Common Issues

#### 1. "Unauthorized" Error
- Ensure you're logged in with Owner or Admin role
- Check your session cookie is valid
- Verify the user exists in the database

#### 2. "Email already exists" Error
- The email address is already in use
- Use a different email or update the existing user

#### 3. "User not found" Error
- The user ID may be invalid
- Check if the user was deleted by another process

#### 4. Database Connection Issues
- Verify your Supabase credentials in `.env`
- Check network connectivity
- Ensure the `users` table exists

### Debug Mode
Enable debug logging by setting `DEBUG=True` in your `.env` file. This will provide detailed error messages and SQL queries.

## Performance Considerations

### Optimization Tips
1. **Indexes**: Ensure proper database indexes on frequently queried fields
2. **Pagination**: Use appropriate page sizes (25-50 users per page)
3. **Caching**: The system includes cache-busting headers for fresh data
4. **Lazy Loading**: User data is loaded on-demand

### Scalability
- The system is designed to handle thousands of users
- Pagination prevents memory issues with large datasets
- Background reconciliation ensures data consistency

## Future Enhancements

### Planned Features
- **Bulk Operations**: Import/export users via CSV
- **Advanced Filtering**: Date range filters, custom criteria
- **User Groups**: Organize users into teams or departments
- **Audit Logging**: Comprehensive activity tracking
- **API Rate Limiting**: Configurable rate limits per user

### Customization
- **Role Permissions**: Fine-grained permission system
- **Custom Fields**: User-defined additional fields
- **Workflow Integration**: Approval processes for user changes
- **Notification System**: Email alerts for user changes

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test script output
3. Check browser console for JavaScript errors
4. Verify database connectivity and permissions

## Contributing

To contribute to the User Management System:
1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure security best practices are maintained

---

**Note**: This system is designed to work seamlessly with the existing Lumen Orders Webapp infrastructure. All operations are logged and can be audited for compliance purposes.
