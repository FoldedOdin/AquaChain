"""
Performance Regression Detector for AquaChain
Detects performance regressions by comparing current metrics with baseline
"""

import json
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
import argparse
from dataclasses import dataclass, asdict
import boto3

@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison."""
    metric_name: str
    baseline_value: float
    baseline_timestamp: str
    measurement_period: str
    confidence_interval: Tuple[float, float]
    sample_size: int

@dataclass
class RegressionDetectionResult:
    """Result of regression detection."""
    metric_name: str
    current_value: float
    baseline_value: float
    change_percentage: float
    regression_detected: bool
    severity: str  # low, medium, high, critical
    confidence_level: float
    trend_direction: str  # improving, degrading, stable
    recommendation: str

@dataclass
class PerformanceRegressionReport:
    """Comprehensive performance regression report."""
    detection_run_id: str
    timestamp: str
    baseline_timestamp: str
    total_metrics: int
    regressions_detected: int
    critical_regressions: int
    overall_performance_change: float
    detection_results: List[RegressionDetectionResult]
    summary: Dict[str, Any]

class PerformanceRegressionDetector:
    """Detector for performance regressions in AquaChain system."""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        
        # Define performance metrics to monitor
        self.performance_metrics = [
            {
                'name': 'lambda_duration',
                'namespace': 'AWS/Lambda',
                'metric_name': 'Duration',
                'dimensions': [{'Name': 'FunctionName', 'Value': 'AquaChain-data-processing'}],
                'statistic': 'Average',
                'threshold_percentage': 20.0,  # 20% increase is concerning
                'critical_threshold': 50.0     # 50% increase is critical
            },
            {
                'name': 'api_response_time',
                'namespace': 'AWS/ApiGateway',
                'metric_name': 'Latency',
                'dimensions': [{'Name': 'ApiName', 'Value': 'AquaChain-API'}],
                'statistic': 'Average',
                'threshold_percentage': 15.0,
                'critical_threshold': 40.0
            },
            {
                'name': 'dynamodb_read_latency',
                'namespace': 'AWS/DynamoDB',
                'metric_name': 'SuccessfulRequestLatency',
                'dimensions': [
                    {'Name': 'TableName', 'Value': 'aquachain-readings'},
                    {'Name': 'Operation', 'Value': 'Query'}
                ],
                'statistic': 'Average',
                'threshold_percentage': 25.0,
                'critical_threshold': 60.0
            },
            {
                'name': 'dynamodb_write_latency',
                'namespace': 'AWS/DynamoDB',
                'metric_name': 'SuccessfulRequestLatency',
                'dimensions': [
                    {'Name': 'TableName', 'Value': 'aquachain-readings'},
                    {'Name': 'Operation', 'Value': 'PutItem'}
                ],
                'statistic': 'Average',
                'threshold_percentage': 25.0,
                'critical_threshold': 60.0
            },
            {
                'name': 'error_rate',
                'namespace': 'AWS/Lambda',
                'metric_name': 'Errors',
                'dimensions': [{'Name': 'FunctionName', 'Value': 'AquaChain-data-processing'}],
                'statistic': 'Sum',
                'threshold_percentage': 10.0,
                'critical_threshold': 50.0
            },
            {
                'name': 'throughput',
                'namespace': 'AWS/Lambda',
                'metric_name': 'Invocations',
                'dimensions': [{'Name': 'FunctionName', 'Value': 'AquaChain-data-processing'}],
                'statistic': 'Sum',
                'threshold_percentage': -10.0,  # Negative means decrease is concerning
                'critical_threshold': -30.0
            },
            {
                'name': 'memory_utilization',
                'namespace': 'AWS/Lambda',
                'metric_name': 'Duration',  # Proxy for memory usage
                'dimensions': [{'Name': 'FunctionName', 'Value': 'AquaChain-ml-inference'}],
                'statistic': 'Maximum',
                'threshold_percentage': 30.0,
                'critical_threshold': 70.0
            }
        ]
    
    def create_performance_baseline(self, days_back: int = 7) -> Dict[str, PerformanceBaseline]:
        """Create performance baseline from historical data."""
        print(f"📊 Creating performance baseline from {days_back} days of data...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        baselines = {}
        
        for metric_config in self.performance_metrics:
            try:
                print(f"  Processing {metric_config['name']}...")
                
                # Get historical data
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=metric_config['namespace'],
                    MetricName=metric_config['metric_name'],
                    Dimensions=metric_config['dimensions'],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=[metric_config['statistic']]
                )
                
                datapoints = response.get('Datapoints', [])
                
                if datapoints:
                    values = [dp[metric_config['statistic']] for dp in datapoints]
                    
                    # Calculate baseline statistics
                    baseline_value = statistics.mean(values)
                    std_dev = statistics.stdev(values) if len(values) > 1 else 0
                    
                    # Calculate confidence interval (95%)
                    confidence_margin = 1.96 * (std_dev / (len(values) ** 0.5))
                    confidence_interval = (
                        baseline_value - confidence_margin,
                        baseline_value + confidence_margin
                    )
                    
                    baseline = PerformanceBaseline(
                        metric_name=metric_config['name'],
                        baseline_value=baseline_value,
                        baseline_timestamp=end_time.isoformat(),
                        measurement_period=f"{days_back}d",
                        confidence_interval=confidence_interval,
                        sample_size=len(values)
                    )
                    
                    baselines[metric_config['name']] = baseline
                    
                    print(f"    ✅ Baseline: {baseline_value:.2f} ± {confidence_margin:.2f}")
                
                else:
                    print(f"    ⚠️  No data available for {metric_config['name']}")
                    
            except Exception as e:
                print(f"    ❌ Failed to create baseline for {metric_config['name']}: {e}")
        
        return baselines
    
    def save_baseline(self, baselines: Dict[str, PerformanceBaseline], filename: str):
        """Save performance baseline to file."""
        try:
            baseline_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'baselines': {name: asdict(baseline) for name, baseline in baselines.items()}
            }
            
            with open(filename, 'w') as f:
                json.dump(baseline_data, f, indent=2)
            
            print(f"📄 Baseline saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save baseline: {e}")
    
    def load_baseline(self, filename: str) -> Dict[str, PerformanceBaseline]:
        """Load performance baseline from file."""
        try:
            with open(filename, 'r') as f:
                baseline_data = json.load(f)
            
            baselines = {}
            for name, data in baseline_data['baselines'].items():
                baselines[name] = PerformanceBaseline(**data)
            
            print(f"📄 Baseline loaded from: {filename}")
            print(f"    Baseline timestamp: {baseline_data['timestamp']}")
            
            return baselines
            
        except Exception as e:
            print(f"❌ Failed to load baseline: {e}")
            return {}
    
    def get_current_metrics(self, hours_back: int = 1) -> Dict[str, float]:
        """Get current performance metrics."""
        print(f"📈 Getting current metrics from last {hours_back} hour(s)...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        current_metrics = {}
        
        for metric_config in self.performance_metrics:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=metric_config['namespace'],
                    MetricName=metric_config['metric_name'],
                    Dimensions=metric_config['dimensions'],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=[metric_config['statistic']]
                )
                
                datapoints = response.get('Datapoints', [])
                
                if datapoints:
                    values = [dp[metric_config['statistic']] for dp in datapoints]
                    current_value = statistics.mean(values)
                    current_metrics[metric_config['name']] = current_value
                    
                    print(f"  {metric_config['name']}: {current_value:.2f}")
                else:
                    print(f"  {metric_config['name']}: No data")
                    current_metrics[metric_config['name']] = 0.0
                    
            except Exception as e:
                print(f"  ❌ Failed to get {metric_config['name']}: {e}")
                current_metrics[metric_config['name']] = 0.0
        
        return current_metrics
    
    def detect_regressions(self, baselines: Dict[str, PerformanceBaseline], 
                          current_metrics: Dict[str, float]) -> List[RegressionDetectionResult]:
        """Detect performance regressions by comparing current metrics with baseline."""
        print("🔍 Detecting performance regressions...")
        
        detection_results = []
        
        for metric_name, baseline in baselines.items():
            if metric_name not in current_metrics:
                continue
            
            current_value = current_metrics[metric_name]
            baseline_value = baseline.baseline_value
            
            # Calculate change percentage
            if baseline_value != 0:
                change_percentage = ((current_value - baseline_value) / baseline_value) * 100
            else:
                change_percentage = 0.0
            
            # Get metric configuration
            metric_config = next((m for m in self.performance_metrics if m['name'] == metric_name), None)
            if not metric_config:
                continue
            
            # Determine if regression is detected
            threshold = metric_config['threshold_percentage']
            critical_threshold = metric_config['critical_threshold']
            
            # For metrics where decrease is bad (like throughput), flip the logic
            if threshold < 0:
                regression_detected = change_percentage < threshold
                severity = self._calculate_severity(change_percentage, threshold, critical_threshold, inverted=True)
            else:
                regression_detected = change_percentage > threshold
                severity = self._calculate_severity(change_percentage, threshold, critical_threshold)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(
                current_value, baseline.confidence_interval
            )
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(change_percentage)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(metric_name, change_percentage, severity)
            
            result = RegressionDetectionResult(
                metric_name=metric_name,
                current_value=current_value,
                baseline_value=baseline_value,
                change_percentage=change_percentage,
                regression_detected=regression_detected,
                severity=severity,
                confidence_level=confidence_level,
                trend_direction=trend_direction,
                recommendation=recommendation
            )
            
            detection_results.append(result)
            
            # Print result
            status = "🔴 REGRESSION" if regression_detected else "✅ OK"
            severity_icon = self._get_severity_icon(severity)
            print(f"  {status} {metric_name}: {change_percentage:+.1f}% {severity_icon}")
        
        return detection_results
    
    def _calculate_severity(self, change_percentage: float, threshold: float, 
                          critical_threshold: float, inverted: bool = False) -> str:
        """Calculate severity of performance change."""
        if inverted:
            # For metrics where decrease is bad
            if change_percentage <= critical_threshold:
                return "critical"
            elif change_percentage <= threshold:
                return "high"
            elif change_percentage <= threshold * 0.5:
                return "medium"
            else:
                return "low"
        else:
            # For metrics where increase is bad
            if change_percentage >= critical_threshold:
                return "critical"
            elif change_percentage >= threshold:
                return "high"
            elif change_percentage >= threshold * 0.5:
                return "medium"
            else:
                return "low"
    
    def _calculate_confidence_level(self, current_value: float, 
                                  confidence_interval: Tuple[float, float]) -> float:
        """Calculate confidence level for the measurement."""
        lower_bound, upper_bound = confidence_interval
        
        if lower_bound <= current_value <= upper_bound:
            return 95.0  # Within confidence interval
        else:
            # Calculate how far outside the interval
            if current_value < lower_bound:
                distance = lower_bound - current_value
                interval_width = upper_bound - lower_bound
            else:
                distance = current_value - upper_bound
                interval_width = upper_bound - lower_bound
            
            # Rough confidence calculation
            confidence = max(50.0, 95.0 - (distance / interval_width) * 20)
            return confidence
    
    def _determine_trend_direction(self, change_percentage: float) -> str:
        """Determine trend direction based on change percentage."""
        if change_percentage > 5:
            return "degrading"
        elif change_percentage < -5:
            return "improving"
        else:
            return "stable"
    
    def _generate_recommendation(self, metric_name: str, change_percentage: float, 
                               severity: str) -> str:
        """Generate recommendation based on regression detection."""
        if severity == "critical":
            if "latency" in metric_name or "duration" in metric_name:
                return f"CRITICAL: {metric_name} increased by {change_percentage:.1f}%. Immediate performance optimization required."
            elif "error" in metric_name:
                return f"CRITICAL: {metric_name} increased by {change_percentage:.1f}%. Investigate and fix errors immediately."
            elif "throughput" in metric_name:
                return f"CRITICAL: {metric_name} decreased by {abs(change_percentage):.1f}%. Scale up resources immediately."
        elif severity == "high":
            return f"HIGH: {metric_name} regression detected ({change_percentage:+.1f}%). Performance tuning recommended."
        elif severity == "medium":
            return f"MEDIUM: {metric_name} showing degradation ({change_percentage:+.1f}%). Monitor closely."
        else:
            return f"LOW: Minor change in {metric_name} ({change_percentage:+.1f}%). Continue monitoring."
    
    def _get_severity_icon(self, severity: str) -> str:
        """Get icon for severity level."""
        icons = {
            "critical": "🚨",
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        return icons.get(severity, "⚪")
    
    def run_regression_detection(self, baseline_file: str, 
                               create_new_baseline: bool = False) -> PerformanceRegressionReport:
        """Run complete regression detection process."""
        print("🔬 AquaChain Performance Regression Detection")
        print("=" * 60)
        
        detection_run_id = f"regression-detection-{int(time.time())}"
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Load or create baseline
        if create_new_baseline:
            print("Creating new performance baseline...")
            baselines = self.create_performance_baseline()
            self.save_baseline(baselines, baseline_file)
            baseline_timestamp = timestamp
        else:
            print("Loading existing performance baseline...")
            baselines = self.load_baseline(baseline_file)
            if not baselines:
                print("No baseline found, creating new one...")
                baselines = self.create_performance_baseline()
                self.save_baseline(baselines, baseline_file)
                baseline_timestamp = timestamp
            else:
                baseline_timestamp = baselines[list(baselines.keys())[0]].baseline_timestamp
        
        # Get current metrics
        current_metrics = self.get_current_metrics()
        
        # Detect regressions
        detection_results = self.detect_regressions(baselines, current_metrics)
        
        # Calculate summary statistics
        regressions_detected = sum(1 for result in detection_results if result.regression_detected)
        critical_regressions = sum(1 for result in detection_results 
                                 if result.regression_detected and result.severity == "critical")
        
        # Calculate overall performance change
        performance_changes = [result.change_percentage for result in detection_results 
                             if result.regression_detected]
        overall_performance_change = statistics.mean(performance_changes) if performance_changes else 0.0
        
        # Generate summary
        summary = {
            "detection_timestamp": timestamp,
            "baseline_age_hours": self._calculate_baseline_age(baseline_timestamp),
            "regression_rate": (regressions_detected / len(detection_results)) * 100 if detection_results else 0,
            "critical_regression_rate": (critical_regressions / len(detection_results)) * 100 if detection_results else 0,
            "most_degraded_metric": max(detection_results, key=lambda r: r.change_percentage).metric_name if detection_results else None,
            "most_improved_metric": min(detection_results, key=lambda r: r.change_percentage).metric_name if detection_results else None,
            "recommendations": [result.recommendation for result in detection_results 
                              if result.regression_detected and result.severity in ["critical", "high"]]
        }
        
        return PerformanceRegressionReport(
            detection_run_id=detection_run_id,
            timestamp=timestamp,
            baseline_timestamp=baseline_timestamp,
            total_metrics=len(detection_results),
            regressions_detected=regressions_detected,
            critical_regressions=critical_regressions,
            overall_performance_change=overall_performance_change,
            detection_results=detection_results,
            summary=summary
        )
    
    def _calculate_baseline_age(self, baseline_timestamp: str) -> float:
        """Calculate age of baseline in hours."""
        try:
            baseline_time = datetime.fromisoformat(baseline_timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            age = (current_time - baseline_time).total_seconds() / 3600
            return age
        except Exception:
            return 0.0
    
    def print_regression_report(self, report: PerformanceRegressionReport):
        """Print formatted performance regression report."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE REGRESSION REPORT")
        print("=" * 60)
        print(f"Detection Run ID: {report.detection_run_id}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Baseline Age: {report.summary['baseline_age_hours']:.1f} hours")
        print(f"Total Metrics: {report.total_metrics}")
        print(f"Regressions Detected: {report.regressions_detected}")
        print(f"Critical Regressions: {report.critical_regressions}")
        print(f"Regression Rate: {report.summary['regression_rate']:.1f}%")
        print(f"Overall Performance Change: {report.overall_performance_change:+.1f}%")
        
        print("\n📋 Detailed Results:")
        print("-" * 60)
        for result in report.detection_results:
            status = "🔴 REGRESSION" if result.regression_detected else "✅ OK"
            severity_icon = self._get_severity_icon(result.severity)
            trend_icon = "📈" if result.trend_direction == "improving" else "📉" if result.trend_direction == "degrading" else "➡️"
            
            print(f"{status} {result.metric_name} {severity_icon}")
            print(f"    Current: {result.current_value:.2f} | Baseline: {result.baseline_value:.2f}")
            print(f"    Change: {result.change_percentage:+.1f}% | Confidence: {result.confidence_level:.1f}%")
            print(f"    Trend: {trend_icon} {result.trend_direction.title()}")
            
            if result.regression_detected:
                print(f"    Severity: {result.severity.upper()}")
        
        print("\n🔧 Priority Recommendations:")
        print("-" * 60)
        priority_recommendations = [rec for rec in report.summary['recommendations']]
        for i, recommendation in enumerate(priority_recommendations[:5], 1):  # Top 5
            print(f"{i}. {recommendation}")
        
        if report.summary['most_degraded_metric']:
            print(f"\n📉 Most Degraded: {report.summary['most_degraded_metric']}")
        
        if report.summary['most_improved_metric']:
            print(f"📈 Most Improved: {report.summary['most_improved_metric']}")
        
        # Overall assessment
        print("\n🏆 OVERALL ASSESSMENT:")
        print("=" * 60)
        if report.critical_regressions == 0 and report.regressions_detected == 0:
            print("✅ NO PERFORMANCE REGRESSIONS DETECTED")
            print("   System performance is stable or improving")
        elif report.critical_regressions == 0:
            print("⚠️  MINOR PERFORMANCE REGRESSIONS DETECTED")
            print(f"   {report.regressions_detected} non-critical regression(s) found")
            print("   Monitor closely and consider optimization")
        else:
            print("🚨 CRITICAL PERFORMANCE REGRESSIONS DETECTED")
            print(f"   {report.critical_regressions} critical regression(s) require immediate attention")
            print("   Performance optimization required before production deployment")

def main():
    """Main function to run performance regression detection."""
    parser = argparse.ArgumentParser(description='AquaChain Performance Regression Detector')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--baseline-file', type=str, default='performance_baseline.json', 
                       help='Baseline file path (default: performance_baseline.json)')
    parser.add_argument('--create-baseline', action='store_true', 
                       help='Create new performance baseline')
    parser.add_argument('--output', type=str, 
                       help='Output report file (JSON format)')
    parser.add_argument('--hours-back', type=int, default=1, 
                       help='Hours of current data to analyze (default: 1)')
    
    args = parser.parse_args()
    
    try:
        detector = PerformanceRegressionDetector(aws_region=args.aws_region)
        
        print("🔬 AquaChain Performance Regression Detector")
        print("=" * 50)
        
        # Run regression detection
        report = detector.run_regression_detection(
            baseline_file=args.baseline_file,
            create_new_baseline=args.create_baseline
        )
        
        # Print report
        detector.print_regression_report(report)
        
        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
            print(f"\n📄 Report saved to: {args.output}")
        
        # Return appropriate exit code
        return 0 if report.critical_regressions == 0 else 1
        
    except Exception as e:
        print(f"💥 Performance regression detection failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())