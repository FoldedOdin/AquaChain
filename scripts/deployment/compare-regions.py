#!/usr/bin/env python3

import boto3
import json
from datetime import datetime

def check_region_resources(region_name):
    """Check what resources exist in a specific region."""
    
    print(f"\n🌍 CHECKING REGION: {region_name}")
    print("=" * 50)
    
    resources = {
        'cognito_user_pools': [],
        'lambda_functions': [],
        'api_gateways': [],
        'dynamodb_tables': [],
        's3_buckets': [],
        'cloudformation_stacks': [],
        'iot_things': [],
        'sagemaker_endpoints': []
    }
    
    try:
        # Check Cognito User Pools
        cognito_client = boto3.client('cognito-idp', region_name=region_name)
        try:
            user_pools = cognito_client.list_user_pools(MaxResults=50)
            for pool in user_pools.get('UserPools', []):
                if 'aquachain' in pool['Name'].lower():
                    resources['cognito_user_pools'].append({
                        'id': pool['Id'],
                        'name': pool['Name'],
                        'creation_date': pool['CreationDate'].isoformat() if pool.get('CreationDate') else 'Unknown'
                    })
        except Exception as e:
            print(f"   ⚠️ Cognito error: {str(e)}")
        
        # Check Lambda Functions
        lambda_client = boto3.client('lambda', region_name=region_name)
        try:
            functions = lambda_client.list_functions()
            for func in functions.get('Functions', []):
                if 'aquachain' in func['FunctionName'].lower():
                    resources['lambda_functions'].append({
                        'name': func['FunctionName'],
                        'runtime': func['Runtime'],
                        'last_modified': func['LastModified']
                    })
        except Exception as e:
            print(f"   ⚠️ Lambda error: {str(e)}")
        
        # Check API Gateway
        apigateway_client = boto3.client('apigateway', region_name=region_name)
        try:
            apis = apigateway_client.get_rest_apis()
            for api in apis.get('items', []):
                if 'aquachain' in api['name'].lower():
                    resources['api_gateways'].append({
                        'id': api['id'],
                        'name': api['name'],
                        'creation_date': api['createdDate'].isoformat() if api.get('createdDate') else 'Unknown'
                    })
        except Exception as e:
            print(f"   ⚠️ API Gateway error: {str(e)}")
        
        # Check DynamoDB Tables
        dynamodb_client = boto3.client('dynamodb', region_name=region_name)
        try:
            tables = dynamodb_client.list_tables()
            for table_name in tables.get('TableNames', []):
                if 'aquachain' in table_name.lower():
                    try:
                        table_info = dynamodb_client.describe_table(TableName=table_name)
                        resources['dynamodb_tables'].append({
                            'name': table_name,
                            'status': table_info['Table']['TableStatus'],
                            'creation_date': table_info['Table']['CreationDateTime'].isoformat()
                        })
                    except:
                        resources['dynamodb_tables'].append({
                            'name': table_name,
                            'status': 'Unknown',
                            'creation_date': 'Unknown'
                        })
        except Exception as e:
            print(f"   ⚠️ DynamoDB error: {str(e)}")
        
        # Check CloudFormation Stacks
        cf_client = boto3.client('cloudformation', region_name=region_name)
        try:
            stacks = cf_client.list_stacks(StackStatusFilter=[
                'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'
            ])
            for stack in stacks.get('StackSummaries', []):
                if 'aquachain' in stack['StackName'].lower():
                    resources['cloudformation_stacks'].append({
                        'name': stack['StackName'],
                        'status': stack['StackStatus'],
                        'creation_time': stack['CreationTime'].isoformat()
                    })
        except Exception as e:
            print(f"   ⚠️ CloudFormation error: {str(e)}")
        
        # Check IoT Things (only if region supports IoT)
        try:
            iot_client = boto3.client('iot', region_name=region_name)
            things = iot_client.list_things()
            for thing in things.get('things', []):
                if 'aquachain' in thing['thingName'].lower():
                    resources['iot_things'].append({
                        'name': thing['thingName'],
                        'thing_type': thing.get('thingTypeName', 'None'),
                        'creation_date': thing.get('attributes', {}).get('creationDate', 'Unknown')
                    })
        except Exception as e:
            print(f"   ⚠️ IoT error: {str(e)}")
        
        # Check SageMaker Endpoints
        try:
            sagemaker_client = boto3.client('sagemaker', region_name=region_name)
            endpoints = sagemaker_client.list_endpoints()
            for endpoint in endpoints.get('Endpoints', []):
                if 'aquachain' in endpoint['EndpointName'].lower():
                    resources['sagemaker_endpoints'].append({
                        'name': endpoint['EndpointName'],
                        'status': endpoint['EndpointStatus'],
                        'creation_time': endpoint['CreationTime'].isoformat()
                    })
        except Exception as e:
            print(f"   ⚠️ SageMaker error: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error checking region {region_name}: {str(e)}")
        return None
    
    return resources

def print_resources(region_name, resources):
    """Print resources in a formatted way."""
    
    if not resources:
        print(f"❌ Could not check resources in {region_name}")
        return
    
    total_resources = sum(len(resource_list) for resource_list in resources.values())
    
    if total_resources == 0:
        print(f"📭 NO AQUACHAIN RESOURCES FOUND in {region_name}")
        return
    
    print(f"📊 FOUND {total_resources} AQUACHAIN RESOURCES in {region_name}:")
    
    # Cognito User Pools
    if resources['cognito_user_pools']:
        print(f"\n🔐 COGNITO USER POOLS ({len(resources['cognito_user_pools'])}):")
        for pool in resources['cognito_user_pools']:
            print(f"   • {pool['name']} ({pool['id']})")
            print(f"     Created: {pool['creation_date']}")
    
    # Lambda Functions
    if resources['lambda_functions']:
        print(f"\n⚡ LAMBDA FUNCTIONS ({len(resources['lambda_functions'])}):")
        for func in resources['lambda_functions'][:10]:  # Show first 10
            print(f"   • {func['name']} ({func['runtime']})")
        if len(resources['lambda_functions']) > 10:
            print(f"   ... and {len(resources['lambda_functions']) - 10} more")
    
    # API Gateways
    if resources['api_gateways']:
        print(f"\n🌐 API GATEWAYS ({len(resources['api_gateways'])}):")
        for api in resources['api_gateways']:
            print(f"   • {api['name']} ({api['id']})")
            print(f"     URL: https://{api['id']}.execute-api.{region_name}.amazonaws.com")
    
    # DynamoDB Tables
    if resources['dynamodb_tables']:
        print(f"\n🗄️ DYNAMODB TABLES ({len(resources['dynamodb_tables'])}):")
        for table in resources['dynamodb_tables']:
            print(f"   • {table['name']} ({table['status']})")
    
    # CloudFormation Stacks
    if resources['cloudformation_stacks']:
        print(f"\n📚 CLOUDFORMATION STACKS ({len(resources['cloudformation_stacks'])}):")
        for stack in resources['cloudformation_stacks']:
            print(f"   • {stack['name']} ({stack['status']})")
    
    # IoT Things
    if resources['iot_things']:
        print(f"\n🔌 IOT THINGS ({len(resources['iot_things'])}):")
        for thing in resources['iot_things']:
            print(f"   • {thing['name']} (Type: {thing['thing_type']})")
    
    # SageMaker Endpoints
    if resources['sagemaker_endpoints']:
        print(f"\n🤖 SAGEMAKER ENDPOINTS ({len(resources['sagemaker_endpoints'])}):")
        for endpoint in resources['sagemaker_endpoints']:
            print(f"   • {endpoint['name']} ({endpoint['status']})")

def compare_regions():
    """Compare resources between ap-south-1 and us-east-1."""
    
    print("🔍 AQUACHAIN MULTI-REGION DEPLOYMENT COMPARISON")
    print("=" * 60)
    
    regions = ['ap-south-1', 'us-east-1']
    region_resources = {}
    
    # Check each region
    for region in regions:
        region_resources[region] = check_region_resources(region)
        print_resources(region, region_resources[region])
    
    # Compare regions
    print(f"\n📊 COMPARISON SUMMARY:")
    print("=" * 30)
    
    for region in regions:
        if region_resources[region]:
            total = sum(len(resource_list) for resource_list in region_resources[region].values())
            print(f"{region}: {total} AquaChain resources")
        else:
            print(f"{region}: Unable to check")
    
    # Detailed comparison
    if all(region_resources.values()):
        print(f"\n🔍 DETAILED COMPARISON:")
        
        resource_types = ['cognito_user_pools', 'lambda_functions', 'api_gateways', 'dynamodb_tables', 'cloudformation_stacks']
        
        for resource_type in resource_types:
            ap_south_count = len(region_resources['ap-south-1'].get(resource_type, []))
            us_east_count = len(region_resources['us-east-1'].get(resource_type, []))
            
            print(f"   {resource_type.replace('_', ' ').title()}:")
            print(f"     ap-south-1: {ap_south_count}")
            print(f"     us-east-1: {us_east_count}")
            
            if ap_south_count > 0 and us_east_count == 0:
                print(f"     ➡️ Only deployed in ap-south-1")
            elif ap_south_count == 0 and us_east_count > 0:
                print(f"     ➡️ Only deployed in us-east-1")
            elif ap_south_count > 0 and us_east_count > 0:
                print(f"     ➡️ Deployed in both regions")
            else:
                print(f"     ➡️ Not deployed in either region")
    
    return region_resources

if __name__ == "__main__":
    print("🚀 Starting multi-region comparison...")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    try:
        comparison_results = compare_regions()
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        ap_south_resources = comparison_results.get('ap-south-1', {})
        us_east_resources = comparison_results.get('us-east-1', {})
        
        if ap_south_resources and us_east_resources:
            ap_south_total = sum(len(resource_list) for resource_list in ap_south_resources.values())
            us_east_total = sum(len(resource_list) for resource_list in us_east_resources.values())
            
            if ap_south_total > 0 and us_east_total == 0:
                print("   • You have a full deployment in ap-south-1 only")
                print("   • us-east-1 is empty - no duplicate deployment costs")
                print("   • Stick with ap-south-1 unless you need multi-region")
            elif ap_south_total > 0 and us_east_total > 0:
                print("   • You have deployments in BOTH regions")
                print("   • This means ~2x AWS costs")
                print("   • Consider consolidating to one region if possible")
            elif ap_south_total == 0 and us_east_total > 0:
                print("   • You have deployment in us-east-1 only")
                print("   • ap-south-1 is empty")
            else:
                print("   • No AquaChain resources found in either region")
                print("   • May need to check resource naming or permissions")
        
    except Exception as e:
        print(f"❌ Error during comparison: {str(e)}")
        print("🔍 Check your AWS credentials and permissions")