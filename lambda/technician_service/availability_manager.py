"""
Technician Availability Management System
Handles work schedules, availability status, and performance scoring
"""

import boto3
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import json

logger = logging.getLogger(__name__)

class TechnicianAvailabilityManager:
    """Manages technician availability, schedules, and performance scoring"""
    
    def __init__(self, users_table_name: str, service_requests_table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.users_table = self.dynamodb.Table(users_table_name)
        self.service_requests_table = self.dynamodb.Table(service_requests_table_name)
    
    def is_technician_available(self, technician_id: str, check_time: datetime = None) -> Dict:
        """
        Comprehensive availability check for a technician
        
        Args:
            technician_id: Technician's user ID
            check_time: Time to check availability (defaults to current time)
            
        Returns:
            Dict with availability status and reasons
        """
        if check_time is None:
            check_time = datetime.utcnow()
        
        try:
            # Get technician record
            response = self.users_table.get_item(Key={'userId': technician_id})
            
            if 'Item' not in response:
                return {
                    'available': False,
                    'reason': 'technician_not_found',
                    'details': 'Technician record not found'
                }
            
            technician = response['Item']
            
            if technician.get('role') != 'technician':
                return {
                    'available': False,
                    'reason': 'not_technician',
                    'details': 'User is not a technician'
                }
            
            # Check manual override status
            work_schedule = technician.get('workSchedule', {})
            override_status = work_schedule.get('overrideStatus', 'available')
            
            if override_status == 'unavailable':
                return {
                    'available': False,
                    'reason': 'manual_override',
                    'details': 'Technician manually set to unavailable'
                }
            
            # Check work schedule (unless override allows overtime)
            if override_status != 'available_overtime':
                schedule_check = self.check_work_schedule(technician, check_time)
                if not schedule_check['within_schedule']:
                    return {
                        'available': False,
                        'reason': 'outside_work_hours',
                        'details': schedule_check['details']
                    }
            
            # Check for active service requests
            active_request_check = self.check_active_service_requests(technician_id)
            if active_request_check['has_active']:
                return {
                    'available': False,
                    'reason': 'active_service_request',
                    'details': active_request_check['details']
                }
            
            return {
                'available': True,
                'reason': 'available',
                'details': 'Technician is available for assignment',
                'override_status': override_status
            }
            
        except Exception as e:
            logger.error(f"Error checking technician availability: {str(e)}")
            return {
                'available': False,
                'reason': 'system_error',
                'details': f'Error checking availability: {str(e)}'
            }
    
    def check_work_schedule(self, technician: Dict, check_time: datetime) -> Dict:
        """
        Check if technician is within their defined work schedule
        
        Args:
            technician: Technician record from database
            check_time: Time to check against schedule
            
        Returns:
            Dict with schedule check results
        """
        try:
            work_schedule = technician.get('workSchedule', {})
            
            # Get current day of week
            current_day = check_time.strftime('%A').lower()
            
            # Check if technician has schedule for this day
            day_schedule = work_schedule.get(current_day)
            if not day_schedule:
                return {
                    'within_schedule': False,
                    'details': f'No work schedule defined for {current_day.capitalize()}'
                }
            
            # Parse start and end times
            try:
                start_time = datetime.strptime(day_schedule['start'], '%H:%M').time()
                end_time = datetime.strptime(day_schedule['end'], '%H:%M').time()
            except (ValueError, KeyError) as e:
                return {
                    'within_schedule': False,
                    'details': f'Invalid schedule format for {current_day.capitalize()}: {str(e)}'
                }
            
            current_time_only = check_time.time()
            
            # Handle schedules that cross midnight
            if start_time <= end_time:
                # Normal schedule (e.g., 9:00 AM - 5:00 PM)
                within_schedule = start_time <= current_time_only <= end_time
            else:
                # Schedule crosses midnight (e.g., 10:00 PM - 6:00 AM)
                within_schedule = current_time_only >= start_time or current_time_only <= end_time
            
            if within_schedule:
                return {
                    'within_schedule': True,
                    'details': f'Within work hours for {current_day.capitalize()} ({day_schedule["start"]} - {day_schedule["end"]})'
                }
            else:
                return {
                    'within_schedule': False,
                    'details': f'Outside work hours for {current_day.capitalize()} ({day_schedule["start"]} - {day_schedule["end"]})'
                }
                
        except Exception as e:
            logger.error(f"Error checking work schedule: {str(e)}")
            return {
                'within_schedule': False,
                'details': f'Error checking schedule: {str(e)}'
            }
    
    def check_active_service_requests(self, technician_id: str) -> Dict:
        """
        Check if technician has any active service requests
        
        Args:
            technician_id: Technician's user ID
            
        Returns:
            Dict with active request check results
        """
        try:
            # Query service requests for this technician with active statuses
            active_statuses = ['accepted', 'en_route', 'in_progress']
            
            response = self.service_requests_table.scan(
                FilterExpression='technicianId = :tid AND #status IN (:accepted, :en_route, :in_progress)',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':tid': technician_id,
                    ':accepted': 'accepted',
                    ':en_route': 'en_route',
                    ':in_progress': 'in_progress'
                }
            )
            
            active_requests = response['Items']
            
            if active_requests:
                request_details = []
                for request in active_requests:
                    request_details.append({
                        'requestId': request['requestId'],
                        'status': request['status'],
                        'createdAt': request['createdAt']
                    })
                
                return {
                    'has_active': True,
                    'count': len(active_requests),
                    'details': f'Technician has {len(active_requests)} active service request(s)',
                    'requests': request_details
                }
            else:
                return {
                    'has_active': False,
                    'count': 0,
                    'details': 'No active service requests'
                }
                
        except Exception as e:
            logger.error(f"Error checking active service requests: {str(e)}")
            return {
                'has_active': True,  # Err on the side of caution
                'details': f'Error checking active requests: {str(e)}'
            }
    
    def update_availability_status(self, technician_id: str, override_status: str, 
                                 updated_by: str = None) -> Dict:
        """
        Update technician's manual availability override
        
        Args:
            technician_id: Technician's user ID
            override_status: 'available', 'unavailable', or 'available_overtime'
            updated_by: User ID who made the update
            
        Returns:
            Dict with update results
        """
        valid_statuses = ['available', 'unavailable', 'available_overtime']
        
        if override_status not in valid_statuses:
            return {
                'success': False,
                'error': f'Invalid override status. Must be one of: {valid_statuses}'
            }
        
        try:
            # Get current technician record
            response = self.users_table.get_item(Key={'userId': technician_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Technician not found'
                }
            
            technician = response['Item']
            
            # Initialize work schedule if it doesn't exist
            if 'workSchedule' not in technician:
                technician['workSchedule'] = {}
            
            # Update override status
            technician['workSchedule']['overrideStatus'] = override_status
            technician['workSchedule']['lastUpdated'] = datetime.utcnow().isoformat()
            
            if updated_by:
                technician['workSchedule']['updatedBy'] = updated_by
            
            # Save updated record
            self.users_table.put_item(Item=technician)
            
            logger.info(f"Updated availability for technician {technician_id} to {override_status}")
            
            return {
                'success': True,
                'message': f'Availability status updated to {override_status}',
                'previous_status': response['Item'].get('workSchedule', {}).get('overrideStatus', 'available')
            }
            
        except Exception as e:
            logger.error(f"Error updating availability status: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to update availability: {str(e)}'
            }
    
    def update_work_schedule(self, technician_id: str, schedule: Dict, updated_by: str = None) -> Dict:
        """
        Update technician's work schedule
        
        Args:
            technician_id: Technician's user ID
            schedule: Dict with day names as keys and {'start': 'HH:MM', 'end': 'HH:MM'} as values
            updated_by: User ID who made the update
            
        Returns:
            Dict with update results
        """
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        try:
            # Validate schedule format
            for day, times in schedule.items():
                if day.lower() not in valid_days:
                    return {
                        'success': False,
                        'error': f'Invalid day: {day}. Must be one of: {valid_days}'
                    }
                
                if not isinstance(times, dict) or 'start' not in times or 'end' not in times:
                    return {
                        'success': False,
                        'error': f'Invalid schedule format for {day}. Must have "start" and "end" times'
                    }
                
                # Validate time format
                try:
                    datetime.strptime(times['start'], '%H:%M')
                    datetime.strptime(times['end'], '%H:%M')
                except ValueError:
                    return {
                        'success': False,
                        'error': f'Invalid time format for {day}. Use HH:MM format (24-hour)'
                    }
            
            # Get current technician record
            response = self.users_table.get_item(Key={'userId': technician_id})
            
            if 'Item' not in response:
                return {
                    'success': False,
                    'error': 'Technician not found'
                }
            
            technician = response['Item']
            
            # Initialize work schedule if it doesn't exist
            if 'workSchedule' not in technician:
                technician['workSchedule'] = {}
            
            # Update schedule
            for day, times in schedule.items():
                technician['workSchedule'][day.lower()] = {
                    'start': times['start'],
                    'end': times['end']
                }
            
            technician['workSchedule']['lastUpdated'] = datetime.utcnow().isoformat()
            
            if updated_by:
                technician['workSchedule']['updatedBy'] = updated_by
            
            # Save updated record
            self.users_table.put_item(Item=technician)
            
            logger.info(f"Updated work schedule for technician {technician_id}")
            
            return {
                'success': True,
                'message': 'Work schedule updated successfully',
                'updated_days': list(schedule.keys())
            }
            
        except Exception as e:
            logger.error(f"Error updating work schedule: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to update work schedule: {str(e)}'
            }
    
    def calculate_performance_score(self, technician_id: str, period_days: int = 30) -> Dict:
        """
        Calculate technician performance score based on customer satisfaction and completion time
        
        Args:
            technician_id: Technician's user ID
            period_days: Number of days to look back for performance calculation
            
        Returns:
            Dict with performance score and breakdown
        """
        try:
            # Get completed service requests for the period
            cutoff_date = (datetime.utcnow() - timedelta(days=period_days)).isoformat()
            
            response = self.service_requests_table.scan(
                FilterExpression='technicianId = :tid AND #status = :completed AND completedAt >= :cutoff',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':tid': technician_id,
                    ':completed': 'completed',
                    ':cutoff': cutoff_date
                }
            )
            
            completed_requests = response['Items']
            
            if not completed_requests:
                return {
                    'performance_score': 0,
                    'breakdown': {
                        'satisfaction_score': 0,
                        'efficiency_score': 0,
                        'total_jobs': 0
                    },
                    'message': f'No completed jobs in the last {period_days} days'
                }
            
            # Calculate satisfaction score (70% weight)
            satisfaction_ratings = []
            efficiency_scores = []
            
            for request in completed_requests:
                # Customer satisfaction rating (1-5 scale)
                rating = request.get('customerRating')
                if rating is not None:
                    satisfaction_ratings.append(float(rating))
                
                # Calculate efficiency score based on completion time vs estimated time
                created_at = datetime.fromisoformat(request['createdAt'].replace('Z', '+00:00'))
                completed_at = datetime.fromisoformat(request['completedAt'].replace('Z', '+00:00'))
                actual_duration = (completed_at - created_at).total_seconds() / 3600  # hours
                
                # Estimate expected duration based on job type (default 2 hours)
                estimated_duration = request.get('estimatedDuration', 2.0)
                
                if estimated_duration > 0:
                    efficiency_ratio = estimated_duration / actual_duration
                    # Cap efficiency score between 0 and 2 (2 = completed in half the time)
                    efficiency_score = min(2.0, max(0.0, efficiency_ratio))
                    efficiency_scores.append(efficiency_score)
            
            # Calculate average scores
            avg_satisfaction = sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else 3.0
            avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 1.0
            
            # Normalize satisfaction to 0-1 scale (5-star rating)
            satisfaction_normalized = (avg_satisfaction - 1) / 4  # Convert 1-5 to 0-1
            
            # Normalize efficiency to 0-1 scale
            efficiency_normalized = min(1.0, avg_efficiency / 2.0)  # Convert 0-2 to 0-1
            
            # Calculate weighted performance score (0-100 scale)
            performance_score = (satisfaction_normalized * 0.7 + efficiency_normalized * 0.3) * 100
            
            # Update technician record with new performance score
            self.users_table.update_item(
                Key={'userId': technician_id},
                UpdateExpression='SET performanceScore = :score, performanceLastUpdated = :updated',
                ExpressionAttributeValues={
                    ':score': Decimal(str(round(performance_score, 2))),
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            
            return {
                'performance_score': round(performance_score, 2),
                'breakdown': {
                    'satisfaction_score': round(avg_satisfaction, 2),
                    'satisfaction_normalized': round(satisfaction_normalized * 100, 2),
                    'efficiency_score': round(avg_efficiency, 2),
                    'efficiency_normalized': round(efficiency_normalized * 100, 2),
                    'total_jobs': len(completed_requests),
                    'jobs_with_ratings': len(satisfaction_ratings)
                },
                'period_days': period_days
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {str(e)}")
            return {
                'performance_score': 0,
                'error': f'Failed to calculate performance score: {str(e)}'
            }
    
    def get_technician_availability_summary(self, technician_id: str) -> Dict:
        """
        Get comprehensive availability summary for a technician
        
        Args:
            technician_id: Technician's user ID
            
        Returns:
            Dict with complete availability information
        """
        try:
            # Get technician record
            response = self.users_table.get_item(Key={'userId': technician_id})
            
            if 'Item' not in response:
                return {'error': 'Technician not found'}
            
            technician = response['Item']
            
            # Check current availability
            availability = self.is_technician_available(technician_id)
            
            # Get work schedule
            work_schedule = technician.get('workSchedule', {})
            
            # Get active service requests
            active_requests = self.check_active_service_requests(technician_id)
            
            # Get performance score
            performance_info = self.calculate_performance_score(technician_id)
            
            return {
                'technician_id': technician_id,
                'name': f"{technician['profile']['firstName']} {technician['profile']['lastName']}",
                'availability': availability,
                'work_schedule': {
                    day: schedule for day, schedule in work_schedule.items()
                    if day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                },
                'override_status': work_schedule.get('overrideStatus', 'available'),
                'active_requests': active_requests,
                'performance': performance_info,
                'last_updated': work_schedule.get('lastUpdated'),
                'location': technician['profile']['address']['coordinates']
            }
            
        except Exception as e:
            logger.error(f"Error getting availability summary: {str(e)}")
            return {'error': f'Failed to get availability summary: {str(e)}'}
    
    def find_all_available_technicians(self, check_time: datetime = None) -> List[Dict]:
        """
        Find all currently available technicians
        
        Args:
            check_time: Time to check availability (defaults to current time)
            
        Returns:
            List of available technicians with their details
        """
        if check_time is None:
            check_time = datetime.utcnow()
        
        try:
            # Get all technicians
            response = self.users_table.scan(
                FilterExpression='#role = :role',
                ExpressionAttributeNames={'#role': 'role'},
                ExpressionAttributeValues={':role': 'technician'}
            )
            
            available_technicians = []
            
            for technician in response['Items']:
                availability = self.is_technician_available(technician['userId'], check_time)
                
                if availability['available']:
                    technician_info = {
                        'userId': technician['userId'],
                        'name': f"{technician['profile']['firstName']} {technician['profile']['lastName']}",
                        'location': technician['profile']['address']['coordinates'],
                        'performanceScore': float(technician.get('performanceScore', 0)),
                        'availability': availability,
                        'phone': technician['profile']['phone']
                    }
                    available_technicians.append(technician_info)
            
            # Sort by performance score (descending)
            available_technicians.sort(key=lambda x: x['performanceScore'], reverse=True)
            
            return available_technicians
            
        except Exception as e:
            logger.error(f"Error finding available technicians: {str(e)}")
            return []