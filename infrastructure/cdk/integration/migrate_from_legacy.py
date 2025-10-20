#!/usr/bin/env python3
"""
Migration script to transition from legacy infrastructure setup to CDK
"""

import boto3
import json
import sys
from typing import Dict, List, Any
from pathlib import Path

class LegacyToCDKMigrator:
    """
    Migrates existing infrastructure to CDK-managed resources
    """
    
    def __init__(self, environment: str, region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        
        # Initialize AWS clients
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
    def analyze_existing_resources(self) -> Dict[str, Any]:
        """
        Analyze existing resources that need to be migrated
        """
        print("Analyzing existing AquaChain resources...")
        
        analysis = {
            "dynamodb_tables": [],
            "s3_buckets": [],
            "lambda_functions": [],
            "iam_roles": [],
            "cloudformation_stacks": []
        }
        
        # Check for existing DynamoDB tables
        try:
            tables = self.dynamodb.list_tables()
            aquachain_tables = [
                table for table in tables['TableNames'] 
                if 'aquachain' in table.lower()
            ]
            analysis["dynamodb_tables"] = aquachain_tables
            print(f"Found {len(aquachain_tables)} AquaChain DynamoDB tables")
            
        except Exception as e:
            print(f"Error checking DynamoDB tables: {e}")
        
        # Check for existing S3 buckets
        try:
            buckets = self.s3.list_buckets()
            aquachain_buckets = [
                bucket['Name'] for bucket in buckets['Buckets']
                if 'aquachain' in bucket['Name'].lower()
            ]
            analysis["s3_buckets"] = aquachain_buckets
            print(f"Found {len(aquachain_buckets)} AquaChain S3 buckets")
            
        except Exception as e:
            print(f"Error checking S3 buckets: {e}")
        
        # Check for existing Lambda functions
        try:
            functions = self.lambda_client.list_functions()
            aquachain_functions = [
                func['FunctionName'] for func in functions['Functions']
                if 'aquachain' in func['FunctionName'].lower()
            ]
            analysis["lambda_functions"] = aquachain_functions
            print(f"Found {len(aquachain_functions)} AquaChain Lambda functions")
            
        except Exception as e:
            print(f"Error checking Lambda functions: {e}")
        
        # Check for existing CloudFormation stacks
        try:
            stacks = self.cloudformation.list_stacks(
                StackStatusFilter=[
                    'CREATE_COMPLETE',
                    'UPDATE_COMPLETE',
                    'UPDATE_ROLLBACK_COMPLETE'
                ]
            )
            aquachain_stacks = [
                stack['StackName'] for stack in stacks['StackSummaries']
                if 'aquachain' in stack['StackName'].lower()
            ]
            analysis["cloudformation_stacks"] = aquachain_stacks
            print(f"Found {len(aquachain_stacks)} AquaChain CloudFormation stacks")
            
        except Exception as e:
            print(f"Error checking CloudFormation stacks: {e}")
        
        return analysis
    
    def generate_migration_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a migration plan based on existing resources
        """
        print("\nGenerating migration plan...")
        
        migration_plan = {
            "phase_1_backup": {
                "description": "Backup existing resources",
                "actions": []
            },
            "phase_2_import": {
                "description": "Import resources into CDK stacks",
                "actions": []
            },
            "phase_3_validate": {
                "description": "Validate migrated resources",
                "actions": []
            },
            "phase_4_cleanup": {
                "description": "Clean up legacy resources",
                "actions": []
            }
        }
        
        # Phase 1: Backup
        if analysis["dynamodb_tables"]:
            migration_plan["phase_1_backup"]["actions"].append({
                "type": "dynamodb_backup",
                "resources": analysis["dynamodb_tables"],
                "command": "aws dynamodb create-backup --table-name {table} --backup-name {table}-migration-backup"
            })
        
        if analysis["s3_buckets"]:
            migration_plan["phase_1_backup"]["actions"].append({
                "type": "s3_backup",
                "resources": analysis["s3_buckets"],
                "command": "aws s3 sync s3://{bucket} s3://{bucket}-migration-backup"
            })
        
        # Phase 2: Import
        migration_plan["phase_2_import"]["actions"].append({
            "type": "cdk_import",
            "description": "Import existing resources into CDK stacks",
            "command": "cdk import AquaChain-Data-{env} --resource-mapping resource-mapping.json"
        })
        
        # Phase 3: Validate
        migration_plan["phase_3_validate"]["actions"].append({
            "type": "validation",
            "description": "Validate migrated infrastructure",
            "command": "python validation/validate_infrastructure.py --environment {env}"
        })
        
        # Phase 4: Cleanup
        if analysis["cloudformation_stacks"]:
            migration_plan["phase_4_cleanup"]["actions"].append({
                "type": "stack_cleanup",
                "resources": analysis["cloudformation_stacks"],
                "command": "aws cloudformation delete-stack --stack-name {stack}"
            })
        
        return migration_plan
    
    def create_resource_mapping(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create resource mapping file for CDK import
        """
        print("Creating resource mapping for CDK import...")
        
        resource_mapping = {}
        
        # Map DynamoDB tables
        for table in analysis["dynamodb_tables"]:
            if "readings" in table.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:ReadingsTable"] = {
                    "Type": "AWS::DynamoDB::Table",
                    "PhysicalResourceId": table
                }
            elif "ledger" in table.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:LedgerTable"] = {
                    "Type": "AWS::DynamoDB::Table", 
                    "PhysicalResourceId": table
                }
            elif "sequence" in table.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:SequenceTable"] = {
                    "Type": "AWS::DynamoDB::Table",
                    "PhysicalResourceId": table
                }
            elif "users" in table.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:UsersTable"] = {
                    "Type": "AWS::DynamoDB::Table",
                    "PhysicalResourceId": table
                }
            elif "service" in table.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:ServiceRequestsTable"] = {
                    "Type": "AWS::DynamoDB::Table",
                    "PhysicalResourceId": table
                }
        
        # Map S3 buckets
        for bucket in analysis["s3_buckets"]:
            if "data-lake" in bucket.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:DataLakeBucket"] = {
                    "Type": "AWS::S3::Bucket",
                    "PhysicalResourceId": bucket
                }
            elif "audit" in bucket.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:AuditBucket"] = {
                    "Type": "AWS::S3::Bucket",
                    "PhysicalResourceId": bucket
                }
            elif "ml-models" in bucket.lower():
                resource_mapping[f"AquaChain-Data-{self.environment.title()}:MLModelsBucket"] = {
                    "Type": "AWS::S3::Bucket",
                    "PhysicalResourceId": bucket
                }
        
        # Save resource mapping to file
        mapping_file = Path(f"resource-mapping-{self.environment}.json")
        with open(mapping_file, 'w') as f:
            json.dump(resource_mapping, f, indent=2)
        
        print(f"Resource mapping saved to: {mapping_file}")
        return resource_mapping
    
    def execute_migration(self, migration_plan: Dict[str, Any]) -> bool:
        """
        Execute the migration plan
        """
        print("\n" + "="*60)
        print("MIGRATION EXECUTION")
        print("="*60)
        
        print("\n⚠️  IMPORTANT: This migration will modify your AWS resources.")
        print("Make sure you have:")
        print("1. Backed up all critical data")
        print("2. Tested the migration in a non-production environment")
        print("3. Have the necessary AWS permissions")
        
        confirmation = input("\nDo you want to proceed with the migration? (yes/no): ")
        if confirmation.lower() != 'yes':
            print("Migration cancelled.")
            return False
        
        # Execute each phase
        for phase_name, phase_info in migration_plan.items():
            print(f"\n{phase_info['description']}:")
            print("-" * 40)
            
            for action in phase_info["actions"]:
                print(f"Action: {action['type']}")
                if 'command' in action:
                    command = action['command'].format(
                        env=self.environment,
                        table="{table}",
                        bucket="{bucket}",
                        stack="{stack}"
                    )
                    print(f"Command: {command}")
                
                # For this example, we'll just print the commands
                # In a real implementation, you would execute them
                print("✓ Action planned (manual execution required)")
        
        print(f"\n✓ Migration plan generated for environment: {self.environment}")
        print("\nNext steps:")
        print("1. Review the generated resource mapping file")
        print("2. Execute the backup commands manually")
        print("3. Run CDK import with the resource mapping")
        print("4. Validate the migrated infrastructure")
        print("5. Clean up legacy resources after validation")
        
        return True

def main():
    """
    Main migration script
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate legacy AquaChain infrastructure to CDK")
    parser.add_argument("--environment", "-e", required=True,
                       choices=["dev", "staging", "prod"],
                       help="Environment to migrate")
    parser.add_argument("--region", "-r", default="us-east-1",
                       help="AWS region")
    parser.add_argument("--analyze-only", action="store_true",
                       help="Only analyze existing resources, don't migrate")
    
    args = parser.parse_args()
    
    # Create migrator
    migrator = LegacyToCDKMigrator(args.environment, args.region)
    
    # Analyze existing resources
    analysis = migrator.analyze_existing_resources()
    
    # Save analysis results
    analysis_file = f"migration-analysis-{args.environment}.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"\nAnalysis results saved to: {analysis_file}")
    
    if args.analyze_only:
        print("Analysis complete. Use --analyze-only=false to proceed with migration.")
        return
    
    # Generate migration plan
    migration_plan = migrator.generate_migration_plan(analysis)
    
    # Create resource mapping
    resource_mapping = migrator.create_resource_mapping(analysis)
    
    # Save migration plan
    plan_file = f"migration-plan-{args.environment}.json"
    with open(plan_file, 'w') as f:
        json.dump(migration_plan, f, indent=2)
    print(f"Migration plan saved to: {plan_file}")
    
    # Execute migration
    success = migrator.execute_migration(migration_plan)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()