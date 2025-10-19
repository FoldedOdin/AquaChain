"""
Intelligent Technician Assignment Algorithm
Implements ETA-based assignment with performance tie-breaking and edge case handling
"""

import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from decimal import Decimal

from .location_service import LocationService
from .availability_manager import TechnicianAvailabilityManager

logger = logging.getLogger(__name__)

class TechnicianAssignmentAlgorithm:
    """Intelligent algorithm for assigning technicians to service requests"""
    
    def __init__(self, location_service: LocationService, availability_manager: TechnicianAvailabilityManager,
                 admin_topic_arn: str = None):
        self.location_service = location_service
        self.availability_manager = availability_manager
        self.admin_topic_arn = admin_topic_arn
        self.sns = boto3.client('sns')
        
        # Assignment parameters
        self.SERVICE_ZONE_MINUTES = 45  # Maximum driving time for service zone
        self.ETA_TOLERANCE_MINUTES = 5  # Tolerance for considering ETAs equal
        self.MAX_ASSIGNMENT_ATTEMPTS = 3  # Maximum attempts before escalation
    
    def assign_technician(self, service_request: Dict) -> Dict:
        """
        Main assignment method - finds and assigns the best technician for a service request
        
        Args:
            service_request: Service request details including location and priority
            
        Returns:
            Dict with assignment results
        """
        try:
            logger.info(f"Starting technician assignment for request {service_request['requestId']}")
            
            # Get consumer location
            consumer_location = service_request['location']
            
            # Validate location coordinates
            if not self._validate_location(consumer_location):
                return {
                    'success': False,
                    'error': 'Invalid consumer location coordinates',
                    'escalation_required': False
                }
            
            # Find available technicians
            available_technicians = self.availability_manager.find_all_available_technicians()
            
            if not available_technicians:
                logger.warning("No available technicians found")
                return self._handle_no_technicians_available(service_request)
            
            # Calculate ETA for all available technicians
            technicians_with_eta = self._calculate_technician_etas(
                available_technicians, consumer_location
            )
            
            # Filter technicians within service zone
            technicians_in_zone = [
                tech for tech in technicians_with_eta
                if tech.get('eta_minutes', float('inf')) <= self.SERVICE_ZONE_MINUTES
            ]
            
            if not technicians_in_zone:
                logger.warning("No technicians available within service zone")
                return self._handle_no_technicians_in_zone(service_request, technicians_with_eta)
            
            # Apply assignment algorithm
            selected_technician = self._select_best_technician(technicians_in_zone, service_request)
            
            if selected_technician:
                return {
                    'success': True,
                    'technician': selected_technician,
                    'assignment_reason': selected_technician.get('assignment_reason', 'best_match'),
                    'eta_minutes': selected_technician.get('eta_minutes'),
                    'estimated_arrival': selected_technician.get('estimated_arrival')
                }
            else:
                return self._handle_assignment_failure(service_request)
                
        except Exception as e:
            logger.error(f"Error in technician assignment: {str(e)}")
            return {
                'success': False,
                'error': f'Assignment algorithm error: {str(e)}',
                'escalation_required': True
            }
    
    def _validate_location(self, location: Dict) -> bool:
        """Validate location coordinates"""
        try:
            lat = float(location.get('latitude', 0))
            lon = float(location.get('longitude', 0))
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (ValueError, TypeError):
            return False
    
    def _calculate_technician_etas(self, technicians: List[Dict], consumer_location: Dict) -> List[Dict]:
        """Calculate ETA for all technicians to consumer location"""
        technicians_with_eta = []
        
        for technician in technicians:
            try:
                # Get technician location
                tech_location = technician['location']
                
                # Calculate route using AWS Location Service
                route_info = self.location_service.calculate_route(tech_location, consumer_location)
                
                if route_info:
                    technician['eta_minutes'] = route_info['duration_minutes']
                    technician['eta_seconds'] = route_info['duration_seconds']
                    technician['distance_km'] = route_info['distance_km']
                    technician['estimated_arrival'] = route_info['estimated_arrival']
                    technician['route_available'] = True
                else:
                    # If route calculation fails, mark as unreachable
                    technician['eta_minutes'] = float('inf')
                    technician['route_available'] = False
                
                technicians_with_eta.append(technician)
                
            except Exception as e:
                logger.error(f"Error calculating ETA for technician {technician['userId']}: {str(e)}")
                technician['eta_minutes'] = float('inf')
                technician['route_available'] = False
                technicians_with_eta.append(technician)
        
        return technicians_with_eta
    
    def _select_best_technician(self, technicians: List[Dict], service_request: Dict) -> Optional[Dict]:
        """
        Select the best technician using ETA-based assignment with performance tie-breaking
        
        Args:
            technicians: List of technicians within service zone
            service_request: Service request details
            
        Returns:
            Selected technician or None
        """
        if not technicians:
            return None
        
        # Sort technicians by ETA first
        technicians.sort(key=lambda t: t.get('eta_minutes', float('inf')))
        
        # Get the shortest ETA
        shortest_eta = technicians[0].get('eta_minutes', float('inf'))
        
        # Find all technicians within tolerance of shortest ETA
        candidates = []
        for tech in technicians:
            eta_diff = tech.get('eta_minutes', float('inf')) - shortest_eta
            if eta_diff <= self.ETA_TOLERANCE_MINUTES:
                candidates.append(tech)
        
        if len(candidates) == 1:
            # Single best candidate
            candidates[0]['assignment_reason'] = 'shortest_eta'
            return candidates[0]
        
        # Multiple candidates with similar ETA - use performance score for tie-breaking
        candidates.sort(key=lambda t: t.get('performanceScore', 0), reverse=True)
        
        best_candidate = candidates[0]
        best_candidate['assignment_reason'] = 'performance_tiebreaker'
        
        logger.info(f"Selected technician {best_candidate['userId']} with ETA {best_candidate.get('eta_minutes'):.1f} min "
                   f"and performance score {best_candidate.get('performanceScore', 0)}")
        
        return best_candidate
    
    def _handle_no_technicians_available(self, service_request: Dict) -> Dict:
        """Handle case when no technicians are available"""
        logger.warning(f"No available technicians for request {service_request['requestId']}")
        
        # Create P1 admin ticket
        self._create_p1_admin_ticket(
            service_request,
            'NO_TECHNICIANS_AVAILABLE',
            'No technicians are currently available for assignment'
        )
        
        return {
            'success': False,
            'error': 'No technicians available',
            'escalation_required': True,
            'escalation_type': 'no_technicians_available'
        }
    
    def _handle_no_technicians_in_zone(self, service_request: Dict, all_technicians: List[Dict]) -> Dict:
        """Handle case when no technicians are within service zone"""
        logger.warning(f"No technicians within service zone for request {service_request['requestId']}")
        
        # Find nearest technician for context
        nearest_tech = None
        if all_technicians:
            available_techs = [t for t in all_technicians if t.get('route_available', False)]
            if available_techs:
                nearest_tech = min(available_techs, key=lambda t: t.get('eta_minutes', float('inf')))
        
        # Create P1 admin ticket with context
        context_info = ""
        if nearest_tech:
            context_info = f" Nearest available technician is {nearest_tech.get('eta_minutes', 0):.1f} minutes away."
        
        self._create_p1_admin_ticket(
            service_request,
            'NO_TECHNICIANS_IN_ZONE',
            f'No technicians available within {self.SERVICE_ZONE_MINUTES}-minute service zone.{context_info}'
        )
        
        return {
            'success': False,
            'error': f'No technicians within {self.SERVICE_ZONE_MINUTES}-minute service zone',
            'escalation_required': True,
            'escalation_type': 'no_technicians_in_zone',
            'nearest_technician_eta': nearest_tech.get('eta_minutes') if nearest_tech else None
        }
    
    def _handle_assignment_failure(self, service_request: Dict) -> Dict:
        """Handle general assignment failure"""
        logger.error(f"Assignment algorithm failed for request {service_request['requestId']}")
        
        self._create_p1_admin_ticket(
            service_request,
            'ASSIGNMENT_ALGORITHM_FAILURE',
            'Technician assignment algorithm failed to select a technician'
        )
        
        return {
            'success': False,
            'error': 'Assignment algorithm failure',
            'escalation_required': True,
            'escalation_type': 'algorithm_failure'
        }
    
    def _create_p1_admin_ticket(self, service_request: Dict, ticket_type: str, description: str):
        """Create P1 admin ticket for escalation"""
        try:
            ticket_data = {
                'type': 'P1_TECHNICIAN_ASSIGNMENT_FAILURE',
                'subtype': ticket_type,
                'serviceRequestId': service_request['requestId'],
                'consumerId': service_request['consumerId'],
                'deviceId': service_request['deviceId'],
                'location': service_request['location'],
                'priority': service_request.get('priority', 'normal'),
                'description': description,
                'timestamp': datetime.utcnow().isoformat(),
                'requires_immediate_attention': True
            }
            
            # Send to admin SNS topic
            if self.admin_topic_arn:
                message = {
                    'default': json.dumps(ticket_data, indent=2),
                    'email': f"""
P1 ALERT: Technician Assignment Failure

Service Request: {service_request['requestId']}
Type: {ticket_type}
Description: {description}

Consumer: {service_request['consumerId']}
Device: {service_request['deviceId']}
Location: {service_request['location']}
Priority: {service_request.get('priority', 'normal')}

Immediate action required to assign technician or contact customer.

Timestamp: {datetime.utcnow().isoformat()}
                    """.strip()
                }
                
                self.sns.publish(
                    TopicArn=self.admin_topic_arn,
                    Subject=f'P1 Alert: Technician Assignment Failure - {service_request["requestId"]}',
                    Message=json.dumps(message),
                    MessageStructure='json'
                )
                
                logger.info(f"Created P1 admin ticket for service request {service_request['requestId']}")
            else:
                logger.warning("Admin topic ARN not configured - cannot send P1 ticket")
                
        except Exception as e:
            logger.error(f"Error creating P1 admin ticket: {str(e)}")
    
    def reassign_technician(self, service_request_id: str, reason: str = 'manual_reassignment') -> Dict:
        """
        Reassign a technician to an existing service request
        
        Args:
            service_request_id: ID of the service request to reassign
            reason: Reason for reassignment
            
        Returns:
            Dict with reassignment results
        """
        try:
            # This would typically fetch the service request from database
            # For now, we'll assume it's passed in or retrieved elsewhere
            logger.info(f"Attempting to reassign technician for request {service_request_id}")
            
            # Implementation would be similar to assign_technician but with additional
            # logic to handle the previous assignment
            
            return {
                'success': True,
                'message': f'Reassignment initiated for request {service_request_id}',
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Error in technician reassignment: {str(e)}")
            return {
                'success': False,
                'error': f'Reassignment failed: {str(e)}'
            }
    
    def get_assignment_metrics(self, period_days: int = 30) -> Dict:
        """
        Get assignment algorithm performance metrics
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Dict with assignment metrics
        """
        try:
            # This would analyze assignment success rates, average ETA, etc.
            # Implementation would query service requests and calculate metrics
            
            return {
                'period_days': period_days,
                'total_assignments': 0,
                'successful_assignments': 0,
                'success_rate': 0.0,
                'average_eta_minutes': 0.0,
                'escalations': 0,
                'escalation_rate': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating assignment metrics: {str(e)}")
            return {
                'error': f'Failed to calculate metrics: {str(e)}'
            }
    
    def validate_assignment_constraints(self, technician: Dict, service_request: Dict) -> Dict:
        """
        Validate that a technician assignment meets all constraints
        
        Args:
            technician: Technician details
            service_request: Service request details
            
        Returns:
            Dict with validation results
        """
        constraints_met = []
        constraints_failed = []
        
        try:
            # Check availability
            availability = self.availability_manager.is_technician_available(technician['userId'])
            if availability['available']:
                constraints_met.append('technician_available')
            else:
                constraints_failed.append(f"technician_not_available: {availability['reason']}")
            
            # Check service zone
            if technician.get('eta_minutes', float('inf')) <= self.SERVICE_ZONE_MINUTES:
                constraints_met.append('within_service_zone')
            else:
                constraints_failed.append(f"outside_service_zone: {technician.get('eta_minutes', 0):.1f} minutes")
            
            # Check route availability
            if technician.get('route_available', False):
                constraints_met.append('route_available')
            else:
                constraints_failed.append('route_not_available')
            
            return {
                'valid': len(constraints_failed) == 0,
                'constraints_met': constraints_met,
                'constraints_failed': constraints_failed,
                'technician_id': technician['userId']
            }
            
        except Exception as e:
            logger.error(f"Error validating assignment constraints: {str(e)}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }