# How to Find Documentation

Quick reference guide for locating documentation in the consolidated DOCS directory.

## 🔍 Quick Search Patterns

### By Feature

| Feature | Location |
|---------|----------|
| Shipment Tracking | `DOCS/lambda/shipments/` |
| Order Management | `DOCS/lambda/orders/` |
| Admin Dashboard | `DOCS/frontend/src/components/Admin/` |
| Consumer Dashboard | `DOCS/frontend/src/components/Dashboard/` |
| Technician Dashboard | `DOCS/frontend/src/components/Dashboard/` |
| IoT Device Management | `DOCS/lambda/iot_management/` |
| ML Inference | `DOCS/lambda/ml_inference/` |
| API Gateway | `DOCS/infrastructure/api_gateway/` |
| Database Schema | `DOCS/infrastructure/dynamodb/` |
| Monitoring & Alerts | `DOCS/infrastructure/monitoring/` |

### By Document Type

| Type | Pattern | Example |
|------|---------|---------|
| Task Completion | `TASK_*_COMPLETION_SUMMARY.md` | `TASK_19_COMPLETION_SUMMARY.md` |
| Quick Start Guides | `*_QUICK_START.md` | `NOTIFICATION_QUICK_START.md` |
| Implementation Summaries | `*_IMPLEMENTATION*.md` | `MONITORING_IMPLEMENTATION_COMPLETE.md` |
| Architecture Docs | `*_ARCHITECTURE.md` | `SHIPMENT_TRACKING_ARCHITECTURE.md` |
| Setup Guides | `*_SETUP.md` or `*_GUIDE.md` | `STALE_SHIPMENT_SETUP.md` |
| README Files | `README.md` | Various locations |

### By Task Number

All task completion summaries are now in `DOCS/`:
- Task 1: `DOCS/infrastructure/dynamodb/TASK_1_COMPLETION_SUMMARY.md`
- Task 2: `DOCS/lambda/shipments/TASK_2_COMPLETION_SUMMARY.md`
- Task 3: `DOCS/lambda/shipments/TASK_3_COMPLETION_SUMMARY.md`
- ...
- Task 19: `DOCS/TASK_19_COMPLETION_SUMMARY.md`

## 📂 Common Documentation Paths

### Lambda Functions
```
DOCS/lambda/
├── shipments/              # Shipment tracking system
│   ├── TASK_*_COMPLETION_SUMMARY.md
│   ├── NOTIFICATION_SYSTEM_README.md
│   ├── AUDIT_TRAIL_QUICK_REFERENCE.md
│   └── DATA_RETENTION_POLICY.md
├── orders/                 # Order management
│   ├── BACKWARD_COMPATIBILITY_GUIDE.md
│   └── PROPERTY_TEST_QUICK_REFERENCE.md
├── iot_management/         # IoT devices
├── ml_inference/           # ML inference
└── shared/                 # Shared utilities
```

### Infrastructure
```
DOCS/infrastructure/
├── api_gateway/            # API configuration
│   ├── API_ENDPOINTS_DIAGRAM.md
│   └── SHIPMENT_ENDPOINTS_README.md
├── dynamodb/               # Database
│   ├── QUICK_START.md
│   └── SHIPMENT_FIELDS_GUIDE.md
├── monitoring/             # CloudWatch
│   ├── MONITORING_QUICK_START.md
│   └── SHIPMENT_MONITORING_README.md
└── cdk/                    # Infrastructure as Code
```

### Frontend
```
DOCS/frontend/src/components/
├── Admin/                  # Admin UI
│   ├── SHIPMENT_TRACKING_QUICK_START.md
│   └── SHIPMENT_TRACKING_UI_SUMMARY.md
└── Dashboard/              # Dashboards
    ├── CONSUMER_TRACKING_QUICK_START.md
    ├── TECHNICIAN_DELIVERY_TRACKING_GUIDE.md
    └── SHIPMENT_TRACKING_ARCHITECTURE.md
```

## 🎯 Finding Specific Information

### "How do I...?"

| Question | Document |
|----------|----------|
| Set up shipment tracking? | `DOCS/lambda/shipments/NOTIFICATION_SYSTEM_README.md` |
| Configure monitoring? | `DOCS/infrastructure/monitoring/MONITORING_QUICK_START.md` |
| Understand the database schema? | `DOCS/infrastructure/dynamodb/SHIPMENT_FIELDS_GUIDE.md` |
| Deploy the application? | `DOCS/infrastructure/DEPLOYMENT_GUIDE.md` |
| Optimize costs? | `DOCS/cost-optimization/README.md` |
| Set up local development? | `DOCS/LOCAL_DEVELOPMENT_GUIDE.md` |
| Implement backward compatibility? | `DOCS/lambda/orders/BACKWARD_COMPATIBILITY_GUIDE.md` |
| Write property-based tests? | `DOCS/lambda/orders/PROPERTY_TEST_QUICK_REFERENCE.md` |

### "What is...?"

| Topic | Document |
|-------|----------|
| Shipment tracking architecture | `DOCS/SHIPMENT_TRACKING_DESIGN.md` |
| Device order workflow | `DOCS/COMPLETE_DEVICE_ORDER_WORKFLOW.md` |
| Audit trail system | `DOCS/lambda/shipments/AUDIT_TRAIL_QUICK_REFERENCE.md` |
| Notification system | `DOCS/lambda/shipments/NOTIFICATION_SYSTEM_ARCHITECTURE.md` |
| Data retention policy | `DOCS/lambda/shipments/DATA_RETENTION_POLICY.md` |

### "Where is the documentation for...?"

| Component | Path |
|-----------|------|
| Create Shipment Lambda | `DOCS/lambda/shipments/TASK_2_COMPLETION_SUMMARY.md` |
| Webhook Handler | `DOCS/lambda/shipments/TASK_3_COMPLETION_SUMMARY.md` |
| Stale Shipment Detector | `DOCS/lambda/shipments/TASK_8_COMPLETION_SUMMARY.md` |
| API Endpoints | `DOCS/infrastructure/api_gateway/` |
| DynamoDB Tables | `DOCS/infrastructure/dynamodb/` |
| CloudWatch Monitoring | `DOCS/infrastructure/monitoring/` |

## 🔧 Search Commands

### PowerShell
```powershell
# Find all documentation about shipments
Get-ChildItem -Path DOCS -Filter *shipment*.md -Recurse

# Find all task completion summaries
Get-ChildItem -Path DOCS -Filter TASK_*_COMPLETION*.md -Recurse

# Find all quick start guides
Get-ChildItem -Path DOCS -Filter *QUICK_START*.md -Recurse

# Search for specific text in all docs
Get-ChildItem -Path DOCS -Filter *.md -Recurse | Select-String -Pattern "your search term"
```

### Command Line (Linux/Mac)
```bash
# Find all documentation about shipments
find DOCS -name "*shipment*.md"

# Find all task completion summaries
find DOCS -name "TASK_*_COMPLETION*.md"

# Find all quick start guides
find DOCS -name "*QUICK_START*.md"

# Search for specific text in all docs
grep -r "your search term" DOCS/*.md
```

## 📚 Documentation Categories

### Getting Started
- `DOCS/guides/START_HERE.md`
- `DOCS/SETUP_GUIDE.md`
- `DOCS/LOCAL_DEVELOPMENT_GUIDE.md`

### Feature Documentation
- `DOCS/lambda/shipments/` - Shipment tracking
- `DOCS/lambda/orders/` - Order management
- `DOCS/frontend/src/components/` - UI components

### API & Integration
- `DOCS/infrastructure/api_gateway/` - API endpoints
- `DOCS/lambda/shipments/NOTIFICATION_SYSTEM_README.md` - Webhooks

### Operations & Deployment
- `DOCS/infrastructure/DEPLOYMENT_GUIDE.md`
- `DOCS/infrastructure/monitoring/`
- `DOCS/cost-optimization/`

### Testing
- `DOCS/tests/` - Test documentation
- `DOCS/lambda/orders/PROPERTY_TEST_QUICK_REFERENCE.md`

## 💡 Tips

1. **Use the Index**: Start with `DOCS/DOCUMENTATION_INDEX.md` for an overview
2. **Search by Keyword**: Use your IDE's search feature to find specific topics
3. **Follow the Structure**: Documentation mirrors the code structure
4. **Check Task Summaries**: Task completion docs provide comprehensive feature overviews
5. **Look for Quick Starts**: Quick start guides provide fastest path to understanding

## 🆘 Still Can't Find It?

1. Check `DOCS/DOCUMENTATION_INDEX.md` - Master index of all documentation
2. Search the entire DOCS directory for keywords
3. Look in the original code directory path under DOCS/
4. Check if it's a README.md in the main project directories

---

**Need Help?** Open an issue or check the main project README.md
