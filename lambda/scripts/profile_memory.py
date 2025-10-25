"""
Lambda Memory Profiling Script

This script analyzes CloudWatch metrics to determine optimal memory allocation
for Lambda functions based on actual usage patterns.
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics


class LambdaMemoryProfiler:
    """Profile Lambda function memory usage and recommend optimal settings"""

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize profiler

        Args:
            region: AWS region
        """
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.lambda_client = boto3.client("lambda", region_name=region)
        self.region = region

    def get_function_metrics(
        self, function_name: str, days: int = 7
    ) -> Dict[str, List[float]]:
        """
        Get CloudWatch metrics for a Lambda function

        Args:
            function_name: Name of the Lambda function
            days: Number of days to analyze

        Returns:
            Dictionary of metric names to values
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        metrics = {}

        # Get duration metrics
        duration_response = self.cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Duration",
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=["Average", "Maximum", "Minimum"],
        )

        metrics["duration"] = [
            dp["Average"] for dp in duration_response["Datapoints"]
        ]
        metrics["duration_max"] = [
            dp["Maximum"] for dp in duration_response["Datapoints"]
        ]

        # Get invocation count
        invocations_response = self.cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Invocations",
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Sum"],
        )

        metrics["invocations"] = [
            dp["Sum"] for dp in invocations_response["Datapoints"]
        ]

        # Get error count
        errors_response = self.cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Errors",
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Sum"],
        )

        metrics["errors"] = [dp["Sum"] for dp in errors_response["Datapoints"]]

        return metrics

    def get_current_config(self, function_name: str) -> Dict:
        """
        Get current Lambda function configuration

        Args:
            function_name: Name of the Lambda function

        Returns:
            Function configuration
        """
        response = self.lambda_client.get_function_configuration(
            FunctionName=function_name
        )

        return {
            "memory_size": response["MemorySize"],
            "timeout": response["Timeout"],
            "runtime": response["Runtime"],
        }

    def calculate_optimal_memory(
        self, function_name: str, metrics: Dict[str, List[float]]
    ) -> Tuple[int, Dict]:
        """
        Calculate optimal memory allocation based on metrics

        Args:
            function_name: Name of the Lambda function
            metrics: CloudWatch metrics

        Returns:
            Tuple of (recommended_memory_mb, analysis_details)
        """
        current_config = self.get_current_config(function_name)
        current_memory = current_config["memory_size"]

        if not metrics["duration"]:
            return current_memory, {"reason": "No metrics available"}

        # Calculate statistics
        avg_duration = statistics.mean(metrics["duration"])
        max_duration = max(metrics["duration_max"]) if metrics["duration_max"] else 0
        p95_duration = (
            statistics.quantiles(metrics["duration"], n=20)[18]
            if len(metrics["duration"]) > 20
            else max_duration
        )

        # Memory allocation recommendations based on duration patterns
        # AWS Lambda: More memory = More CPU = Faster execution
        # Cost-optimal point is usually where duration * memory is minimized

        analysis = {
            "current_memory_mb": current_memory,
            "avg_duration_ms": round(avg_duration, 2),
            "max_duration_ms": round(max_duration, 2),
            "p95_duration_ms": round(p95_duration, 2),
            "total_invocations": sum(metrics["invocations"]),
            "total_errors": sum(metrics["errors"]),
        }

        # Recommendation logic
        if avg_duration < 100:
            # Very fast functions - can use minimal memory
            recommended_memory = 256
            analysis["reason"] = "Fast execution - minimal memory sufficient"
        elif avg_duration < 500:
            # Fast functions - moderate memory
            recommended_memory = 512
            analysis["reason"] = "Moderate execution - standard memory"
        elif avg_duration < 2000:
            # Medium functions - more memory for better performance
            recommended_memory = 1024
            analysis["reason"] = "Medium execution - increased memory for performance"
        elif avg_duration < 5000:
            # Slower functions - high memory
            recommended_memory = 2048
            analysis["reason"] = "Slow execution - high memory for compute-intensive tasks"
        else:
            # Very slow functions - maximum memory
            recommended_memory = 3008
            analysis["reason"] = "Very slow execution - maximum memory recommended"

        # Adjust based on error rate
        if metrics["errors"] and sum(metrics["errors"]) > 0:
            error_rate = sum(metrics["errors"]) / sum(metrics["invocations"])
            if error_rate > 0.05:  # More than 5% errors
                analysis["warning"] = f"High error rate: {error_rate:.2%}"

        # Calculate cost impact
        current_cost_per_million = self._calculate_cost(current_memory, avg_duration)
        recommended_cost_per_million = self._calculate_cost(
            recommended_memory, avg_duration * (current_memory / recommended_memory)
        )

        analysis["current_cost_per_1m_invocations"] = f"${current_cost_per_million:.2f}"
        analysis[
            "estimated_cost_per_1m_invocations"
        ] = f"${recommended_cost_per_million:.2f}"
        analysis["estimated_savings"] = (
            f"${current_cost_per_million - recommended_cost_per_million:.2f}"
        )

        return recommended_memory, analysis

    def _calculate_cost(self, memory_mb: int, duration_ms: float) -> float:
        """
        Calculate Lambda cost per million invocations

        Args:
            memory_mb: Memory allocation in MB
            duration_ms: Average duration in milliseconds

        Returns:
            Cost per million invocations in USD
        """
        # AWS Lambda pricing (us-east-1)
        # $0.0000166667 per GB-second
        # $0.20 per 1M requests

        gb_seconds = (memory_mb / 1024) * (duration_ms / 1000)
        compute_cost = gb_seconds * 0.0000166667 * 1_000_000
        request_cost = 0.20

        return compute_cost + request_cost

    def profile_all_functions(
        self, function_prefix: str = "aquachain", days: int = 7
    ) -> Dict[str, Dict]:
        """
        Profile all Lambda functions with given prefix

        Args:
            function_prefix: Prefix to filter functions
            days: Number of days to analyze

        Returns:
            Dictionary of function names to recommendations
        """
        # List all functions
        paginator = self.lambda_client.get_paginator("list_functions")
        functions = []

        for page in paginator.paginate():
            functions.extend(
                [
                    f["FunctionName"]
                    for f in page["Functions"]
                    if f["FunctionName"].startswith(function_prefix)
                ]
            )

        print(f"Found {len(functions)} functions with prefix '{function_prefix}'")

        recommendations = {}

        for function_name in functions:
            print(f"\nProfiling {function_name}...")

            try:
                metrics = self.get_function_metrics(function_name, days)
                recommended_memory, analysis = self.calculate_optimal_memory(
                    function_name, metrics
                )

                recommendations[function_name] = {
                    "recommended_memory_mb": recommended_memory,
                    "analysis": analysis,
                }

                print(f"  Current: {analysis['current_memory_mb']} MB")
                print(f"  Recommended: {recommended_memory} MB")
                print(f"  Reason: {analysis['reason']}")

            except Exception as e:
                print(f"  Error profiling {function_name}: {str(e)}")
                recommendations[function_name] = {"error": str(e)}

        return recommendations

    def generate_report(
        self, recommendations: Dict[str, Dict], output_file: str = None
    ) -> str:
        """
        Generate a formatted report of recommendations

        Args:
            recommendations: Dictionary of recommendations
            output_file: Optional file to write report to

        Returns:
            Formatted report string
        """
        report_lines = [
            "# Lambda Memory Optimization Report",
            f"\nGenerated: {datetime.utcnow().isoformat()}",
            "\n## Summary\n",
        ]

        total_functions = len(recommendations)
        functions_with_recommendations = sum(
            1
            for r in recommendations.values()
            if "recommended_memory_mb" in r
            and r["recommended_memory_mb"] != r["analysis"]["current_memory_mb"]
        )

        report_lines.append(f"Total functions analyzed: {total_functions}")
        report_lines.append(
            f"Functions with optimization opportunities: {functions_with_recommendations}\n"
        )

        report_lines.append("## Recommendations\n")

        for function_name, rec in sorted(recommendations.items()):
            if "error" in rec:
                report_lines.append(f"### {function_name}")
                report_lines.append(f"Error: {rec['error']}\n")
                continue

            if "recommended_memory_mb" not in rec:
                continue

            analysis = rec["analysis"]
            recommended = rec["recommended_memory_mb"]
            current = analysis["current_memory_mb"]

            report_lines.append(f"### {function_name}\n")
            report_lines.append(f"**Current Memory**: {current} MB")
            report_lines.append(f"**Recommended Memory**: {recommended} MB")
            report_lines.append(f"**Change**: {recommended - current:+d} MB\n")

            report_lines.append(f"**Performance Metrics**:")
            report_lines.append(f"- Average Duration: {analysis['avg_duration_ms']} ms")
            report_lines.append(f"- P95 Duration: {analysis['p95_duration_ms']} ms")
            report_lines.append(f"- Max Duration: {analysis['max_duration_ms']} ms")
            report_lines.append(
                f"- Total Invocations: {analysis['total_invocations']:.0f}"
            )

            if analysis.get("total_errors", 0) > 0:
                report_lines.append(f"- Total Errors: {analysis['total_errors']:.0f}")

            report_lines.append(f"\n**Cost Analysis**:")
            report_lines.append(
                f"- Current Cost: {analysis['current_cost_per_1m_invocations']}"
            )
            report_lines.append(
                f"- Estimated Cost: {analysis['estimated_cost_per_1m_invocations']}"
            )
            report_lines.append(f"- Estimated Savings: {analysis['estimated_savings']}")

            report_lines.append(f"\n**Reason**: {analysis['reason']}\n")

            if "warning" in analysis:
                report_lines.append(f"⚠️ **Warning**: {analysis['warning']}\n")

        report = "\n".join(report_lines)

        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            print(f"\nReport written to {output_file}")

        return report


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Profile Lambda function memory usage"
    )
    parser.add_argument(
        "--function",
        help="Specific function name to profile (optional)",
    )
    parser.add_argument(
        "--prefix",
        default="aquachain",
        help="Function name prefix to filter (default: aquachain)",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to analyze (default: 7)"
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--output", help="Output file for report (optional)"
    )

    args = parser.parse_args()

    profiler = LambdaMemoryProfiler(region=args.region)

    if args.function:
        # Profile single function
        print(f"Profiling function: {args.function}")
        metrics = profiler.get_function_metrics(args.function, args.days)
        recommended_memory, analysis = profiler.calculate_optimal_memory(
            args.function, metrics
        )

        recommendations = {args.function: {"recommended_memory_mb": recommended_memory, "analysis": analysis}}
    else:
        # Profile all functions with prefix
        recommendations = profiler.profile_all_functions(args.prefix, args.days)

    # Generate report
    report = profiler.generate_report(recommendations, args.output)
    print("\n" + report)


if __name__ == "__main__":
    main()
