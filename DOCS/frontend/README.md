# AquaChain Frontend

**React-based Progressive Web Application for real-time water quality monitoring**

---

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Access at http://localhost:3000
# Login: demo@aquachain.com / demo123
```

### Production Build

```bash
# Build for production
npm run build

# Test production build
npm run serve
```

---

## 📋 Features

### Core Features
- ✅ Real-time water quality monitoring
- ✅ Multi-role dashboards (Admin/Technician/Consumer)
- ✅ Interactive charts and data visualization
- ✅ Alert management system
- ✅ Service request tracking
- ✅ Data export functionality
- ✅ Progressive Web App (PWA)

### Technical Features
- ✅ Mobile-first responsive design
- ✅ AWS Cognito authentication
- ✅ Real-time WebSocket updates
- ✅ Offline capability
- ✅ Performance optimized (<3s load time)
- ✅ Accessibility compliant (WCAG 2.1 AA)

---

## 🛠️ Tech Stack

**Core:**
- React 19.2.0
- TypeScript 4.9.5
- Tailwind CSS 3.4.18

**State Management:**
- React Context API
- TanStack Query 5.90.5

**UI Components:**
- Headless UI 2.2.9
- Heroicons 2.2.0
- Recharts 3.3.0

**Authentication:**
- AWS Amplify 6.15.7
- AWS Cognito

**Build Tools:**
- Create React App
- CRACO (for customization)
- Webpack 5

---

## 📁 Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── Admin/       # Admin dashboard
│   │   ├── Dashboard/   # Shared dashboard components
│   │   ├── Technician/  # Technician dashboard
│   │   ├── Auth/        # Authentication components
│   │   └── ...
│   ├── contexts/        # React contexts
│   ├── hooks/           # Custom hooks
│   ├── pages/           # Page components
│   ├── services/        # API services
│   ├── types/           # TypeScript types
│   ├── utils/           # Utility functions
│   └── App.tsx          # Main app component
├── .env.example         # Environment variables template
├── package.json         # Dependencies
└── README.md            # This file
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env.local` file:

```env
# AWS Configuration
REACT_APP_AWS_REGION=ap-south-1
REACT_APP_USER_POOL_ID=ap-south-1_XXXXXXXXX
REACT_APP_USER_POOL_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
REACT_APP_API_ENDPOINT=https://your-api.execute-api.ap-south-1.amazonaws.com/dev

# Optional
REACT_APP_WEBSOCKET_ENDPOINT=wss://your-websocket-api
REACT_APP_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

### Development Mode

For local development without AWS:

```env
# .env.development
REACT_APP_USE_MOCK_AUTH=true
REACT_APP_API_ENDPOINT=http://localhost:3002
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- AuthService.test.ts
```

### Test Coverage

Current coverage: **80%+**

---

## 🎨 Development

### Available Scripts

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Run linter
npm run lint

# Format code
npm run format

# Analyze bundle size
npm run analyze
```

### Code Style

- **ESLint** for code quality
- **Prettier** for formatting
- **TypeScript** for type safety

---

## 🚀 Deployment

### AWS Deployment

See main [PROJECT_REPORT.md](../PROJECT_REPORT.md) Appendix J for complete deployment guide.

**Quick deploy:**
```bash
cd ../infrastructure/cdk
cdk deploy AquaChain-LandingPage-dev
```

### Manual Deployment

```bash
# Build
npm run build

# Deploy to S3
aws s3 sync build/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

---

## 🔐 Authentication

### AWS Cognito Setup

1. **Create User Pool** in AWS Cognito
2. **Create App Client** (no secret)
3. **Configure** environment variables
4. **Enable** email verification

### Demo Users

**Local Development:**
- Email: `demo@aquachain.com`
- Password: `demo123`
- OTP: `123456`

**Production:**
- Create users via AWS Cognito Console
- Or use signup flow in app

---

## 📊 Performance

### Metrics

- **First Contentful Paint:** <1.8s
- **Largest Contentful Paint:** <2.5s
- **Time to Interactive:** <3.5s
- **Lighthouse Score:** 92/100

### Optimizations

- Code splitting
- Lazy loading
- Image optimization
- Bundle size optimization
- Caching strategies

See [PROJECT_REPORT.md](../PROJECT_REPORT.md) Appendix N for details.

---

## 🐛 Troubleshooting

### Common Issues

**Port 3000 already in use:**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

**Dependencies not installing:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Build fails:**
```bash
# Clear cache
npm run clean
npm install
npm run build
```

**Authentication not working:**
- Check `.env.local` configuration
- Verify AWS Cognito User Pool ID
- Check network connectivity

---

## 📚 Documentation

### Main Documentation

All comprehensive documentation is in:
- **[../PROJECT_REPORT.md](../PROJECT_REPORT.md)** - Complete technical guide

### Quick Links

- **Architecture:** PROJECT_REPORT.md Section 6
- **Deployment:** PROJECT_REPORT.md Appendix J
- **Performance:** PROJECT_REPORT.md Appendix N
- **Troubleshooting:** PROJECT_REPORT.md Appendix M

---

## 🔧 Advanced Configuration

### Custom Build

Edit `craco.config.js` for webpack customization:

```javascript
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Custom webpack config
      return webpackConfig;
    }
  }
};
```

### PWA Configuration

Edit `public/manifest.json` for PWA settings:

```json
{
  "short_name": "AquaChain",
  "name": "AquaChain Water Quality Monitor",
  "icons": [...],
  "start_url": ".",
  "display": "standalone"
}
```

---

## 📦 Dependencies

### Core Dependencies

```json
{
  "react": "^19.2.0",
  "typescript": "^4.9.5",
  "tailwindcss": "^3.4.18",
  "@tanstack/react-query": "^5.90.5",
  "aws-amplify": "^6.15.7",
  "recharts": "^3.3.0"
}
```

### Dev Dependencies

```json
{
  "@testing-library/react": "^13.4.0",
  "eslint": "^8.57.0",
  "prettier": "^3.0.0"
}
```

---

## 🤝 Contributing

### Development Workflow

1. Create feature branch
2. Make changes
3. Run tests: `npm test`
4. Run linter: `npm run lint`
5. Commit changes
6. Create pull request

### Code Standards

- Follow TypeScript best practices
- Write tests for new features
- Update documentation
- Follow existing code style

---

## 📄 License

Proprietary - AquaChain Development Team

---

## 📞 Support

### Documentation
- **Main Guide:** [PROJECT_REPORT.md](../PROJECT_REPORT.md)
- **Quick Start:** [GET_STARTED.md](../GET_STARTED.md)
- **Troubleshooting:** PROJECT_REPORT.md Appendix M

### Common Commands

```bash
# Development
npm start

# Production build
npm run build

# Tests
npm test

# Lint
npm run lint
```

---

**Version:** 1.1  
**Last Updated:** November 5, 2025  
**Status:** Production Ready

**For complete documentation, see [PROJECT_REPORT.md](../PROJECT_REPORT.md)**
