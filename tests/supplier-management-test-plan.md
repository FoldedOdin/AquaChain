# Supplier Management API Test Plan

## Overview
Test plan for the enhanced supplier management service with dashboard overhaul features including audit logging, performance scoring, financial risk assessment, and contract management.

## Test Environment Setup

### Prerequisites
1. **API Server**: Ensure supplier management Lambda is deployed and accessible
2. **Authentication**: Valid JWT token with appropriate permissions
3. **Test Data**: Sample suppliers, contracts, and financial data
4. **Postman Environment**: Configure base_url and auth_token variables

### Environment Variables
```json
{
  "base_url": "https://api.aquachain.com/api",
  "auth_token": "{{JWT_TOKEN}}",
  "supplier_id": "SUPPLIER-001",
  "contract_id": "CONTRACT-001"
}
```

## Test Scenarios

### 1. Supplier Profile Management

#### 1.1 Get Suppliers List
- **Endpoint**: `GET /api/suppliers`
- **Query Parameters**: `status=active&category=electronics`
- **Expected**: 200 OK with filtered supplier list
- **Validation**: 
  - Response contains suppliers array
  - Audit logging captures read operation
  - Filtering works correctly

#### 1.2 Create New Supplier
- **Endpoint**: `POST /api/suppliers`
- **Payload**:
```json
{
  "supplier_name": "TechSensors Inc",
  "contact_email": "orders@techsensors.com",
  "contact_phone": "+1-555-0123",
  "address": "123 Tech Street, Silicon Valley, CA",
  "category": "electronics",
  "payment_terms": "NET30",
  "api_endpoint": "https://api.techsensors.com/orders"
}
```
- **Expected**: 201 Created with supplier_id
- **Validation**:
  - Supplier created in database
  - Audit trail logged
  - Input validation works

#### 1.3 Update Supplier Profile
- **Endpoint**: `PUT /api/suppliers/{supplier_id}`
- **Payload**:
```json
{
  "contact_email": "neworders@techsensors.com",
  "contact_phone": "+1-555-0124",
  "payment_terms": "NET15",
  "notes": "Updated contact information per supplier request"
}
```
- **Expected**: 200 OK with updated supplier
- **Validation**:
  - Changes persisted correctly
  - Audit trail captures modifications
  - Version control maintained

### 2. Performance Metrics

#### 2.1 Get Supplier Performance
- **Endpoint**: `GET /api/suppliers/{supplier_id}/performance`
- **Query Parameters**: `period=12months`
- **Expected**: 200 OK with comprehensive metrics
- **Validation**:
  - Performance calculations accurate
  - Includes on-time delivery, quality scores
  - Historical trend data present

### 3. Financial Risk Assessment

#### 3.1 Update Financial Data
- **Endpoint**: `PUT /api/suppliers/{supplier_id}/financial-data`
- **Payload**:
```json
{
  "credit_rating": "A",
  "debt_to_equity_ratio": 0.6,
  "cash_flow_trend": 5,
  "market_reputation_score": 85,
  "industry_rating": "Excellent"
}
```
- **Expected**: 200 OK with updated data
- **Validation**:
  - Financial data stored securely
  - Risk score recalculated
  - Audit trail maintained

#### 3.2 Calculate Risk Assessment
- **Endpoint**: `POST /api/suppliers/{supplier_id}/risk-assessment`
- **Payload**:
```json
{
  "financial_data": {
    "credit_rating": "B",
    "debt_to_equity_ratio": 0.8,
    "cash_flow_trend": -2
  }
}
```
- **Expected**: 200 OK with risk assessment
- **Validation**:
  - Risk level calculated correctly
  - Score within expected range (0-100)
  - Recommendations generated

### 4. Contract Management

#### 4.1 Create Contract
- **Endpoint**: `POST /api/contracts`
- **Payload**:
```json
{
  "supplier_id": "SUPPLIER-001",
  "contract_type": "SUPPLY_AGREEMENT",
  "contract_value": 50000.00,
  "start_date": "2026-02-01",
  "end_date": "2027-01-31",
  "terms": {
    "payment_terms": "NET30",
    "delivery_terms": "FOB Destination",
    "quality_requirements": "ISO 9001 certified"
  }
}
```
- **Expected**: 201 Created with contract_id
- **Validation**:
  - Contract stored with proper structure
  - Supplier relationship established
  - Audit trail created

#### 4.2 Get Supplier Contracts
- **Endpoint**: `GET /api/suppliers/{supplier_id}/contracts`
- **Expected**: 200 OK with contracts list
- **Validation**:
  - All supplier contracts returned
  - Contract status accurate
  - Expiration dates calculated

#### 4.3 Update Contract Status
- **Endpoint**: `PUT /api/contracts/{contract_id}/status`
- **Payload**:
```json
{
  "status": "active",
  "notes": "Contract activated after legal review"
}
```
- **Expected**: 200 OK with updated contract
- **Validation**:
  - Status change persisted
  - Audit trail updated
  - Notifications sent if required

### 5. Legacy Purchase Orders (Backward Compatibility)

#### 5.1 Get Purchase Orders
- **Endpoint**: `GET /api/purchase-orders`
- **Query Parameters**: `supplier_id=SUPPLIER-001&status=pending`
- **Expected**: 200 OK with filtered orders
- **Validation**: Legacy functionality maintained

#### 5.2 Create Purchase Order
- **Endpoint**: `POST /api/purchase-orders`
- **Expected**: 201 Created or approval workflow triggered
- **Validation**: Approval thresholds work correctly

### 6. Security & Audit Testing

#### 6.1 Authentication Validation
- **Test**: Request without valid JWT token
- **Expected**: 401 Unauthorized
- **Validation**: Proper error handling

#### 6.2 Authorization Testing
- **Test**: User without supplier management permissions
- **Expected**: 403 Forbidden
- **Validation**: RBAC enforcement

#### 6.3 Audit Trail Verification
- **Test**: Perform various operations and check audit logs
- **Expected**: All actions logged with proper context
- **Validation**: 
  - User ID captured
  - IP address logged
  - Action details complete

### 7. Error Handling

#### 7.1 Invalid Supplier ID
- **Test**: Request with non-existent supplier_id
- **Expected**: 404 Not Found with proper error message

#### 7.2 Invalid Input Data
- **Test**: Send malformed JSON or missing required fields
- **Expected**: 400 Bad Request with validation errors

#### 7.3 Database Errors
- **Test**: Simulate database connectivity issues
- **Expected**: 500 Internal Server Error with generic message

## Performance Testing

### Load Testing Scenarios
1. **Concurrent Supplier Queries**: 100 concurrent GET requests
2. **Bulk Performance Calculations**: Multiple performance metric requests
3. **Risk Assessment Load**: Simultaneous risk calculations

### Performance Targets
- **Response Time**: < 500ms for GET requests
- **Throughput**: > 1000 requests/minute
- **Error Rate**: < 0.1%

## Security Testing

### Input Validation
- SQL injection attempts
- XSS payload testing
- JSON structure attacks
- Oversized payloads

### Authentication & Authorization
- Token expiration handling
- Role-based access control
- Cross-tenant data access prevention

## Compliance Testing

### GDPR Compliance
- Data export functionality
- Audit trail completeness
- Personal data handling

### Financial Audit Requirements
- Transaction logging
- Approval workflow tracking
- Data integrity verification

## Test Data Requirements

### Sample Suppliers
```json
[
  {
    "supplier_id": "SUPPLIER-001",
    "supplier_name": "TechSensors Inc",
    "status": "active",
    "category": "electronics"
  },
  {
    "supplier_id": "SUPPLIER-002", 
    "supplier_name": "Industrial Components Ltd",
    "status": "active",
    "category": "hardware"
  }
]
```

### Sample Performance Data
- Historical purchase orders (last 12 months)
- Delivery records with timestamps
- Quality metrics and issues
- Communication response times

### Sample Financial Data
- Credit ratings
- Financial ratios
- Market reputation scores
- Industry benchmarks

## Test Execution Checklist

- [ ] Environment setup complete
- [ ] Test data loaded
- [ ] Authentication configured
- [ ] All endpoints tested individually
- [ ] Integration scenarios validated
- [ ] Performance benchmarks met
- [ ] Security tests passed
- [ ] Error handling verified
- [ ] Audit trails confirmed
- [ ] Documentation updated

## Expected Test Results

### Success Criteria
- All API endpoints return expected responses
- Performance metrics within acceptable ranges
- Security controls functioning properly
- Audit trails complete and accurate
- Error handling graceful and informative

### Failure Scenarios
- Document any failing tests with:
  - Endpoint details
  - Request/response data
  - Error messages
  - Suggested fixes
  - Priority level

## Post-Test Actions

1. **Bug Reports**: Create detailed reports for any failures
2. **Performance Analysis**: Review response times and optimization opportunities
3. **Security Review**: Assess any security vulnerabilities found
4. **Documentation Updates**: Update API documentation based on test results
5. **Monitoring Setup**: Configure alerts for production deployment