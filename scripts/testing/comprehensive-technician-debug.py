#!/usr/bin/env python3
"""
Comprehensive Technician Dashboard Debug

This script thoroughly investigates all potential issues:
1. Lambda function code analysis
2. Variable mismatches
3. Database queries
4. API Gateway configuration
5. Authentication flow
"""

import boto3
import json
from datetime import datetime

def check_lambda_function_code():
    """Check the actual Lambda function code to see what it's doing"""
    try:
        lambda_client = boto3.client('lambda')
        
        print("🔍 Checking Lambda function code...")
        
        # Get the function code
        response = lambda_client.get_function(
            FunctionName='aquachain-function-technician-tasks-dev'
        )
        
        print(f"✅ Lambda function details:")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Handler: {response['Configuration']['Handler']}")
        print(f"   Last Modified: {response['Configuration']['LastModified']}")
        print(f"   Code Size: {response['Configuration']['CodeSize']} bytes")
        
        # Check environment variables
        env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})
        print(f"   Environment Variables: {len(env_vars)} variables")
        for key, value in env_vars.items():
            if 'TABLE' in key or 'POOL' in key or 'REGION' in key:
                print(f"     {key}: {value}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error checking Lambda function: {e}")
        return None

def check_all_lambda_functions_with_technician():
    """Check all Lambda functions that might handle technician tasks"""
    try:
        lambda_client = boto3.client('lambda')
        
        print("🔍 Checking all technician-related Lambda functions...")
        
        # List all functions
        response = lambda_client.list_functions()
        
        technician_functions = []
        for func in response['Functions']:
            if 'technician' in func['FunctionName'].lower():
                technician_functions.append(func)
        
        print(f"✅ Found {len(technician_functions)} technician-related functions:")
        for func in technician_functions:
            print(f"   📋 {func['FunctionName']}")
            print(f"      Handler: {func['Handler']}")
            print(f"      Runtime: {func['Runtime']}")
            print(f"      Last Modified: {func['LastModified']}")
            print()
        
        return technician_functions
        
    except Exception as e:
        print(f"❌ Error listing Lambda functions: {e}")
        return []

def check_api_gateway_detailed():
    """Check API Gateway configuration in detail"""
    try:
        apigateway = boto3.client('apigateway')
        
        rest_api_id = 'vtqjfznspc'
        
        print("🔍 Checking API Gateway configuration...")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=rest_api_id)
        
        technician_resources = []
        for resource in resources['items']:
            if 'technician' in resource.get('pathPart', '').lower() or 'technician' in resource.get('path', '').lower():
                technician_resources.append(resource)
        
        print(f"✅ Found {len(technician_resources)} technician-related resources:")
        
        for resource in technician_resources:
            print(f"   📋 Path: {resource.get('path', 'N/A')}")
            print(f"      Resource ID: {resource['id']}")
            
            # Check methods for this resource
            if 'resourceMethods' in resource:
                for method in resource['resourceMethods']:
                    try:
                        method_details = apigateway.get_method(
                            restApiId=rest_api_id,
                            resourceId=resource['id'],
                            httpMethod=method
                        )
                        
                        print(f"      Method: {method}")
                        
                        # Check integration
                        try:
                            integration = apigateway.get_integration(
                                restApiId=rest_api_id,
                                resourceId=resource['id'],
                                httpMethod=method
                            )
                            
                            print(f"        Integration URI: {integration.get('uri', 'N/A')}")
                            print(f"        Integration Type: {integration.get('type', 'N/A')}")
                            
                        except Exception as e:
                            print(f"        Integration Error: {e}")
                            
                    except Exception as e:
                        print(f"      Method Error: {e}")
            print()
        
        return technician_resources
        
    except Exception as e:
        print(f"❌ Error checking API Gateway: {e}")
        return []

def test_direct_database_queries():
    """Test direct database queries to see what data exists"""
    try:
        dynamodb = boto3.resource('dynamodb')
        
        print("🔍 Testing direct database queries...")
        
        # Check service requests table
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        print("📋 Service Requests Table:")
        response = service_requests_table.scan(Limit=10)
        items = response.get('Items', [])
        
        print(f"   Total items scanned: {len(items)}")
        
        for item in items:
            print(f"   📄 Request ID: {item.get('requestId', 'N/A')}")
            print(f"      Status: {item.get('status', 'N/A')}")
            print(f"      Technician ID: {item.get('technicianId', 'N/A')}")
            print(f"      Description: {item.get('description', 'N/A')}")
            print()
        
        # Check users table
        users_table = dynamodb.Table('AquaChain-Users')
        
        print("📋 Users Table (Technicians only):")
        response = users_table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        
        technicians = response.get('Items', [])
        print(f"   Total technicians: {len(technicians)}")
        
        for tech in technicians:
            print(f"   👤 User ID: {tech.get('userId', 'N/A')}")
            print(f"      Name: {tech.get('profile', {}).get('firstName', 'N/A')} {tech.get('profile', {}).get('lastName', 'N/A')}")
            print(f"      Email: {tech.get('email', 'N/A')}")
            print(f"      Verified: {tech.get('verified', 'N/A')}")
            print(f"      Active: {tech.get('active', 'N/A')}")
            print()
        
        return {'service_requests': items, 'technicians': technicians}
        
    except Exception as e:
        print(f"❌ Error testing database queries: {e}")
        return {}

def check_lambda_logs():
    """Check recent Lambda function logs"""
    try:
        logs_client = boto3.client('logs')
        
        log_group = '/aws/lambda/aquachain-function-technician-tasks-dev'
        
        print("🔍 Checking Lambda function logs...")
        
        # Get recent log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        log_streams = response.get('logStreams', [])
        print(f"✅ Found {len(log_streams)} recent log streams")
        
        for stream in log_streams:
            print(f"   📋 Stream: {stream['logStreamName']}")
            print(f"      Last Event: {datetime.fromtimestamp(stream['lastEventTime']/1000)}")
            
            # Get recent events from this stream
            try:
                events_response = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream['logStreamName'],
                    limit=10,
                    startFromHead=False
                )
                
                events = events_response.get('events', [])
                print(f"      Recent events: {len(events)}")
                
                for event in events[-3:]:  # Last 3 events
                    timestamp = datetime.fromtimestamp(event['timestamp']/1000)
                    print(f"        {timestamp}: {event['message'][:100]}...")
                
            except Exception as e:
                print(f"      Error getting events: {e}")
            
            print()
        
        return log_streams
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")
        return []

def main():
    """Main debugging function"""
    print("🚀 Comprehensive Technician Dashboard Debug")
    print("=" * 70)
    
    # Step 1: Check Lambda function code
    print("\n1. LAMBDA FUNCTION CODE ANALYSIS")
    print("-" * 40)
    lambda_details = check_lambda_function_code()
    
    # Step 2: Check all technician-related functions
    print("\n2. ALL TECHNICIAN LAMBDA FUNCTIONS")
    print("-" * 40)
    all_functions = check_all_lambda_functions_with_technician()
    
    # Step 3: Check API Gateway configuration
    print("\n3. API GATEWAY CONFIGURATION")
    print("-" * 40)
    api_resources = check_api_gateway_detailed()
    
    # Step 4: Test database queries
    print("\n4. DATABASE QUERIES")
    print("-" * 40)
    db_data = test_direct_database_queries()
    
    # Step 5: Check Lambda logs
    print("\n5. LAMBDA FUNCTION LOGS")
    print("-" * 40)
    log_streams = check_lambda_logs()
    
    # Analysis
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE ANALYSIS")
    print("=" * 70)
    
    print("\n🔍 POTENTIAL ISSUES FOUND:")
    
    # Check if the right Lambda function exists
    if lambda_details:
        print("✅ Main Lambda function exists and is accessible")
    else:
        print("❌ Main Lambda function has issues")
    
    # Check if there are multiple technician functions
    if len(all_functions) > 1:
        print(f"⚠️  Multiple technician Lambda functions found ({len(all_functions)})")
        print("   This could cause routing confusion")
    
    # Check if API Gateway is configured correctly
    if len(api_resources) > 0:
        print("✅ API Gateway has technician resources")
    else:
        print("❌ No technician resources found in API Gateway")
    
    # Check database data
    service_requests = db_data.get('service_requests', [])
    technicians = db_data.get('technicians', [])
    
    if len(service_requests) > 0:
        print(f"✅ Service requests exist in database ({len(service_requests)})")
    else:
        print("❌ No service requests found in database")
    
    if len(technicians) > 0:
        print(f"✅ Technicians exist in database ({len(technicians)})")
    else:
        print("❌ No technicians found in database")
    
    # Check logs
    if len(log_streams) > 0:
        print("✅ Lambda function has recent activity")
    else:
        print("❌ Lambda function has no recent activity")
    
    print("\n🎯 RECOMMENDATIONS:")
    print("1. If multiple Lambda functions exist, verify API Gateway routes to correct one")
    print("2. Check if Lambda function is actually being invoked when API is called")
    print("3. Verify database table names and query patterns in Lambda code")
    print("4. Test authentication flow end-to-end")
    print("5. Consider cleaning up and recreating assignments for fresh start")

if __name__ == "__main__":
    main()