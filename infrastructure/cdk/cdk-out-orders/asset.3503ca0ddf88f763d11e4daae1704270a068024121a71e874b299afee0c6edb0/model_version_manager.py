"""
ML Model Version Manager
Handles model versioning, A/B testing, and rollback capabilities
"""

import json
import boto3
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import hashlib
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class ModelMetadata:
    """Model metadata structure"""
    model_name: str
    version: str
    s3_path: str
    created_at: str
    metrics: Dict[str, float]
    status: str  # 'active', 'testing', 'deprecated', 'archived'
    traffic_percentage: float  # For A/B testing
    checksum: str
    description: str = ""


class ModelVersionManager:
    """
    Manages ML model versions with A/B testing and rollback support
    """
    
    def __init__(self, s3_bucket: str, dynamodb_table: str, region: str = 'us-east-1'):
        """
        Initialize model version manager
        
        Args:
            s3_bucket: S3 bucket for model storage
            dynamodb_table: DynamoDB table for model registry
            region: AWS region
        """
        self.s3_bucket = s3_bucket
        self.dynamodb_table = dynamodb_table
        self.region = region
        
        self.s3_client = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(dynamodb_table)
        
        # Local model cache
        self.model_cache: Dict[str, Tuple[Any, ModelMetadata]] = {}
        self.cache_ttl = timedelta(hours=1)
        self.cache_timestamps: Dict[str, datetime] = {}
    
    def register_model(
        self,
        model_name: str,
        version: str,
        model_object: Any,
        metrics: Dict[str, float],
        description: str = "",
        traffic_percentage: float = 0.0
    ) -> ModelMetadata:
        """
        Register a new model version
        
        Args:
            model_name: Name of the model
            version: Version string (e.g., 'v1.0.0')
            model_object: Trained model object
            metrics: Model performance metrics
            description: Model description
            traffic_percentage: Initial traffic percentage for A/B testing
            
        Returns:
            ModelMetadata object
        """
        # Serialize model
        model_bytes = pickle.dumps(model_object)
        checksum = hashlib.sha256(model_bytes).hexdigest()
        
        # Upload to S3
        s3_path = f"ml-models/{model_name}/{version}/model.pkl"
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_path,
            Body=model_bytes,
            Metadata={
                'model_name': model_name,
                'version': version,
                'checksum': checksum,
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        # Create metadata
        metadata = ModelMetadata(
            model_name=model_name,
            version=version,
            s3_path=s3_path,
            created_at=datetime.utcnow().isoformat(),
            metrics=metrics,
            status='testing',
            traffic_percentage=traffic_percentage,
            checksum=checksum,
            description=description
        )
        
        # Store in DynamoDB
        self.table.put_item(Item={
            'model_name': model_name,
            'version': version,
            **asdict(metadata)
        })
        
        logger.info(f"Registered model {model_name} version {version}")
        return metadata
    
    def load_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        use_cache: bool = True
    ) -> Tuple[Any, ModelMetadata]:
        """
        Load a specific model version
        
        Args:
            model_name: Name of the model
            version: Version to load (None for latest active)
            use_cache: Whether to use cached model
            
        Returns:
            Tuple of (model_object, metadata)
        """
        # Determine version to load
        if version is None:
            version = self.get_active_version(model_name)
        
        cache_key = f"{model_name}:{version}"
        
        # Check cache
        if use_cache and cache_key in self.model_cache:
            cache_time = self.cache_timestamps.get(cache_key)
            if cache_time and datetime.utcnow() - cache_time < self.cache_ttl:
                logger.info(f"Loading model {cache_key} from cache")
                return self.model_cache[cache_key]
        
        # Load metadata from DynamoDB
        response = self.table.get_item(
            Key={
                'model_name': model_name,
                'version': version
            }
        )
        
        if 'Item' not in response:
            raise ValueError(f"Model {model_name} version {version} not found")
        
        item = response['Item']
        metadata = ModelMetadata(**{k: v for k, v in item.items() if k in ModelMetadata.__annotations__})
        
        # Load model from S3
        response = self.s3_client.get_object(
            Bucket=self.s3_bucket,
            Key=metadata.s3_path
        )
        
        model_bytes = response['Body'].read()
        
        # Verify checksum
        checksum = hashlib.sha256(model_bytes).hexdigest()
        if checksum != metadata.checksum:
            raise ValueError(f"Model checksum mismatch for {model_name}:{version}")
        
        # Deserialize model
        model_object = pickle.loads(model_bytes)
        
        # Update cache
        self.model_cache[cache_key] = (model_object, metadata)
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        logger.info(f"Loaded model {cache_key} from S3")
        return model_object, metadata
    
    def get_active_version(self, model_name: str) -> str:
        """
        Get the currently active version for a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Version string
        """
        response = self.table.query(
            KeyConditionExpression='model_name = :name',
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':name': model_name,
                ':status': 'active'
            },
            ScanIndexForward=False,  # Latest first
            Limit=1
        )
        
        if not response['Items']:
            raise ValueError(f"No active version found for model {model_name}")
        
        return response['Items'][0]['version']
    
    def set_model_status(
        self,
        model_name: str,
        version: str,
        status: str,
        traffic_percentage: Optional[float] = None
    ):
        """
        Update model status and traffic allocation
        
        Args:
            model_name: Name of the model
            version: Version string
            status: New status ('active', 'testing', 'deprecated', 'archived')
            traffic_percentage: Traffic percentage for A/B testing
        """
        update_expression = "SET #status = :status"
        expression_values = {':status': status}
        expression_names = {'#status': 'status'}
        
        if traffic_percentage is not None:
            update_expression += ", traffic_percentage = :traffic"
            expression_values[':traffic'] = traffic_percentage
        
        self.table.update_item(
            Key={
                'model_name': model_name,
                'version': version
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values
        )
        
        # Invalidate cache
        cache_key = f"{model_name}:{version}"
        if cache_key in self.model_cache:
            del self.model_cache[cache_key]
            del self.cache_timestamps[cache_key]
        
        logger.info(f"Updated model {model_name}:{version} status to {status}")
    
    def promote_to_active(self, model_name: str, version: str):
        """
        Promote a model version to active (100% traffic)
        
        Args:
            model_name: Name of the model
            version: Version to promote
        """
        # Get current active version
        try:
            current_active = self.get_active_version(model_name)
            # Deprecate current active
            self.set_model_status(model_name, current_active, 'deprecated', 0.0)
        except ValueError:
            # No current active version
            pass
        
        # Promote new version
        self.set_model_status(model_name, version, 'active', 100.0)
        logger.info(f"Promoted {model_name}:{version} to active")
    
    def rollback_to_version(self, model_name: str, version: str):
        """
        Rollback to a previous model version
        
        Args:
            model_name: Name of the model
            version: Version to rollback to
        """
        # Verify version exists and is not archived
        _, metadata = self.load_model(model_name, version, use_cache=False)
        
        if metadata.status == 'archived':
            raise ValueError(f"Cannot rollback to archived version {version}")
        
        # Promote to active
        self.promote_to_active(model_name, version)
        logger.info(f"Rolled back {model_name} to version {version}")
    
    def setup_ab_test(
        self,
        model_name: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5
    ):
        """
        Setup A/B test between two model versions
        
        Args:
            model_name: Name of the model
            version_a: First version (gets traffic_split percentage)
            version_b: Second version (gets 1-traffic_split percentage)
            traffic_split: Percentage of traffic for version_a (0.0 to 1.0)
        """
        if not 0.0 <= traffic_split <= 1.0:
            raise ValueError("traffic_split must be between 0.0 and 1.0")
        
        # Set both versions to testing status
        self.set_model_status(
            model_name, version_a, 'testing',
            traffic_percentage=traffic_split * 100
        )
        self.set_model_status(
            model_name, version_b, 'testing',
            traffic_percentage=(1 - traffic_split) * 100
        )
        
        logger.info(
            f"Setup A/B test for {model_name}: "
            f"{version_a} ({traffic_split*100}%) vs {version_b} ({(1-traffic_split)*100}%)"
        )
    
    def get_model_for_request(
        self,
        model_name: str,
        request_id: str
    ) -> Tuple[Any, ModelMetadata]:
        """
        Get model for a request (handles A/B testing)
        
        Args:
            model_name: Name of the model
            request_id: Unique request identifier for consistent routing
            
        Returns:
            Tuple of (model_object, metadata)
        """
        # Get all testing and active versions
        response = self.table.query(
            KeyConditionExpression='model_name = :name',
            FilterExpression='#status IN (:active, :testing)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':name': model_name,
                ':active': 'active',
                ':testing': 'testing'
            }
        )
        
        versions = response['Items']
        
        if not versions:
            raise ValueError(f"No active or testing versions for model {model_name}")
        
        # If only one version, use it
        if len(versions) == 1:
            version = versions[0]['version']
            return self.load_model(model_name, version)
        
        # A/B testing: use consistent hashing for request routing
        request_hash = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
        random_value = (request_hash % 100) / 100.0  # 0.0 to 1.0
        
        # Sort versions by traffic percentage
        versions.sort(key=lambda x: x['traffic_percentage'], reverse=True)
        
        # Select version based on traffic allocation
        cumulative = 0.0
        for version_data in versions:
            cumulative += version_data['traffic_percentage'] / 100.0
            if random_value <= cumulative:
                version = version_data['version']
                return self.load_model(model_name, version)
        
        # Fallback to first version
        version = versions[0]['version']
        return self.load_model(model_name, version)
    
    def list_versions(
        self,
        model_name: str,
        status_filter: Optional[str] = None
    ) -> List[ModelMetadata]:
        """
        List all versions of a model
        
        Args:
            model_name: Name of the model
            status_filter: Optional status filter
            
        Returns:
            List of ModelMetadata objects
        """
        if status_filter:
            response = self.table.query(
                KeyConditionExpression='model_name = :name',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':name': model_name,
                    ':status': status_filter
                }
            )
        else:
            response = self.table.query(
                KeyConditionExpression='model_name = :name',
                ExpressionAttributeValues={':name': model_name}
            )
        
        versions = [
            ModelMetadata(**{k: v for k, v in item.items() if k in ModelMetadata.__annotations__})
            for item in response['Items']
        ]
        
        return versions
    
    def get_model_metrics(
        self,
        model_name: str,
        version: str
    ) -> Dict[str, float]:
        """
        Get performance metrics for a model version
        
        Args:
            model_name: Name of the model
            version: Version string
            
        Returns:
            Dictionary of metrics
        """
        response = self.table.get_item(
            Key={
                'model_name': model_name,
                'version': version
            }
        )
        
        if 'Item' not in response:
            raise ValueError(f"Model {model_name} version {version} not found")
        
        return response['Item'].get('metrics', {})
    
    def update_model_metrics(
        self,
        model_name: str,
        version: str,
        metrics: Dict[str, float]
    ):
        """
        Update performance metrics for a model version
        
        Args:
            model_name: Name of the model
            version: Version string
            metrics: Updated metrics dictionary
        """
        self.table.update_item(
            Key={
                'model_name': model_name,
                'version': version
            },
            UpdateExpression="SET metrics = :metrics",
            ExpressionAttributeValues={':metrics': metrics}
        )
        
        logger.info(f"Updated metrics for {model_name}:{version}")
