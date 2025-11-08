# ✅ AquaChain Setup Checklist

Use this checklist to track your setup progress.

---

## Prerequisites

- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] AWS CLI installed
- [ ] AWS account with admin access
- [ ] Git installed (optional)

**Verify:** Run `quick-start.sh` or `quick-start.bat` to check automatically

---

## Initial Setup

- [ ] Clone/download project
- [ ] Read GET_STARTED.md
- [ ] Choose your setup path (frontend only, full stack, or infrastructure only)

---

## Frontend Setup

- [ ] Navigate to `frontend/` directory
- [ ] Run `npm install`
- [ ] Copy `.env.example` to `.env.development`
- [ ] Configure AWS settings in `.env.development`
- [ ] Run `npm start` to test
- [ ] Verify app opens at http://localhost:3000

---

## Infrastructure Setup

- [ ] Configure AWS credentials (`aws configure`)
- [ ] Verify credentials (`aws sts get-caller-identity`)
- [ ] Navigate to `infrastructure/cdk/`
- [ ] Install CDK dependencies (`pip install -r requirements.txt`)
- [ ] Bootstrap CDK (`cdk bootstrap`) - first time only
- [ ] Review stack list (`cdk list`)
- [ ] Deploy infrastructure (`cdk deploy --all` or `./deploy-all.sh`)
- [ ] Verify deployment (`python infrastructure/check-deployment.py`)

---

## AWS Configuration

- [ ] Get Cognito User Pool ID
- [ ] Get Cognito Client ID
- [ ] Get API Gateway URL
- [ ] Get WebSocket API URL
- [ ] Get IoT Core endpoint
- [ ] Update frontend `.env.development` with these values

---

## Testing

- [ ] Create test user in Cognito
- [ ] Test frontend login
- [ ] Test API endpoints
- [ ] Run frontend tests (`npm test`)
- [ ] Run backend tests (`pytest`)
- [ ] Verify real-time updates work

---

## IoT Setup (Optional)

- [ ] Navigate to `iot-simulator/`
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Provision test device
- [ ] Run simulator
- [ ] Verify data appears in dashboard

---

## Documentation Review

- [ ] Read PROJECT_REPORT.md (comprehensive technical docs)
- [ ] Read SETUP_GUIDE.md (detailed setup instructions)
- [ ] Read README_START_HERE.md (project navigation)
- [ ] Browse /DOCS directory (additional guides)

---

## Production Deployment (When Ready)

- [ ] Review security checklist
- [ ] Run all tests
- [ ] Update environment to production
- [ ] Deploy infrastructure to production
- [ ] Deploy frontend to production
- [ ] Configure monitoring and alerts
- [ ] Set up backup strategy
- [ ] Document rollback procedures
- [ ] Run smoke tests
- [ ] Monitor for 24 hours

---

## Troubleshooting

If you encounter issues:

- [ ] Check SETUP_GUIDE.md troubleshooting section
- [ ] Verify AWS credentials are correct
- [ ] Check CloudWatch logs for errors
- [ ] Verify all environment variables are set
- [ ] Ensure all dependencies are installed
- [ ] Check AWS service limits and quotas

---

## Quick Reference

### Start Frontend:
```bash
cd frontend
npm start
```

### Deploy Infrastructure:
```bash
./deploy-all.sh
```

### Run Tests:
```bash
npm test
pytest
```

### View Logs:
```bash
aws logs tail /aws/lambda/AquaChain-DataProcessing --follow
```

### Check Deployment:
```bash
python infrastructure/check-deployment.py
```

---

## Success Criteria

You've successfully set up AquaChain when:

- ✅ Frontend runs at http://localhost:3000
- ✅ You can log in with test credentials
- ✅ Dashboard displays (even with mock data)
- ✅ All tests pass
- ✅ Infrastructure is deployed (if doing full setup)
- ✅ API endpoints respond correctly
- ✅ Real-time updates work (if infrastructure deployed)

---

## Next Steps After Setup

- [ ] Explore the dashboard features
- [ ] Review PROJECT_REPORT.md for architecture details
- [ ] Customize configuration for your needs
- [ ] Add real IoT devices (if applicable)
- [ ] Set up monitoring and alerts
- [ ] Plan production deployment
- [ ] Train team members

---

**Setup Time Estimate:**
- Frontend only: 5-10 minutes
- Full stack: 30-45 minutes
- Production deployment: 1-2 hours

**Need help?** Check GET_STARTED.md or SETUP_GUIDE.md

---

**Last Updated:** October 27, 2025
