"""
AWS Location Service utilities for routing and geocoding
"""

import boto3
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Import structured logging
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger

logger = get_logger(__name__, service='location-service')

class LocationService:
    """AWS Location Service wrapper for routing and geocoding operations"""
    
    def __init__(self, map_name: str, route_calculator_name: str, place_index_name: str = None):
        self.location_client = boto3.client('location')
        self.map_name = map_name
        self.route_calculator_name = route_calculator_name
        self.place_index_name = place_index_name
    
    def calculate_route(self, origin: Dict[str, float], destination: Dict[str, float], 
                       travel_mode: str = 'Car') -> Optional[Dict]:
        """
        Calculate route between two points using AWS Location Service
        
        Args:
            origin: {'latitude': float, 'longitude': float}
            destination: {'latitude': float, 'longitude': float}
            travel_mode: 'Car', 'Truck', 'Walking'
            
        Returns:
            Dict with route information or None if calculation fails
        """
        try:
            # Convert to AWS Location Service format [longitude, latitude]
            departure_position = [origin['longitude'], origin['latitude']]
            destination_position = [destination['longitude'], destination['latitude']]
            
            response = self.location_client.calculate_route(
                CalculatorName=self.route_calculator_name,
                DeparturePosition=departure_position,
                DestinationPosition=destination_position,
                TravelMode=travel_mode,
                DepartNow=True,
                IncludeLegGeometry=False,  # Don't need detailed geometry for ETA calculation
                DistanceUnit='Kilometers'
            )
            
            summary = response['Summary']
            
            return {
                'duration_seconds': summary['DurationSeconds'],
                'duration_minutes': summary['DurationSeconds'] / 60,
                'distance_km': summary['Distance'],
                'estimated_arrival': (datetime.utcnow() + 
                                    timedelta(seconds=summary['DurationSeconds'])).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating route: {str(e)}")
            return None
    
    def calculate_eta_to_multiple_destinations(self, origin: Dict[str, float], 
                                             destinations: List[Dict]) -> List[Dict]:
        """
        Calculate ETA from origin to multiple destinations
        
        Args:
            origin: {'latitude': float, 'longitude': float}
            destinations: List of dicts with 'latitude', 'longitude', and 'id' keys
            
        Returns:
            List of destinations with ETA information added
        """
        results = []
        
        for destination in destinations:
            route_info = self.calculate_route(origin, destination)
            
            destination_with_eta = destination.copy()
            if route_info:
                destination_with_eta.update({
                    'eta_minutes': route_info['duration_minutes'],
                    'eta_seconds': route_info['duration_seconds'],
                    'distance_km': route_info['distance_km'],
                    'estimated_arrival': route_info['estimated_arrival']
                })
            else:
                # If route calculation fails, mark as unreachable
                destination_with_eta.update({
                    'eta_minutes': float('inf'),
                    'eta_seconds': float('inf'),
                    'distance_km': float('inf'),
                    'estimated_arrival': None,
                    'unreachable': True
                })
            
            results.append(destination_with_eta)
        
        return results
    
    def is_within_service_zone(self, origin: Dict[str, float], destination: Dict[str, float], 
                              max_minutes: int = 45) -> bool:
        """
        Check if destination is within service zone (driving time threshold)
        
        Args:
            origin: Technician location
            destination: Consumer location
            max_minutes: Maximum driving time in minutes
            
        Returns:
            True if within service zone, False otherwise
        """
        route_info = self.calculate_route(origin, destination)
        
        if not route_info:
            return False
        
        return route_info['duration_minutes'] <= max_minutes
    
    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Convert address to coordinates using AWS Location Service
        
        Args:
            address: Street address to geocode
            
        Returns:
            {'latitude': float, 'longitude': float} or None if geocoding fails
        """
        if not self.place_index_name:
            logger.warning("Place index not configured for geocoding")
            return None
        
        try:
            response = self.location_client.search_place_index_for_text(
                IndexName=self.place_index_name,
                Text=address,
                MaxResults=1
            )
            
            if response['Results']:
                place = response['Results'][0]['Place']
                geometry = place['Geometry']['Point']
                
                return {
                    'latitude': geometry[1],
                    'longitude': geometry[0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {str(e)}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Convert coordinates to address using AWS Location Service
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Address string or None if reverse geocoding fails
        """
        if not self.place_index_name:
            logger.warning("Place index not configured for reverse geocoding")
            return None
        
        try:
            response = self.location_client.search_place_index_for_position(
                IndexName=self.place_index_name,
                Position=[longitude, latitude],
                MaxResults=1
            )
            
            if response['Results']:
                place = response['Results'][0]['Place']
                return place.get('Label', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Error reverse geocoding coordinates ({latitude}, {longitude}): {str(e)}")
            return None
    
    def batch_calculate_routes(self, origins: List[Dict], destinations: List[Dict]) -> List[Dict]:
        """
        Calculate routes between multiple origins and destinations
        Useful for finding optimal technician assignments
        
        Args:
            origins: List of origin points with 'id', 'latitude', 'longitude'
            destinations: List of destination points with 'id', 'latitude', 'longitude'
            
        Returns:
            List of route calculations with origin_id, destination_id, and route info
        """
        results = []
        
        for origin in origins:
            for destination in destinations:
                route_info = self.calculate_route(origin, destination)
                
                result = {
                    'origin_id': origin.get('id'),
                    'destination_id': destination.get('id'),
                    'origin': origin,
                    'destination': destination
                }
                
                if route_info:
                    result.update(route_info)
                else:
                    result.update({
                        'duration_minutes': float('inf'),
                        'distance_km': float('inf'),
                        'unreachable': True
                    })
                
                results.append(result)
        
        return results
    
    def find_nearest_technicians(self, consumer_location: Dict[str, float], 
                                technician_locations: List[Dict], 
                                max_results: int = 5) -> List[Dict]:
        """
        Find nearest technicians to a consumer location
        
        Args:
            consumer_location: Consumer's coordinates
            technician_locations: List of technician locations with 'id', 'latitude', 'longitude'
            max_results: Maximum number of results to return
            
        Returns:
            List of nearest technicians sorted by ETA
        """
        # Calculate ETA to all technicians
        technicians_with_eta = self.calculate_eta_to_multiple_destinations(
            consumer_location, technician_locations
        )
        
        # Filter out unreachable technicians and sort by ETA
        reachable_technicians = [
            tech for tech in technicians_with_eta 
            if not tech.get('unreachable', False)
        ]
        
        reachable_technicians.sort(key=lambda x: x.get('eta_minutes', float('inf')))
        
        return reachable_technicians[:max_results]


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate latitude and longitude coordinates
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def calculate_distance_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using Haversine formula
    Useful for quick distance estimates without API calls
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        Distance in kilometers
    """
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r


def estimate_driving_time(distance_km: float, avg_speed_kmh: float = 50) -> float:
    """
    Estimate driving time based on distance and average speed
    
    Args:
        distance_km: Distance in kilometers
        avg_speed_kmh: Average driving speed in km/h
        
    Returns:
        Estimated time in minutes
    """
    return (distance_km / avg_speed_kmh) * 60