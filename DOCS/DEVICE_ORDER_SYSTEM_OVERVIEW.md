# Device Order & Onboarding System - Overview

## 🎯 Goal
Add a production-ready "Request Device → Order → Ship → Technician Install → Device Linked to User" workflow to AquaChain so real users can acquire hardware and have it appear in their Consumer Dashboard.

## 📋 System Flow

```
Consumer Request → Admin Quote → Payment → Device Provision → 
Technician Assignment → Shipping → Installation → Device Active
```

## 🗂️ Data Model

### Orders Table
- Order lifecycle management
- Payment tracking
- Shipping information
- Technician assignment

### Devices Table (Extended)
- Device inventory
- Provisioning status
- Installation tracking
- Owner assignment

### Ledger Table
- Audit trail
- State transitions
- Compliance records

## 🔐 Security Model
- Role-based access (Consumer, Admin, Technician)
- JWT authentication
- Payment webhook validation
- Audit logging

## 📱 User Interfaces

### Consumer
- Request device form
- Order tracking
- Payment options
- Installation scheduling

### Admin
- Order queue management
- Device provisioning
- Technician assignment
- Shipping management

### Technician
- Installation assignments
- Device activation
- Photo upload
- Calibration tools

## 🚀 Implementation Phases

### Phase 1: MVP (Dev Environment) - Week 1
- Basic order creation
- Admin order management
- Manual device assignment
- Simple status tracking

### Phase 2: Payment Integration - Week 2
- Razorpay integration
- COD support
- Payment webhooks
- Order confirmation

### Phase 3: Technician Flow - Week 3
- Assignment system
- Installation workflow
- Device activation
- Photo upload

### Phase 4: Production Ready - Week 4
- AWS infrastructure
- DynamoDB tables
- Lambda functions
- API Gateway setup

See detailed specs in:
- DEVICE_ORDER_API_SPEC.md
- DEVICE_ORDER_UI_SPEC.md
- DEVICE_ORDER_AWS_SPEC.md
