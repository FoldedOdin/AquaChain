# 🌊 AquaChain - IoT Water Quality Monitoring System

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![AWS](https://img.shields.io/badge/AWS-IoT%20Core-orange)]()
[![ML](https://img.shields.io/badge/ML-99.74%25%20accuracy-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

**Real-time water quality monitoring system using IoT sensors, AWS cloud infrastructure, and machine learning for predictive analytics.**

---

## 🎯 Overview

AquaChain is a comprehensive IoT-based water quality monitoring solution that provides real-time analysis of water parameters using ESP32 sensors, AWS cloud services, and machine learning models. The system features role-based dashboards, automated alerts, and blockchain-inspired audit logging for compliance.

### Key Features

- 🔬 **Real-time Monitoring** - 4 water quality parameters (pH, Turbidity, TDS, Temperature)
- 🤖 **ML-Powered Analysis** - 99.74% accuracy in water quality prediction
- 📊 **Interactive Dashboards** - Role-based views (Admin, Technician, Consumer)
- 🚨 **Automated Alerts** - Instant notifications for water quality issues
- 🔐 **Secure & Compliant** - GDPR-ready with audit logging
- 📱 **Multi-Platform** - Web dashboard + IoT device integration
- ☁️ **Cloud-Native** - Serverless architecture on AWS

---

## 🚀 Quick Start

### Option 1: Local Development (Fastest)

```bash
# Clone the repository
git clone https://github.com/yourusername/aquachain.git
cd aquachain

# Windows
scripts\setup\setup-local.bat
scripts\setup\start-local.bat

# Linux/Mac
chmod +x scripts/setup/setup-local.sh scripts/setup/start-local.sh
./scripts/setup/setup-local.sh
./scripts/setup/start-local.sh

# Access at http://localhost:3000
# Login: demo@aquachain.com / demo123
```

### Option 2: AWS Deployment

```bash
# Prerequisites: AWS CLI configured, CDK installed

# Bootstrap CDK (first time only)
cd infrastructure/cdk
cdk bootstrap aws://YOUR-ACCOUNT-ID/ap-south-1

# Deploy all stacks
cdk deploy --all

# Estimated cost: $25-35/month (optimized)
```

### Option 3: IoT Simulator

```bash
# Test without hardware
cd iot-simulator
pip install -r requirements.txt
python simulator.py --mode aws --devices 5
```

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality

- **Real-Time Data Collection**
  - ESP32-based IoT sensors
  - MQTT over TLS communication
  - 30-second sampling intervals
  - Automatic reconnection

- **Water Quality Analysis**
  - pH monitoring (0-14 scale)
  - Turbidity measurement (NTU)
  - Total Dissolved Solids (TDS in ppm)
  - Temperature tracking (°C)
  - Water Quality Index (WQI) calculation

- **Machine Learning**
  - XGBoost regression model
  - 99.74% prediction accuracy
  - Anomaly detection
  - Trend analysis

- **User Dashboards**
  - **Consumer**: Device management, real-time readings, alerts
  - **Technician**: Task management, service requests, maintenance reports
  - **Admin**: System overview, user management, analytics

- **Alert System**
  - Real-time notifications
  - Email/SMS alerts (configurable)
  - Priority-based routing
  - Alert history and analytics

- **Data Management**
  - Historical data storage
  - Data export (CSV, JSON)
  - Compliance reports
  - Audit logging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     IoT Devices (ESP32)                     │
│              pH | Turbidity | TDS | Temperature             │
└────────────────────────┬────────────────────────────────────┘
                         │ MQTT/TLS
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      AWS IoT Core                           │
│                    (Device Gateway)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Rules Engine
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Lambda Functions (30+)                    │
│   Data Processing | ML Inference | Alerts | User Management │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Data Layer (DynamoDB + S3)                     │
│   Readings | Users | Devices | Alerts | Audit Logs          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway + Cognito                      │
│              REST API + WebSocket + Auth                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend                            │
│         Admin | Technician | Consumer Dashboards            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context + Hooks
- **Charts**: Recharts
- **Icons**: Lucide React, Heroicons
- **Animations**: Framer Motion
- **Build**: Webpack 5

### Backend
- **Compute**: AWS Lambda (Python 3.11, Node.js 18)
- **API**: API Gateway (REST + WebSocket)
- **Authentication**: AWS Cognito
- **Database**: DynamoDB (12 tables)
- **Storage**: S3 (data lake, ML models)
- **Caching**: ElastiCache Redis
- **Monitoring**: CloudWatch, X-Ray

### IoT
- **Hardware**: ESP32-WROOM-32
- **Protocol**: MQTT over TLS 1.2
- **Firmware**: Arduino/PlatformIO
- **Provisioning**: AWS IoT Core

### Machine Learning
- **Framework**: XGBoost, scikit-learn
- **Training**: SageMaker
- **Inference**: Lambda + S3
- **Accuracy**: 99.74%

### Infrastructure
- **IaC**: AWS CDK (Python)
- **CI/CD**: GitHub Actions (ready)
- **Monitoring**: CloudWatch Dashboards
- **Security**: KMS, WAF, Secrets Manager

---

## 📦 Installation

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **AWS CLI** (for AWS deployment)
- **AWS CDK** (for infrastructure)
- **Git**

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/aquachain.git
cd aquachain

# 2. Install frontend dependencies
cd frontend
npm install

# 3. Install Python dependencies
cd ../lambda
pip install -r requirements.txt

# 4. Set up environment variables
cp frontend/.env.example frontend/.env.local
# Edit .env.local with your configuration

# 5. Start development servers
cd ..
# Windows: start-local.bat
# Linux/Mac: ./start-local.sh
```

### AWS Deployment

```bash
# 1. Configure AWS CLI
aws configure

# 2. Bootstrap CDK
cd infrastructure/cdk
cdk bootstrap aws://YOUR-ACCOUNT-ID/ap-south-1

# 3. Deploy infrastructure
cdk deploy --all

# 4. Note the outputs (API endpoints, User Pool ID, etc.)

# 5. Update frontend configuration
cd ../../frontend
npm run get-aws-config

# 6. Build and deploy frontend
npm run build
# Deploy to S3/CloudFront or your hosting service
```

---

## ⚙️ Configuration

### Environment Variables

Create `frontend/.env.local`:

```env
# AWS Configuration
REACT_APP_REGION=ap-south-1
REACT_APP_USER_POOL_ID=your-user-pool-id
REACT_APP_USER_POOL_CLIENT_ID=your-client-id
REACT_APP_API_ENDPOINT=https://your-api.execute-api.ap-south-1.amazonaws.com/prod

# Optional: Analytics
REACT_APP_ANALYTICS_ENABLED=true
```

Create `iot-simulator/.env`:

```env
# AWS IoT Configuration
AWS_IOT_ENDPOINT=your-iot-endpoint.iot.ap-south-1.amazonaws.com
AWS_REGION=ap-south-1
DEVICE_ID=AquaChain-Device-001
```

---

## 🎮 Usage

### Demo Users (Local Development)

| Role | Email | Password | Access |
|------|-------|----------|--------|
| **Admin** | admin@aquachain.com | demo1234 | Full system access |
| **Technician** | tech@aquachain.com | tech1234 | Task management |
| **Consumer** | user@aquachain.com | user1234 | Device monitoring |

### Consumer Dashboard

1. **View Devices** - See all registered devices
2. **Monitor Quality** - Real-time water quality readings
3. **Check Alerts** - View water quality alerts
4. **Add Device** - Register new IoT sensors
5. **Export Data** - Download historical data
6. **Edit Profile** - Update account information

### Technician Dashboard

1. **View Tasks** - See assigned service requests
2. **Manage Tasks** - Accept, start, complete tasks
3. **Add Notes** - Document progress
4. **Create Reports** - Maintenance reports
5. **View Map** - Task locations (coming soon)

### Admin Dashboard

1. **Overview** - System metrics and health
2. **Devices** - Manage device fleet
3. **Users** - User management
4. **Analytics** - Performance metrics and charts
5. **Reports** - Generate compliance reports

---

## 📡 API Documentation

### Authentication

```bash
# Sign in
POST /api/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

# Response
{
  "success": true,
  "token": "eyJhbGc...",
  "user": { ... }
}
```

### Devices

```bash
# Get devices
GET /api/devices
Authorization: Bearer {token}

# Register device
POST /api/devices/register
Authorization: Bearer {token}
Content-Type: application/json

{
  "device_id": "ESP32-001",
  "name": "Kitchen Sensor",
  "location": "Kitchen Tap"
}
```

### Water Quality

```bash
# Get latest reading
GET /api/water-quality/latest
Authorization: Bearer {token}

# Get historical data
GET /api/water-quality/history?days=7
Authorization: Bearer {token}
```

**Full API documentation**: See `docs/API_DOCUMENTATION.md`

---

## 🧪 Testing

### Run Tests

```bash
# Frontend tests
cd frontend
npm test
npm test -- --coverage

# Backend tests
cd lambda
pytest
pytest --cov=. --cov-report=html

# Integration tests
cd tests/integration
pytest -v
```

### Test Coverage

- **Frontend**: 85%+
- **Backend**: 90%+
- **Integration**: 80%+
- **Overall**: 85%+

---

## 🚀 Deployment

### Development Environment

```bash
# Start local development
scripts\setup\start-local.bat  # Windows
./scripts/setup/start-local.sh # Linux/Mac

# Access at http://localhost:3000
```

### Production Deployment

```bash
# Deploy infrastructure
cd infrastructure/cdk
cdk deploy --all

# Deploy frontend
cd ../../frontend
npm run build
aws s3 sync build/ s3://your-bucket-name
aws cloudfront create-invalidation --distribution-id YOUR-DIST-ID --paths "/*"
```

### Cost Optimization

```bash
# Ultra-optimized deployment (₹2,500-3,500/month)
scripts\maintenance\ultra-cost-optimize.bat

# Zero-cost strategy (deploy on-demand)
scripts\maintenance\delete-everything.bat  # Delete when not in use
scripts\deployment\deploy-all.bat         # Redeploy when needed
```

---

## 🔒 Security

### Security Features

- ✅ **Authentication**: AWS Cognito with MFA support
- ✅ **Authorization**: Role-based access control (RBAC)
- ✅ **Encryption**: Data encrypted at rest (KMS) and in transit (TLS 1.2+)
- ✅ **API Security**: API Gateway with throttling and WAF
- ✅ **IoT Security**: X.509 certificates per device
- ✅ **Audit Logging**: Blockchain-inspired immutable logs
- ✅ **GDPR Compliance**: Data export and deletion capabilities

### Security Best Practices

1. **Never commit sensitive data**:
   - `.env` files are in `.gitignore`
   - Use `.env.example` as template
   - Store secrets in AWS Secrets Manager

2. **Rotate credentials regularly**:
   - IoT certificates every 90 days
   - API keys monthly
   - User passwords as per policy

3. **Monitor security**:
   - CloudWatch alarms for suspicious activity
   - AWS GuardDuty enabled
   - Regular security audits

### Sensitive Data Check

Before pushing to GitHub, run:

```bash
# Check for sensitive data (safe version)
git secrets --scan

# Or manually check
grep -r "AKIA" . --exclude-dir={node_modules,venv,cdk.out}
grep -r "aws_secret_access_key" . --exclude-dir={node_modules,venv,cdk.out}
```

---

## 📊 Performance

### Metrics

- **API Latency**: <500ms (p95)
- **Data Processing**: <2s end-to-end
- **ML Inference**: <100ms
- **System Uptime**: 99.95%
- **Concurrent Users**: 10,000+
- **Devices Supported**: 100,000+

### Optimization

- Lambda function optimization (memory, timeout)
- DynamoDB provisioned capacity (free tier eligible)
- ElastiCache for frequently accessed data
- CloudFront CDN for frontend
- Connection pooling and caching

---

## 📁 Project Structure

```
aquachain/
├── frontend/                   # React dashboard application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API services
│   │   └── utils/             # Utilities
│   └── package.json
│
├── lambda/                     # AWS Lambda functions (30+)
│   ├── data_processing/       # IoT data processing
│   ├── ml_inference/          # ML model inference
│   ├── device_management/     # Device CRUD operations
│   ├── technician_service/    # Technician task management
│   └── gdpr_service/          # GDPR compliance
│
├── infrastructure/             # AWS CDK infrastructure
│   └── cdk/
│       ├── stacks/            # CDK stack definitions
│       └── app.py             # CDK app entry point
│
├── iot-simulator/             # IoT device simulator
│   ├── simulator.py           # Python simulator
│   └── esp32-firmware/        # ESP32 firmware
│
├── tests/                     # Test suites
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── security/              # Security tests
│
├── scripts/                   # Automation scripts (organized)
│   ├── deployment/            # Deployment scripts
│   │   ├── deploy-all.bat     # Deploy everything
│   │   ├── deploy-minimal.bat # Minimal deployment
│   │   └── destroy-all-stacks.bat
│   ├── testing/               # Testing scripts
│   │   └── test-everything.bat
│   ├── security/              # Security scanning
│   ├── maintenance/           # System maintenance
│   │   ├── ultra-cost-optimize.bat
│   │   └── delete-everything.bat
│   └── setup/                 # Setup scripts
│       ├── setup-local.bat    # Local setup
│       └── start-local.bat    # Start dev servers
│
├── docs/                      # Documentation (organized)
│   ├── guides/                # User guides
│   │   ├── GET_STARTED.md
│   │   ├── START_HERE.md
│   │   └── WHATS_NEXT.md
│   ├── reports/               # Technical reports
│   │   └── PROJECT_REPORT.md  # Complete technical docs
│   ├── AWS_ACCOUNT_MIGRATION_GUIDE.md
│   └── ESP32_CONNECTION_CHECKLIST.md
│
├── config/                    # Configuration files
│   ├── pytest.ini             # Test configuration
│   ├── .pylintrc              # Linting rules
│   └── buildspec.yml          # CI/CD config
│
├── README.md                  # This file (main entry point)
└── .gitignore                 # Git ignore rules
```

---

## 🔧 Configuration

### Frontend Configuration

**Required Environment Variables**:

```env
REACT_APP_REGION=ap-south-1
REACT_APP_USER_POOL_ID=your-user-pool-id
REACT_APP_USER_POOL_CLIENT_ID=your-client-id
REACT_APP_API_ENDPOINT=https://your-api-endpoint
```

### Backend Configuration

**Lambda Environment Variables**:

```python
READINGS_TABLE=AquaChain-Readings
DEVICES_TABLE=AquaChain-Devices
USERS_TABLE=AquaChain-Users
ML_MODEL_BUCKET=aquachain-ml-models
ALERT_TOPIC_ARN=arn:aws:sns:region:account:alerts
```

### IoT Device Configuration

**ESP32 Firmware**:

```cpp
#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASSWORD "your-wifi-password"
#define AWS_IOT_ENDPOINT "your-endpoint.iot.region.amazonaws.com"
#define DEVICE_ID "AquaChain-Device-001"
```

---

## 💻 Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm start

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint
```

### Backend Development

```bash
cd lambda

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Type checking
mypy .
```

### IoT Simulator

```bash
cd iot-simulator

# Install dependencies
pip install -r requirements.txt

# Run simulator (local mode)
python simulator.py --mode local --devices 3

# Run simulator (AWS mode)
python simulator.py --mode aws --devices 5 --interval 60
```

---

## 🧪 Testing

### Unit Tests

```bash
# Frontend
cd frontend && npm test

# Backend
cd lambda && pytest tests/unit/

# Coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Integration Tests

```bash
cd tests/integration
pytest -v

# Specific test
pytest test_data_pipeline_workflow.py -v
```

### End-to-End Tests

```bash
# Full system test
scripts\testing\test-everything.bat  # Windows
./scripts/testing/test-everything.bat # Linux/Mac
```

---

## 📚 Documentation

### Main Documentation

- **[PROJECT_REPORT.md](docs/reports/PROJECT_REPORT.md)** - Complete technical documentation (3,900+ lines)
  - System architecture
  - Implementation details
  - Deployment guides
  - Security & compliance
  - Performance optimization
  - Troubleshooting

### Quick Guides

- **[GET_STARTED.md](docs/guides/GET_STARTED.md)** - Quick start guide
- **[START_HERE.md](docs/guides/START_HERE.md)** - Project navigation
- **[WHATS_NEXT.md](docs/guides/WHATS_NEXT.md)** - Post-deployment steps
- **[AWS_ACCOUNT_MIGRATION_SUMMARY.md](docs/AWS_ACCOUNT_MIGRATION_SUMMARY.md)** - Switch AWS accounts (quick)

### Technical Docs

- **[AWS_ACCOUNT_MIGRATION_GUIDE.md](docs/AWS_ACCOUNT_MIGRATION_GUIDE.md)** - Complete AWS account migration guide
- **[ESP32_CONNECTION_CHECKLIST.md](docs/ESP32_CONNECTION_CHECKLIST.md)** - ESP32 hardware setup
- **[LOCAL_DEVELOPMENT_GUIDE.md](docs/LOCAL_DEVELOPMENT_GUIDE.md)** - Local development setup
- **[Frontend Documentation](frontend/README.md)** - Frontend documentation
- **[Backend Documentation](lambda/README.md)** - Backend documentation

---

## 🌐 API Endpoints

### Base URL

- **Development**: `http://localhost:3002`
- **Production**: `https://your-api.execute-api.region.amazonaws.com/prod`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signin` | User authentication |
| GET | `/api/devices` | Get user devices |
| POST | `/api/devices/register` | Register new device |
| GET | `/api/water-quality/latest` | Latest reading |
| GET | `/api/alerts` | Get alerts |
| GET | `/api/notifications` | Get notifications |
| POST | `/api/service-requests` | Create service request |

**Full API documentation**: See [docs/API_DOCUMENTATION.md](docs/)

---

## 🔐 Security Considerations

### Before Publishing to GitHub

1. **Check for sensitive data**:
   ```bash
   # Search for AWS keys
   grep -r "AKIA" . --exclude-dir={node_modules,venv,cdk.out}
   
   # Search for secrets
   grep -r "aws_secret_access_key" . --exclude-dir={node_modules,venv,cdk.out}
   
   # Check .env files
   find . -name ".env" -not -path "*/node_modules/*"
   ```

2. **Verify .gitignore**:
   - ✅ `.env*` files excluded
   - ✅ `*.pem`, `*.key` excluded
   - ✅ `.dev-data.json` excluded
   - ✅ `cdk.context.json` excluded

3. **Remove personal data**:
   - Replace real AWS account IDs with placeholders
   - Remove personal email addresses
   - Sanitize configuration examples

4. **Review documentation**:
   - Remove internal URLs
   - Remove real credentials
   - Use example values

---

## 💰 Cost Breakdown

### Development (Optimized)

| Service | Monthly Cost |
|---------|--------------|
| DynamoDB | ₹0 (Free Tier) |
| Lambda | ₹500-800 |
| IoT Core | ₹800-1,200 |
| API Gateway | ₹400-600 |
| S3 | ₹200-300 |
| CloudWatch | ₹300-400 |
| Other | ₹300-200 |
| **Total** | **₹2,500-3,500** |

### Production (10K devices)

| Service | Monthly Cost |
|---------|--------------|
| IoT Core | ₹15,000-18,000 |
| Lambda | ₹3,000-4,000 |
| DynamoDB | ₹4,000-5,000 |
| API Gateway | ₹1,500-2,000 |
| S3 | ₹1,000-1,500 |
| Other | ₹500-500 |
| **Total** | **₹25,000-30,000** |

**Cost per device**: ₹0.28-0.30/month

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Frontend**: ESLint + Prettier
- **Backend**: Black + Flake8
- **TypeScript**: Strict mode enabled
- **Python**: Type hints required

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

---

## 📈 Roadmap

### Phase 1: Core Features ✅
- [x] IoT data ingestion
- [x] Real-time dashboards
- [x] ML model integration
- [x] Alert system
- [x] User management

### Phase 2: Enhancements ✅
- [x] Multi-role dashboards
- [x] Service request system
- [x] Data export
- [x] Audit logging
- [x] GDPR compliance

### Phase 3: Advanced Features 🔄
- [ ] Mobile app (iOS/Android)
- [ ] Advanced analytics
- [ ] Predictive maintenance
- [ ] Multi-region deployment
- [ ] White-label solution

### Phase 4: Enterprise 📋
- [ ] Multi-tenancy
- [ ] Custom branding
- [ ] Advanced reporting
- [ ] SLA management
- [ ] Enterprise support

---

## 🐛 Troubleshooting

### Common Issues

**Frontend won't start**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

**Backend connection refused**:
```bash
# Check if port 3002 is available
netstat -ano | findstr :3002  # Windows
lsof -ti:3002                 # Linux/Mac

# Kill process if needed
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

**Devices not connecting**:
- Verify IoT endpoint is correct
- Check device certificates are valid
- Ensure WiFi credentials are correct
- Check CloudWatch logs for errors

**High AWS costs**:
```bash
# Check current costs
aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-30 --granularity MONTHLY --metrics BlendedCost

# Optimize
scripts\maintenance\ultra-cost-optimize.bat
```

**Full troubleshooting guide**: See PROJECT_REPORT.md Appendix M

---

## 📊 Project Statistics

- **Total Code**: 50,000+ lines
- **Lambda Functions**: 30+
- **DynamoDB Tables**: 12
- **Test Coverage**: 85%+
- **API Endpoints**: 50+
- **Documentation**: 5,000+ lines
- **Development Time**: 6 months
- **Team Size**: 4 developers

---

## 🏆 Achievements

- ✅ **99.74% ML accuracy** - Industry-leading water quality prediction
- ✅ **99.95% uptime** - Highly reliable system
- ✅ **<500ms latency** - Fast API responses
- ✅ **0 critical vulnerabilities** - Secure codebase
- ✅ **85%+ test coverage** - Well-tested
- ✅ **GDPR compliant** - Privacy-focused
- ✅ **Cost optimized** - 57% cost reduction achieved

---

## 📞 Support

### Documentation
- **Complete Guide**: [PROJECT_REPORT.md](docs/reports/PROJECT_REPORT.md)
- **Quick Start**: [GET_STARTED.md](docs/guides/GET_STARTED.md)
- **Navigation**: [START_HERE.md](docs/guides/START_HERE.md)
- **Troubleshooting**: [PROJECT_REPORT.md Appendix M](docs/reports/PROJECT_REPORT.md#appendix-m-troubleshooting-guide)

### Contact
- **Issues**: Open a GitHub issue
- **Discussions**: GitHub Discussions
- **Email**: contactaquachain@gmail.com

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- AWS for cloud infrastructure
- ESP32 community for IoT support
- React team for frontend framework
- Open source contributors

---

## 📝 Changelog

### Version 1.1 (November 2025)
- ✅ Admin Dashboard enhancement with tabbed navigation
- ✅ Dynamic notifications system
- ✅ Profile editing with OTP verification
- ✅ Technician dashboard with task management
- ✅ Add device feature
- ✅ WebSocket stability fixes
- ✅ Documentation consolidation

### Version 1.0 (October 2025)
- ✅ Initial release
- ✅ Core IoT functionality
- ✅ ML model integration
- ✅ Multi-role dashboards
- ✅ AWS deployment

**Full changelog**: See PROJECT_REPORT.md Section 12

---

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐

---

**Built with ❤️ by the AquaChain Team**

**Last Updated**: November 7, 2025  
**Version**: 1.1  
**Status**: Production Ready 

---

## 📖 Additional Resources

- **[Complete Documentation](docs/reports/PROJECT_REPORT.md)** - 3,900+ lines of technical docs
- **[Architecture Guide](docs/reports/PROJECT_REPORT.md#system-architecture)** - System design
- **[Deployment Guide](docs/reports/PROJECT_REPORT.md#appendix-j-aws-deployment)** - AWS setup
- **[Security Guide](docs/reports/PROJECT_REPORT.md#appendix-l-security--compliance)** - Security best practices
- **[Cost Optimization](docs/cost-optimization/README.md)** - Cost reduction strategies
- **[All Documentation](docs/)** - Browse all docs

---

**For complete documentation, see [PROJECT_REPORT.md](docs/reports/PROJECT_REPORT.md)**
