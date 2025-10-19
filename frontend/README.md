# AquaChain Consumer Dashboard

A React-based Progressive Web Application for real-time water quality monitoring and analysis.

## Features

- **Mobile-First Design**: Responsive layout optimized for mobile devices
- **Real-Time Monitoring**: Live water quality status with color-coded indicators
- **Historical Data**: Interactive charts and trend analysis
- **Service Requests**: Request and track technician services
- **Progressive Web App**: Installable on mobile devices with offline capabilities
- **Role-Based Access**: Secure authentication with AWS Cognito

## Technology Stack

- **Frontend**: React 18 with TypeScript
- **Styling**: Tailwind CSS for responsive design
- **Authentication**: AWS Amplify with Cognito
- **Charts**: Recharts for data visualization
- **Routing**: React Router with protected routes
- **PWA**: Service worker for offline functionality

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- AWS account with Cognito User Pool configured

### Installation

1. Clone the repository and navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment configuration:
```bash
cp .env.example .env.development
```

4. Update environment variables in `.env.development` with your AWS configuration:
```
REACT_APP_AWS_REGION=your-aws-region
REACT_APP_USER_POOL_ID=your-user-pool-id
REACT_APP_USER_POOL_CLIENT_ID=your-client-id
REACT_APP_API_ENDPOINT=your-api-endpoint
```

### Development

Start the development server:
```bash
npm start
```

The application will open at [http://localhost:3000](http://localhost:3000).

### Building for Production

Create a production build:
```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

### Testing

Run the test suite:
```bash
npm test
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Auth/           # Authentication components
│   └── Layout/         # Layout components
├── contexts/           # React contexts (Auth, etc.)
├── pages/              # Page components
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── App.tsx             # Main application component
```

## Authentication

The application uses AWS Cognito for authentication with support for:
- Email/password authentication
- Google OAuth integration
- Role-based access control (Consumer, Technician, Administrator)
- JWT token management

For development, you can use any email/password combination to log in.

## PWA Features

The application is configured as a Progressive Web App with:
- Service worker for offline functionality
- Web app manifest for installation
- Responsive design for mobile devices
- Push notification support (when implemented)

## Environment Configuration

The application supports multiple environments:
- `.env.development` - Development environment
- `.env.production` - Production environment
- `.env.example` - Template for environment variables

## Contributing

1. Follow the existing code style and conventions
2. Use TypeScript for type safety
3. Write responsive components with mobile-first approach
4. Include proper error handling and loading states
5. Test components thoroughly before submitting

## Deployment

The application can be deployed to:
- AWS S3 + CloudFront
- Netlify
- Vercel
- Any static hosting service

For AWS deployment, use the build artifacts from `npm run build`.