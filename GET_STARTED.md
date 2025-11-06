# Get Started with AquaChain

**Quick start guide for AquaChain water quality monitoring system.**

---

## 🎯 Choose Your Path

### 1. Local Development (Fastest - 5 minutes)

**Best for:** Testing without AWS costs

```bash
# Windows
setup-local.bat
start-local.bat

# Linux/Mac
./setup-local.sh
./start-local.sh

# Access at http://localhost:3000
# Login: demo@aquachain.com / demo123
```

**Cost:** ₹0/month

---

### 2. AWS Deployment (30 minutes)

**Best for:** Production deployment

```bash
# Prerequisites
# - AWS account with admin access
# - AWS CLI configured
# - CDK installed

# Bootstrap (first time only)
cd infrastructure/cdk
cdk bootstrap aws://ACCOUNT-ID/ap-south-1

# Deploy
cdk deploy --all

# Cost: ₹2,500-3,500/month (optimized)
```

---

### 3. IoT Simulator (10 minutes)

**Best for:** Testing without hardware

```bash
cd iot-simulator
python simulator.py --mode aws --devices 5
```

---

## 📚 Complete Documentation

**All detailed guides are in PROJECT_REPORT.md:**

- **Appendix I:** Local Development Setup (Lines 2951-3050)
- **Appendix J:** AWS Deployment Guide (Lines 3051-3200)
- **Appendix K:** IoT Device Setup (Lines 3201-3350)
- **Appendix L:** Security & Compliance (Lines 3351-3500)
- **Appendix M:** Troubleshooting (Lines 3501-3650)

---

## 🚀 Next Steps

After setup:

1. **Login** to dashboard at http://localhost:3000
2. **View devices** in the dashboard
3. **Check data** flowing in real-time
4. **Create alerts** for water quality issues
5. **Export data** for analysis

---

## 📖 More Information

- **[PROJECT_REPORT.md](PROJECT_REPORT.md)** - Complete documentation
- **[START_HERE.md](START_HERE.md)** - Project navigation
- **[WHATS_NEXT.md](WHATS_NEXT.md)** - Post-deployment steps
- **[README.md](README.md)** - Project overview

---

**Last Updated:** November 5, 2025  
**Status:** Ready to use
