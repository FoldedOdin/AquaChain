# Demo Users - Development Server

## Available Users

The development server comes with pre-configured demo users for testing different roles.

### Admin Users

#### 1. Demo Admin
- **Email**: `demo@aquachain.com`
- **Password**: `demo1234`
- **Role**: Administrator
- **Access**: Full system access, admin dashboard

#### 2. Admin User
- **Email**: `admin@aquachain.com`
- **Password**: `admin1234`
- **Role**: Administrator
- **Access**: Full system access, admin dashboard

### Technician User

#### Demo Technician
- **Email**: `tech@aquachain.com`
- **Password**: `tech1234`
- **Role**: Technician
- **Access**: Technician dashboard, task management

### Consumer User

#### Demo Consumer
- **Email**: `user@aquachain.com`
- **Password**: `user1234`
- **Role**: Consumer
- **Access**: Consumer dashboard, device management, water quality monitoring

## How to Use

1. **Start the development server**:
   ```bash
   npm run start:full
   ```

2. **Navigate to**: http://localhost:3000

3. **Login** with any of the demo accounts above

4. **Test different roles**:
   - Login as Admin to access admin features
   - Login as Technician to manage tasks
   - Login as Consumer to monitor water quality

## Features by Role

### Admin Dashboard
- System health monitoring
- User management
- Device fleet status
- Performance metrics
- Alert analytics
- System configuration

### Technician Dashboard
- Assigned tasks list
- Task status management (Accept, Start, Complete)
- Task filtering and search
- Recent activity tracking
- Performance metrics
- Quick actions (Reports, Map, Inventory)
- Edit profile

### Consumer Dashboard
- Real-time water quality monitoring
- Device management
- Alert notifications
- Historical data charts
- Service request creation
- Device registration
- Edit profile

## User Data Storage

- Users are stored in `.dev-data.json` file
- Data persists across server restarts
- Email verification is auto-enabled for demo users
- All demo users are pre-verified

## Creating New Users

You can create new users via:

1. **Signup page**: http://localhost:3000/signup
2. **Dev API**: POST to `/api/auth/signup`
3. **Manually add to dev-server.js**: Edit the `demoUsers` array

## Resetting Demo Users

To reset all demo users to default:

1. Stop the dev server
2. Delete `.dev-data.json` file
3. Restart the dev server
4. Demo users will be recreated automatically

## Security Notes

⚠️ **Development Only**
- These are demo accounts for development/testing
- Passwords are simple and should NOT be used in production
- Email verification is bypassed for demo users
- Token validation is simplified

## Troubleshooting

### Can't Login?
- Check if dev server is running on port 3002
- Verify email and password are correct
- Check browser console for errors
- Try clearing browser cache/cookies

### User Not Found?
- Restart the dev server
- Check `.dev-data.json` exists
- Verify demo users are initialized (check server logs)

### Wrong Dashboard?
- Each role has a specific dashboard
- Check the user's role in the database
- Verify routing is working correctly

## API Endpoints

All demo users can access:
- `/api/auth/signin` - Login
- `/api/auth/validate` - Validate session
- `/api/profile/*` - Profile management
- `/api/notifications` - Notifications

Role-specific endpoints:
- **Admin**: `/api/admin/*`
- **Technician**: `/api/v1/technician/*`
- **Consumer**: `/api/devices/*`, `/api/water-quality/*`
