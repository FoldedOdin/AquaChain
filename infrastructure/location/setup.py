"""
AWS Location Service Infrastructure Setup
Creates map resources, route calculators, and place indexes for technician routing
"""

import boto3
import logging
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class LocationServiceSetup:
    """Setup AWS Location Service resources for AquaChain system"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.location_client = boto3.client('location', region_name=region)
        self.region = region
    
    def create_map_resource(self, map_name: str = 'aquachain-map') -> Dict:
        """
        Create map resource for visualization and routing
        
        Args:
            map_name: Name for the map resource
            
        Returns:
            Dict with creation results
        """
        try:
            # Check if map already exists
            try:
                response = self.location_client.describe_map(MapName=map_name)
                logger.info(f"Map {map_name} already exists")
                return {
                    'success': True,
                    'map_name': map_name,
                    'map_arn': response['MapArn'],
                    'status': 'already_exists'
                }
            except self.location_client.exceptions.ResourceNotFoundException:
                pass
            
            # Create new map resource
            response = self.location_client.create_map(
                MapName=map_name,
                Configuration={
                    'Style': 'VectorEsriStreets'  # Good for routing and navigation
                },
                Description='AquaChain technician routing map',
                Tags={
                    'Project': 'AquaChain',
                    'Environment': 'production',
                    'Purpose': 'technician-routing'
                }
            )
            
            logger.info(f"Created map resource: {map_name}")
            
            return {
                'success': True,
                'map_name': map_name,
                'map_arn': response['MapArn'],
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Error creating map resource: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create map: {str(e)}'
            }
    
    def create_route_calculator(self, calculator_name: str = 'aquachain-routes') -> Dict:
        """
        Create route calculator for ETA calculations
        
        Args:
            calculator_name: Name for the route calculator
            
        Returns:
            Dict with creation results
        """
        try:
            # Check if route calculator already exists
            try:
                response = self.location_client.describe_route_calculator(
                    CalculatorName=calculator_name
                )
                logger.info(f"Route calculator {calculator_name} already exists")
                return {
                    'success': True,
                    'calculator_name': calculator_name,
                    'calculator_arn': response['CalculatorArn'],
                    'status': 'already_exists'
                }
            except self.location_client.exceptions.ResourceNotFoundException:
                pass
            
            # Create new route calculator
            response = self.location_client.create_route_calculator(
                CalculatorName=calculator_name,
                DataSource='Esri',  # High-quality routing data
                Description='AquaChain technician ETA calculator',
                Tags={
                    'Project': 'AquaChain',
                    'Environment': 'production',
                    'Purpose': 'eta-calculation'
                }
            )
            
            logger.info(f"Created route calculator: {calculator_name}")
            
            return {
                'success': True,
                'calculator_name': calculator_name,
                'calculator_arn': response['CalculatorArn'],
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Error creating route calculator: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create route calculator: {str(e)}'
            }
    
    def create_place_index(self, index_name: str = 'aquachain-places') -> Dict:
        """
        Create place index for geocoding and reverse geocoding
        
        Args:
            index_name: Name for the place index
            
        Returns:
            Dict with creation results
        """
        try:
            # Check if place index already exists
            try:
                response = self.location_client.describe_place_index(IndexName=index_name)
                logger.info(f"Place index {index_name} already exists")
                return {
                    'success': True,
                    'index_name': index_name,
                    'index_arn': response['IndexArn'],
                    'status': 'already_exists'
                }
            except self.location_client.exceptions.ResourceNotFoundException:
                pass
            
            # Create new place index
            response = self.location_client.create_place_index(
                IndexName=index_name,
                DataSource='Esri',  # Comprehensive place data
                Description='AquaChain address geocoding index',
                Tags={
                    'Project': 'AquaChain',
                    'Environment': 'production',
                    'Purpose': 'geocoding'
                }
            )
            
            logger.info(f"Created place index: {index_name}")
            
            return {
                'success': True,
                'index_name': index_name,
                'index_arn': response['IndexArn'],
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Error creating place index: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create place index: {str(e)}'
            }
    
    def create_geofence_collection(self, collection_name: str = 'aquachain-service-zones') -> Dict:
        """
        Create geofence collection for service zone management
        
        Args:
            collection_name: Name for the geofence collection
            
        Returns:
            Dict with creation results
        """
        try:
            # Check if collection already exists
            try:
                response = self.location_client.describe_geofence_collection(
                    CollectionName=collection_name
                )
                logger.info(f"Geofence collection {collection_name} already exists")
                return {
                    'success': True,
                    'collection_name': collection_name,
                    'collection_arn': response['CollectionArn'],
                    'status': 'already_exists'
                }
            except self.location_client.exceptions.ResourceNotFoundException:
                pass
            
            # Create new geofence collection
            response = self.location_client.create_geofence_collection(
                CollectionName=collection_name,
                Description='AquaChain service zone geofences',
                Tags={
                    'Project': 'AquaChain',
                    'Environment': 'production',
                    'Purpose': 'service-zones'
                }
            )
            
            logger.info(f"Created geofence collection: {collection_name}")
            
            return {
                'success': True,
                'collection_name': collection_name,
                'collection_arn': response['CollectionArn'],
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Error creating geofence collection: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create geofence collection: {str(e)}'
            }
    
    def setup_all_resources(self) -> Dict:
        """
        Set up all AWS Location Service resources for AquaChain
        
        Returns:
            Dict with setup results for all resources
        """
        results = {
            'success': True,
            'resources': {},
            'errors': []
        }
        
        # Create map resource
        map_result = self.create_map_resource()
        results['resources']['map'] = map_result
        if not map_result['success']:
            results['success'] = False
            results['errors'].append(f"Map creation failed: {map_result['error']}")
        
        # Create route calculator
        route_result = self.create_route_calculator()
        results['resources']['route_calculator'] = route_result
        if not route_result['success']:
            results['success'] = False
            results['errors'].append(f"Route calculator creation failed: {route_result['error']}")
        
        # Create place index
        place_result = self.create_place_index()
        results['resources']['place_index'] = place_result
        if not place_result['success']:
            results['success'] = False
            results['errors'].append(f"Place index creation failed: {place_result['error']}")
        
        # Create geofence collection
        geofence_result = self.create_geofence_collection()
        results['resources']['geofence_collection'] = geofence_result
        if not geofence_result['success']:
            results['success'] = False
            results['errors'].append(f"Geofence collection creation failed: {geofence_result['error']}")
        
        return results
    
    def create_iam_policy(self) -> Dict:
        """
        Create IAM policy for Location Service access
        
        Returns:
            Dict with policy document
        """
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "geo:CalculateRoute",
                        "geo:SearchPlaceIndexForText",
                        "geo:SearchPlaceIndexForPosition",
                        "geo:GetGeofence",
                        "geo:ListGeofences",
                        "geo:PutGeofence"
                    ],
                    "Resource": [
                        f"arn:aws:geo:{self.region}:*:route-calculator/aquachain-routes",
                        f"arn:aws:geo:{self.region}:*:place-index/aquachain-places",
                        f"arn:aws:geo:{self.region}:*:geofence-collection/aquachain-service-zones"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "geo:GetMap*"
                    ],
                    "Resource": [
                        f"arn:aws:geo:{self.region}:*:map/aquachain-map"
                    ]
                }
            ]
        }
        
        return {
            'success': True,
            'policy_document': policy_document,
            'policy_name': 'AquaChainLocationServicePolicy'
        }
    
    def test_location_services(self) -> Dict:
        """
        Test AWS Location Service setup with sample requests
        
        Returns:
            Dict with test results
        """
        test_results = {
            'success': True,
            'tests': {},
            'errors': []
        }
        
        try:
            # Test route calculation
            try:
                route_response = self.location_client.calculate_route(
                    CalculatorName='aquachain-routes',
                    DeparturePosition=[-122.4194, 37.7749],  # San Francisco
                    DestinationPosition=[-122.4094, 37.7849],  # Nearby location
                    TravelMode='Car'
                )
                
                test_results['tests']['route_calculation'] = {
                    'success': True,
                    'duration_seconds': route_response['Summary']['DurationSeconds'],
                    'distance_km': route_response['Summary']['Distance'] / 1000
                }
                
            except Exception as e:
                test_results['success'] = False
                test_results['tests']['route_calculation'] = {
                    'success': False,
                    'error': str(e)
                }
                test_results['errors'].append(f"Route calculation test failed: {str(e)}")
            
            # Test geocoding
            try:
                geocode_response = self.location_client.search_place_index_for_text(
                    IndexName='aquachain-places',
                    Text='1600 Amphitheatre Parkway, Mountain View, CA',
                    MaxResults=1
                )
                
                if geocode_response['Results']:
                    coordinates = geocode_response['Results'][0]['Place']['Geometry']['Point']
                    test_results['tests']['geocoding'] = {
                        'success': True,
                        'coordinates': coordinates
                    }
                else:
                    test_results['tests']['geocoding'] = {
                        'success': False,
                        'error': 'No results returned'
                    }
                
            except Exception as e:
                test_results['success'] = False
                test_results['tests']['geocoding'] = {
                    'success': False,
                    'error': str(e)
                }
                test_results['errors'].append(f"Geocoding test failed: {str(e)}")
            
            # Test reverse geocoding
            try:
                reverse_response = self.location_client.search_place_index_for_position(
                    IndexName='aquachain-places',
                    Position=[-122.0822, 37.4220],  # Google HQ coordinates
                    MaxResults=1
                )
                
                if reverse_response['Results']:
                    address = reverse_response['Results'][0]['Place']['Label']
                    test_results['tests']['reverse_geocoding'] = {
                        'success': True,
                        'address': address
                    }
                else:
                    test_results['tests']['reverse_geocoding'] = {
                        'success': False,
                        'error': 'No results returned'
                    }
                
            except Exception as e:
                test_results['success'] = False
                test_results['tests']['reverse_geocoding'] = {
                    'success': False,
                    'error': str(e)
                }
                test_results['errors'].append(f"Reverse geocoding test failed: {str(e)}")
            
        except Exception as e:
            test_results['success'] = False
            test_results['errors'].append(f"General test error: {str(e)}")
        
        return test_results
    
    def cleanup_resources(self) -> Dict:
        """
        Clean up all AWS Location Service resources (for testing/development)
        
        Returns:
            Dict with cleanup results
        """
        cleanup_results = {
            'success': True,
            'cleaned_up': [],
            'errors': []
        }
        
        resources_to_cleanup = [
            ('map', 'aquachain-map', self.location_client.delete_map),
            ('route_calculator', 'aquachain-routes', self.location_client.delete_route_calculator),
            ('place_index', 'aquachain-places', self.location_client.delete_place_index),
            ('geofence_collection', 'aquachain-service-zones', self.location_client.delete_geofence_collection)
        ]
        
        for resource_type, resource_name, delete_function in resources_to_cleanup:
            try:
                if resource_type == 'map':
                    delete_function(MapName=resource_name)
                elif resource_type == 'route_calculator':
                    delete_function(CalculatorName=resource_name)
                elif resource_type == 'place_index':
                    delete_function(IndexName=resource_name)
                elif resource_type == 'geofence_collection':
                    delete_function(CollectionName=resource_name)
                
                cleanup_results['cleaned_up'].append(f"{resource_type}: {resource_name}")
                logger.info(f"Deleted {resource_type}: {resource_name}")
                
            except self.location_client.exceptions.ResourceNotFoundException:
                logger.info(f"{resource_type} {resource_name} not found (already deleted)")
            except Exception as e:
                cleanup_results['success'] = False
                cleanup_results['errors'].append(f"Failed to delete {resource_type} {resource_name}: {str(e)}")
                logger.error(f"Error deleting {resource_type} {resource_name}: {str(e)}")
        
        return cleanup_results


def main():
    """Main function to set up AWS Location Service resources"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize setup
    location_setup = LocationServiceSetup()
    
    print("Setting up AWS Location Service resources for AquaChain...")
    
    # Set up all resources
    results = location_setup.setup_all_resources()
    
    if results['success']:
        print("✅ All AWS Location Service resources created successfully!")
        
        # Print resource details
        for resource_type, resource_info in results['resources'].items():
            if resource_info['success']:
                status = resource_info['status']
                name = resource_info.get('map_name') or resource_info.get('calculator_name') or \
                       resource_info.get('index_name') or resource_info.get('collection_name')
                print(f"  - {resource_type}: {name} ({status})")
        
        # Test the setup
        print("\nTesting AWS Location Service setup...")
        test_results = location_setup.test_location_services()
        
        if test_results['success']:
            print("✅ All tests passed!")
            for test_name, test_info in test_results['tests'].items():
                if test_info['success']:
                    print(f"  - {test_name}: ✅")
                else:
                    print(f"  - {test_name}: ❌ {test_info['error']}")
        else:
            print("❌ Some tests failed:")
            for error in test_results['errors']:
                print(f"  - {error}")
        
        # Print IAM policy
        policy_info = location_setup.create_iam_policy()
        print(f"\nIAM Policy for Lambda functions:")
        print(json.dumps(policy_info['policy_document'], indent=2))
        
    else:
        print("❌ Failed to set up some resources:")
        for error in results['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    main()