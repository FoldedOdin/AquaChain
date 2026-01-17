# Documentation Index

This directory contains all project documentation organized by category.

## 📁 Directory Structure

### Root Documentation
- Task completion summaries (TASK_*.md files)
- Main project documentation

### Lambda Functions (`lambda/`)
Documentation for all Lambda function implementations:
- **shipments/** - Shipment tracking system documentation
- **orders/** - Order management documentation  
- **iot_management/** - IoT device management
- **ml_inference/** - Machine learning inference
- **ml_training/** - ML model training
- **shared/** - Shared utilities documentation
- **compliance_service/** - GDPR compliance
- **contact_service/** - Contact form handling
- **technician_service/** - Technician management

### Infrastructure (`infrastructure/`)
Infrastructure and deployment documentation:
- **api_gateway/** - API Gateway configuration
- **dynamodb/** - Database schema and setup
- **monitoring/** - CloudWatch monitoring and alarms
- **cdk/** - CDK infrastructure as code
- **security/** - Security configurations

### Frontend (`frontend/`)
Frontend application documentation:
- **src/components/Admin/** - Admin UI documentation
- **src/components/Dashboard/** - Dashboard documentation
- **src/components/LandingPage/** - Landing page docs
- **src/services/** - Service layer documentation
- **src/config/** - Configuration documentation

### Tests (`tests/`)
Testing documentation and guides:
- **integration/** - Integration test documentation
- **unit/infrastructure/** - Infrastructure unit tests

### Scripts (`scripts/`)
Automation and utility scripts documentation:
- **deployment/** - Deployment scripts
- **maintenance/** - Maintenance utilities
- **security/** - Security tools
- **setup/** - Setup scripts
- **testing/** - Testing utilities

### IoT Simulator (`iot-simulator/`)
IoT device simulation documentation:
- **esp32-firmware/** - ESP32 firmware documentation
- **simulation/** - Simulation tools

### Project Reports (`project_report/`)
Project status and quality reports

## 🔍 Quick Links

### Getting Started
- [Main README](../README.md)
- [Setup Guide](SETUP_GUIDE.md)
- [Quick Start](guides/START_HERE.md)

### Feature Documentation

#### Shipment Tracking
- [Shipment Tracking Design](SHIPMENT_TRACKING_DESIGN.md)
- [Shipment Tracking Spec Summary](SHIPMENT_TRACKING_SPEC_SUMMARY.md)
- [Task 19 Completion](TASK_19_COMPLETION_SUMMARY.md)

#### Order Management
- [Device Order System Overview](DEVICE_ORDER_SYSTEM_OVERVIEW.md)
- [Complete Device Order Workflow](COMPLETE_DEVICE_ORDER_WORKFLOW.md)

#### Dashboard Features
- [Consumer Dashboard](CONSUMER_DASHBOARD_COMPLETE.md)
- [Technician Workflow](TECHNICIAN_WORKFLOW_IMPLEMENTATION.md)

### Deployment & Operations
- [Deployment Guide](infrastructure/DEPLOYMENT_GUIDE.md)
- [AWS Account Migration](AWS_ACCOUNT_MIGRATION_GUIDE.md)
- [Cost Optimization](cost-optimization/README.md)

### Development
- [Local Development Guide](LOCAL_DEVELOPMENT_GUIDE.md)
- [Error Handling](lambda/ERROR_HANDLING_IMPLEMENTATION.md)
- [Performance Optimization](lambda/LAMBDA_PERFORMANCE_OPTIMIZATION.md)

## 📊 Documentation by Category

### Architecture & Design
- System architecture documents
- Component design specifications
- Data flow diagrams

### Implementation Guides
- Feature implementation summaries
- Task completion reports
- Quick start guides

### API Documentation
- API endpoint specifications
- Integration guides
- Webhook documentation

### Testing
- Test guides and strategies
- Property-based testing documentation
- Integration test specifications

### Operations
- Deployment procedures
- Monitoring and alerting
- Maintenance guides

### Security
- Security implementation guides
- Credential management
- Compliance documentation

## 🔄 Recent Updates

All markdown documentation files have been consolidated into this DOCS directory while preserving their original directory structure for easy navigation and reference.

## 📝 Contributing

When adding new documentation:
1. Place files in the appropriate subdirectory matching the source code structure
2. Update this index if adding a new major section
3. Use clear, descriptive filenames
4. Include links to related documentation

---

**Last Updated**: January 2, 2026
**Total Documentation Files**: 135+
