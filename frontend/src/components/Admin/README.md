# Administrator Dashboard Components

This directory contains all components for the AquaChain Administrator Dashboard, implementing comprehensive system monitoring, user management, device management, and compliance reporting features.

## Components Overview

### System Monitoring (Task 9.1)

#### SystemHealthCard
- Real-time system health metrics display
- Uptime tracking for critical path, API, and notifications
- Error rate monitoring
- Active device and alert counts
- Color-coded status indicators based on SLA targets

#### DeviceFleetOverview
- Complete device fleet status visualization
- Filtering by status (online, offline, warning, error)
- Sortable device list by ID, uptime, WQI, or last seen
- Device details including location, consumer, battery level
- Real-time status updates

#### PerformanceMetricsChart
- Interactive performance metrics visualization using Recharts
- Multiple time ranges (1h, 24h, 7d, 30d)
- Four metric categories:
  - Alert Latency (avg, P95, P99)
  - Throughput & API Response Time
  - Lambda Invocations & Errors
  - DynamoDB Read/Write Capacity
- Current metrics summary with SLA compliance indicators

#### AlertAnalytics
- Alert volume and distribution analysis
- Pie charts for severity and type distribution
- Bar chart for top devices by alert count
- Resolution time tracking
- Detailed device alert breakdown

### User & Device Management (Task 9.2)

#### UserManagement
- Complete user lifecycle management (create, read, update, delete)
- Role-based filtering (consumer, technician, administrator)
- Search functionality across email and names
- User statistics dashboard
- Inline editing with modal forms
- Status management (active, inactive, suspended)

#### DeviceManagement
- Device registration and configuration
- Status management (active, inactive, maintenance)
- Device assignment to users
- Location and configuration management
- Alert threshold configuration per device
- Bulk operations support
- Serial number and firmware tracking

#### TechnicianManagement
- Technician profile and schedule management
- Work schedule editor with day-by-day configuration
- Performance score tracking
- Job statistics (completed, active, average rating)
- Override status management (available, unavailable, overtime)
- Certification tracking
- Service zone configuration

### Compliance & Audit (Task 9.3)

#### ComplianceReporting
- Automated compliance report generation
- Date range selection for custom reporting periods
- Comprehensive metrics:
  - Total readings and devices monitored
  - Alerts generated
  - Compliance rate calculation
  - Ledger verification status
  - Data integrity metrics (missing, duplicate, invalid readings)
  - System uptime metrics
- PDF and CSV export functionality
- Visual compliance status indicators

#### AuditTrailViewer
- Tamper-evident audit trail access
- Hash chain verification
- Cryptographic signature display
- Sequence number tracking
- Device filtering
- Expandable entry details showing:
  - Log ID
  - Data hash
  - Previous hash
  - Chain hash
  - KMS signature
- CSV export for regulatory compliance
- Verification status indicators

#### SystemConfiguration
- Global alert threshold management
- Notification settings configuration
- System limits configuration
- Maintenance mode controls
- Rate limiting settings
- Data retention policies
- Real-time configuration updates

## Data Flow

All components use the `adminService.ts` service layer which provides:
- Mock data for development
- Consistent API interface
- Error handling
- Loading states
- Type-safe data structures

## Type Definitions

All types are defined in `types/admin.ts`:
- SystemHealthMetrics
- DeviceFleetStatus
- PerformanceMetrics
- AlertAnalytics
- UserManagementData
- DeviceRegistration
- TechnicianManagementData
- ComplianceReport
- AuditTrailEntry
- SystemConfiguration

## Integration

The admin dashboard is integrated into the main application via:
- Route: `/admin`
- Protected by role-based access control (administrator role required)
- Accessible from the main navigation for administrator users

## Requirements Mapping

This implementation satisfies the following requirements from the spec:

### Requirement 4.1 & 4.2 (System Monitoring)
- Real-time dashboard showing system health metrics
- Uptime monitoring with 99.5% target tracking
- Device fleet status overview
- Performance metrics visualization

### Requirement 4.3 & 4.4 (User & Device Management)
- User account creation, modification, and deactivation
- Device fleet management with status and location tracking
- Technician management with work schedules
- Bulk operations support

### Requirement 4.5 (Compliance Reporting)
- Exportable compliance reports
- Ledger verification
- Audit trail access with hash chain verification

### Requirement 15.3 & 15.4 (Audit Trail)
- Public API endpoint simulation for hash chain verification
- Downloadable hash chain logs
- Independent verification capability
- Tamper-evident record display

## Future Enhancements

- Real-time WebSocket updates for live metrics
- Advanced filtering and search capabilities
- Custom dashboard layouts
- Automated alerting for SLA breaches
- Integration with external monitoring tools (PagerDuty, DataDog)
- Advanced analytics and trend analysis
- Machine learning insights for predictive maintenance
