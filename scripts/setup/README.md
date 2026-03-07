# Setup Scripts

Environment setup and configuration scripts for AquaChain development.

## Quick Start

### New Developer Setup

```bash
# One-command setup (recommended)
scripts\setup\quick-start.bat    # Windows
./scripts/setup/quick-start.sh   # Linux/Mac
```

This will:
1. Check prerequisites (Python, Node.js, AWS CLI)
2. Install dependencies
3. Configure AWS credentials
4. Set up local environment
5. Create `.env` files
6. Initialize database (if needed)

### Start Development

```bash
# Start local development servers
scripts\setup\start-local.bat    # Windows
./scripts/setup/start-local.sh   # Linux/Mac
```

This will:
1. Start frontend dev server (React)
2. Start local DynamoDB (if configured)
3. Open browser to http://localhost:3000

## Scripts Reference

### quick-start.bat / quick-start.sh

Complete setup for new developers.

**Usage:**
```bash
# Windows
scripts\setup\quick-start.bat

# Linux/Mac
./scripts/setup/quick-start.sh
```

**What it does:**
- Validates prerequisites
- Installs Python dependencies
- Installs Node.js dependencies
- Configures AWS CLI
- Creates environment files
- Sets up local database
- Runs initial tests

**Duration:** 5-10 minutes

### setup-local.bat / setup-local.sh

Configure local development environment.

**Usage:**
```bash
# Windows
scripts\setup\setup-local.bat

# Linux/Mac
./scripts/setup/setup-local.sh
```

**What it does:**
- Creates `.env.local` files
- Configures local DynamoDB
- Sets up test data
- Configures frontend proxy

### start-local.bat / start-local.sh

Start local development servers.

**Usage:**
```bash
# Windows
scripts\setup\start-local.bat

# Linux/Mac
./scripts/setup/start-local.sh
```

**What it does:**
- Starts React dev server (port 3000)
- Starts local DynamoDB (port 8000)
- Opens browser automatically

**Stop servers:**
- Press `Ctrl+C` in terminal

### create-admin-user.ps1

Create admin user in AWS Cognito.

**Usage:**
```bash
.\scripts\setup\create-admin-user.ps1 -Email admin@example.com -Password SecurePass123!
```

**Options:**
```bash
-Email      # Admin email address (required)
-Password   # Admin password (required)
-UserPoolId # Cognito User Pool ID (optional, auto-detected)
```

**What it does:**
- Creates user in Cognito
- Assigns admin role
- Confirms email automatically
- Outputs user credentials

## Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   python --version
   # Should show: Python 3.11.x or higher
   ```

2. **Node.js 18+**
   ```bash
   node --version
   # Should show: v18.x.x or higher
   ```

3. **AWS CLI**
   ```bash
   aws --version
   # Should show: aws-cli/2.x.x or higher
   ```

4. **Git**
   ```bash
   git --version
   # Should show: git version 2.x.x or higher
   ```

### AWS Configuration

Configure AWS credentials:
```bash
aws configure
```

Enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `ap-south-1`
- Default output format: `json`

Verify configuration:
```bash
aws sts get-caller-identity
```

### Environment Variables

Create `.env.local` in `frontend/`:
```bash
REACT_APP_API_ENDPOINT=http://localhost:3000/api
REACT_APP_USER_POOL_ID=ap-south-1_XXXXXXX
REACT_APP_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
REACT_APP_REGION=ap-south-1
```

## Local Development Setup

### Frontend Only

```bash
cd frontend
npm install
npm start
```

Access at: http://localhost:3000

### Backend (Lambda) Testing

```bash
cd lambda
pip install -r requirements.txt
pytest
```

### Full Stack Local

```bash
# Terminal 1: Start backend
cd lambda
python -m flask run

# Terminal 2: Start frontend
cd frontend
npm start
```

## Troubleshooting

### Python Version Issues

**Issue: Python 3.11 not found**
```bash
# Windows: Download from python.org
# Linux: sudo apt install python3.11
# Mac: brew install python@3.11
```

### Node.js Version Issues

**Issue: Node.js 18 not found**
```bash
# Windows: Download from nodejs.org
# Linux: Use nvm (Node Version Manager)
# Mac: brew install node@18
```

### AWS CLI Not Configured

**Issue: AWS credentials not found**
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=ap-south-1
```

### Port Already in Use

**Issue: Port 3000 already in use**
```bash
# Windows: Find and kill process
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac: Find and kill process
lsof -ti:3000 | xargs kill -9
```

### Dependencies Installation Failed

**Issue: npm install fails**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue: pip install fails**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

## Development Workflow

### Daily Workflow

1. **Pull latest changes**
   ```bash
   git pull origin develop
   ```

2. **Start development servers**
   ```bash
   scripts\setup\start-local.bat
   ```

3. **Make changes**
   - Edit code
   - Test locally
   - Run tests

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/my-feature
   ```

### Testing Changes

```bash
# Run frontend tests
cd frontend
npm test

# Run backend tests
cd lambda
pytest

# Run comprehensive tests
scripts\testing\run-comprehensive-test.bat dev
```

### Deploying Changes

```bash
# Deploy to dev environment
scripts\deployment\deploy-all.bat

# Verify deployment
python scripts/testing/production_readiness_validation.py --environment dev
```

## Best Practices

1. **Always pull before starting work** - Avoid merge conflicts
2. **Test locally before committing** - Catch issues early
3. **Use feature branches** - Keep main/develop clean
4. **Run tests before pushing** - Ensure code quality
5. **Keep dependencies updated** - Security and performance
6. **Document environment changes** - Update .env.example

## Additional Resources

- [Main README](../../README.md)
- [Deployment Guide](../deployment/README.md)
- [Testing Guide](../testing/COMPREHENSIVE_TEST_README.md)
- [AquaChain Documentation](../../DOCS/)

## Support

For setup issues:
- Check troubleshooting section above
- Review error messages carefully
- Consult team documentation
- Ask in #dev-help Slack channel
