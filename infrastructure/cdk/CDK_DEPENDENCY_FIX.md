# CDK Cyclic Dependency Resolution Guide

## Problem

The API and Monitoring stacks were disabled due to cyclic dependencies with WebSocketAPI. This prevented complete infrastructure deployment.

## Root Cause

**Cyclic Reference Chain:**
```
ComputeStack → APIStack → WebSocketAPI → Lambda Functions → ComputeStack
```

The issue occurred because:
1. ComputeStack creates Lambda functions
2. APIStack needs Lambda function ARNs for integration
3. WebSocketAPI (in APIStack) needs to invoke Lambda functions
4. Lambda functions need API Gateway endpoints (circular!)

## Solution

### 1. Use CloudFormation Exports

Instead of passing direct references, use CloudFormation exports:

```python
# In ComputeStack
from aws_cdk import CfnOutput

CfnOutput(
    self, "DataProcessingFunctionArn",
    value=self.data_processing_function.function_arn,
    export_name=f"AquaChain-{env_name}-DataProcessingFunctionArn"
)

# In APIStack
from aws_cdk import Fn

function_arn = Fn.import_value(f"AquaChain-{env_name}-DataProcessingFunctionArn")
```

### 2. Separate WebSocket Stack

Create a dedicated WebSocketStack that depends on both Compute and API:

```python
# New file: stacks/websocket_stack.py
class AquaChainWebSocketStack(Stack):
    def __init__(self, scope, id, config, compute_resources, api_resources, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # WebSocket API implementation
        # Uses exports from both stacks
```

### 3. Use SSM Parameters for Dynamic References

```python
# In ComputeStack - Store function ARN
from aws_cdk import aws_ssm as ssm

ssm.StringParameter(
    self, "DataProcessingFunctionArnParam",
    parameter_name=f"/aquachain/{env_name}/lambda/data-processing-arn",
    string_value=self.data_processing_function.function_arn
)

# In APIStack - Retrieve function ARN
function_arn = ssm.StringParameter.value_from_lookup(
    self,
    parameter_name=f"/aquachain/{env_name}/lambda/data-processing-arn"
)
```

## Implementation Steps

### Step 1: Update ComputeStack

```python
# infrastructure/cdk/stacks/compute_stack.py

class AquaChainComputeStack(Stack):
    def __init__(self, scope, construct_id, config, data_resources, security_resources, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Create Lambda functions
        self.data_processing_function = self._create_data_processing_function()
        
        # Export function ARNs
        CfnOutput(
            self, "DataProcessingFunctionArn",
            value=self.data_processing_function.function_arn,
            export_name=f"{Stack.of(self).stack_name}-DataProcessingFunctionArn"
        )
        
        CfnOutput(
            self, "DataProcessingFunctionName",
            value=self.data_processing_function.function_name,
            export_name=f"{Stack.of(self).stack_name}-DataProcessingFunctionName"
        )
        
        # Store in compute_resources for backward compatibility
        self.compute_resources = {
            'data_processing_function': {
                'function_name': self.data_processing_function.function_name,
                'function_arn': self.data_processing_function.function_arn
            }
        }
```

### Step 2: Update APIStack

```python
# infrastructure/cdk/stacks/api_stack.py

class AquaChainApiStack(Stack):
    def __init__(self, scope, construct_id, config, compute_resources, security_resources, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Import Lambda function ARN from exports
        # Instead of direct reference, use the exported value
        data_processing_function_arn = compute_resources['data_processing_function']['function_arn']
        
        # Create API Gateway integration
        # This breaks the circular dependency
```

### Step 3: Create Separate WebSocket Stack

```python
# infrastructure/cdk/stacks/websocket_stack.py

from aws_cdk import (
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_lambda as _lambda,
    Fn
)

class AquaChainWebSocketStack(Stack):
    def __init__(self, scope, construct_id, config, env_name, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Import Lambda function ARN from exports
        connect_function_arn = Fn.import_value(
            f"AquaChain-Compute-{env_name}-ConnectFunctionArn"
        )
        
        # Create WebSocket API
        websocket_api = apigwv2.WebSocketApi(
            self, "WebSocketAPI",
            api_name=f"aquachain-websocket-{env_name}"
        )
        
        # Add routes using imported function ARNs
        # No circular dependency!
```

### Step 4: Update app.py

```python
# infrastructure/cdk/app.py

def main():
    app = App()
    env_name = app.node.try_get_context("environment") or "dev"
    config = get_environment_config(env_name)
    
    # 1. Security Stack
    security_stack = AquaChainSecurityStack(...)
    
    # 2. Core Stack
    core_stack = AquaChainCoreStack(...)
    
    # 3. Data Stack
    data_stack = AquaChainDataStack(...)
    data_stack.add_dependency(security_stack)
    
    # 4. Compute Stack (exports function ARNs)
    compute_stack = AquaChainComputeStack(...)
    compute_stack.add_dependency(data_stack)
    
    # 5. API Stack (uses exported ARNs)
    api_stack = AquaChainApiStack(...)
    api_stack.add_dependency(compute_stack)
    
    # 6. WebSocket Stack (separate, uses exports)
    websocket_stack = AquaChainWebSocketStack(
        app,
        f"AquaChain-WebSocket-{env_name}",
        config=config,
        env_name=env_name,
        env=aws_env
    )
    websocket_stack.add_dependency(compute_stack)
    websocket_stack.add_dependency(api_stack)
    
    # 7. Monitoring Stack
    monitoring_stack = AquaChainMonitoringStack(...)
    monitoring_stack.add_dependency(api_stack)
    monitoring_stack.add_dependency(websocket_stack)
    
    app.synth()
```

## Testing

### 1. Validate Stack Dependencies

```bash
# Check for circular dependencies
cdk synth --all

# Should output all stacks without errors
```

### 2. Deploy in Order

```bash
# Deploy stacks in dependency order
cdk deploy AquaChain-Security-dev
cdk deploy AquaChain-Core-dev
cdk deploy AquaChain-Data-dev
cdk deploy AquaChain-Compute-dev
cdk deploy AquaChain-API-dev
cdk deploy AquaChain-WebSocket-dev
cdk deploy AquaChain-Monitoring-dev

# Or deploy all at once (CDK handles order)
cdk deploy --all
```

### 3. Verify Exports

```bash
# List CloudFormation exports
aws cloudformation list-exports

# Should see exports like:
# - AquaChain-Compute-dev-DataProcessingFunctionArn
# - AquaChain-API-dev-RestApiId
# - AquaChain-WebSocket-dev-WebSocketApiId
```

## Best Practices

### 1. Use Exports for Cross-Stack References

```python
# Export
CfnOutput(
    self, "ResourceId",
    value=resource.id,
    export_name=f"{Stack.of(self).stack_name}-ResourceId"
)

# Import
resource_id = Fn.import_value(f"StackName-ResourceId")
```

### 2. Minimize Cross-Stack Dependencies

- Keep related resources in the same stack
- Use exports only when necessary
- Consider using SSM parameters for dynamic values

### 3. Document Dependencies

```python
# Add comments explaining dependencies
# This stack depends on:
# - Security Stack: KMS keys
# - Data Stack: DynamoDB tables
# Exports:
# - Lambda function ARNs
# - API Gateway endpoints
```

### 4. Use Stack Props for Configuration

```python
@dataclass
class ComputeStackProps:
    config: Dict[str, Any]
    data_table_name: str  # From Data Stack
    kms_key_arn: str      # From Security Stack
    
class AquaChainComputeStack(Stack):
    def __init__(self, scope, id, props: ComputeStackProps, **kwargs):
        super().__init__(scope, id, **kwargs)
        # Use props instead of direct references
```

## Troubleshooting

### Error: "Circular dependency between resources"

**Solution:** Use CloudFormation exports or SSM parameters

### Error: "Export already exists"

**Solution:** Delete the stack and redeploy, or use unique export names

### Error: "Cannot import value from deleted stack"

**Solution:** Deploy the source stack first, then the dependent stack

## Verification Checklist

- [ ] All stacks synthesize without errors
- [ ] No circular dependencies detected
- [ ] Exports are properly named and unique
- [ ] Dependent stacks can import values
- [ ] Deployment order is documented
- [ ] Stack deletion order is documented (reverse of deployment)

## Additional Resources

- [AWS CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)
- [CloudFormation Exports](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-exports.html)
- [CDK Cross-Stack References](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib-readme.html#cross-stack-references)
