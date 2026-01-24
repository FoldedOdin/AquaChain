# AquaChain Technician Service

The Technician Service is a comprehensive Lambda-based microservice that handles technician assignment, availability management, and service request lifecycle for the AquaChain water quality monitoring system.

## Features

### 1. AWS Location Service Integration (`location_service.py`)
- **Route Calculation**: Real-time ETA calculation using AWS Location Service
- **Geocoding**: Convert addresses to coordinates and vice versa
- **Service Zone Validation**: Check if technicians are within 45-minute driving time
- **Batch Operations**: Efficient routing calculations for multiple technicians

### 2. Technician Availability Management (`availability_manager.py`)
- **Work Schedule Management**: Define and validate technician work schedules
- **Availability Status Tracking**: Available/Unavailable/Overtime status management
- **Active Service Request Monitoring**: Prevent double-booking of technicians
- **Performance Score Calculation**: Weighted scoring based on customer satisfaction and efficiency

### 3. Intelligent Assignment Algorithm (`assignment_algorithm.py`)
- **ETA-Based Assignment**: Assign nearest available technician
- **Performance Tie-Breaking**: Use performance scores when ETAs are similar
- **Edge Case Handling**: Automatic P1 admin ticket creation when no technicians available
- **Service Zone Enforcement**: Ensure assignments are within 45-minute driving time

### 4. Service Request Lifecycle Management (`service_request_manager.py`)
- **Request Creation**: Create and track service requests
- **Status Management**: Handle complete request lifecycle with validation
- **Real-time Notifications**: WebSocket and SNS notifications for status updates
- **Customer Feedback**: Rating and feedback collection system

## API Endpoints

### Service Requests
- `POST /api/v1/service-requests` - Create new service request
- `GET /api/v1/service-requests/{requestId}` - Get service request details
- `PUT /api/v1/service-requests/{requestId}/status` - Update request status

### Technician Management
- `GET /api/v1/technicians/available` - List available technicians (admin only)
- `PUT /api/v1/technicians/{technicianId}/availability` - Update availability status
- `PUT /api/v1/technicians/{technicianId}/schedule` - Update work schedule

## Service Request Status Flow

```
pending → assigned → accepted → en_route → in_progress → completed
    ↓         ↓         ↓          ↓           ↓
cancelled  cancelled  cancelled  cancelled  cancelled
```

## Assignment Algorithm Logic

1. **Find Available Technicians**
   - Check work schedule compliance
   - Verify no active service requests
   - Respect manual availability overrides

2. **Calculate ETAs**
   - Use AWS Location Service for accurate routing
   - Filter by 45-minute service zone

3. **Select Best Technician**
   - Primary: Shortest ETA
   - Tie-breaker: Highest performance score
   - Edge case: Create P1 admin ticket if none available

## Performance Scoring

Technician performance scores are calculated monthly using:
- **Customer Satisfaction (70% weight)**: Average rating from 1-5 stars
- **Efficiency (30% weight)**: Completion time vs. estimated duration

## Environment Variables

```bash
USERS_TABLE=aquachain-users
SERVICE_REQUESTS_TABLE=aquachain-service-requests
LOCATION_MAP_NAME=aquachain-map
LOCATION_ROUTE_CALCULATOR=aquachain-routes
LOCATION_PLACE_INDEX=aquachain-places
ADMIN_TOPIC_ARN=arn:aws:sns:region:account:admin-alerts
NOTIFICATION_TOPIC_ARN=arn:aws:sns:region:account:service-notifications
WEBSOCKET_API_ENDPOINT=wss://api.aquachain.io/ws
```

## Required AWS Resources

### AWS Location Service
- **Map Resource**: `aquachain-map` (VectorEsriStreets)
- **Route Calculator**: `aquachain-routes` (Esri data source)
- **Place Index**: `aquachain-places` (for geocoding)
- **Geofence Collection**: `aquachain-service-zones` (optional)

### DynamoDB Tables
- **Users Table**: Technician profiles and schedules
- **Service Requests Table**: Request lifecycle tracking

### SNS Topics
- **Admin Topic**: P1 escalation alerts
- **Notification Topic**: Service updates

## IAM Permissions

The service requires permissions for:
- DynamoDB read/write operations
- AWS Location Service routing and geocoding
- SNS publishing for notifications
- API Gateway WebSocket management

## Error Handling

### P1 Admin Escalation
Automatic P1 tickets are created for:
- No available technicians
- No technicians within service zone
- Assignment algorithm failures

### Notification Strategy
- **Real-time**: WebSocket updates for active users
- **Push**: SNS notifications for mobile apps
- **Email**: Critical alerts and status updates

## Testing

The service includes comprehensive error handling and logging for:
- Route calculation failures
- Database connectivity issues
- Invalid location coordinates
- Authorization violations

## Deployment

Deploy using the provided `deployment.yaml` configuration with AWS SAM or CloudFormation. Ensure all AWS Location Service resources are created first using the `infrastructure/location/setup.py` script.

## Monitoring

Key metrics to monitor:
- Assignment success rate
- Average ETA accuracy
- P1 escalation frequency
- API response times
- Location service API usage

## Security

- JWT token validation for all endpoints
- Role-based access control (consumer/technician/admin)
- Input validation and sanitization
- Encrypted data transmission
- Audit logging for sensitive operations