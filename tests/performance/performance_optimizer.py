"""
Comprehensive Performance Optimizer for AquaChain
Orchestrates all performance optimization tools and provides unified reporting
"""

import argparse
import json
import time
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import concurrent.futures
import os

@dataclass
class OptimizationResult:
    """Result from running an optimization tool."""
    optimizer_name: str
    success: bool
    duration: float
    return_code: int
    recommendations_count: int
    high_priority_count: int
    cost_impact: str  # positive, negative, neutral
    stdout: str
    stderr: str
    error_message: Optional[str] = None

@dataclass
class PerformanceOptimizationReport:
    """Comprehensive performance optimization report."""
    optimization_run_id: str
    start_time: str
    end_time: str
    total_duration: float
    total_optimizers: int
    successful_optimizers: int
    failed_optimizers: int
    total_recommendations: int
    high_priority_recommendations: int
    optimization_results: List[OptimizationResult]
    summary: Dict[str, Any]
    cost_analysis: Dict[str, Any]

class PerformanceOptimizer:
    """Comprehensive performance optimizer orchestrator."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.optimization_run_id = f"perf-opt-{int(time.time())}"
        self.results: List[OptimizationResult] = []
        
        # Default optimization tools
        self.optimization_tools = [
            {
                'name': 'Lambda Optimizer',
                'script': 'tests/performance/lambda_optimizer.py',
                'args': ['--dry-run'],
                'timeout': 600,
                'critical': True
            },
            {
                'name': 'DynamoDB Optimizer',
                'script': 'tests/performance/dynamodb_optimizer.py',
                'args': ['--dry-run'],
                'timeout': 600,
                'critical': True
            },
            {
                'name': 'Caching Optimizer',
                'script': 'tests/performance/caching_optimizer.py',
                'args': ['--dry-run'],
                'timeout': 300,
                'critical': False
            },
            {
                'name': 'CDN Optimizer',
                'script': 'tests/performance/cdn_optimizer.py',
                'args': ['--dry-run'],
                'timeout': 300,
                'critical': False
            }
        ]
    
    def load_config(self, config_file: str):
        """Load optimization configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Override default tools with config
            if 'optimization_tools' in config:
                self.optimization_tools = config['optimization_tools']
            
            # Update run ID if specified
            if 'optimization_run_id' in config:
                self.optimization_run_id = config['optimization_run_id']
                
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            print("Using default configuration")
    
    def run_optimization_tool(self, tool_config: Dict) -> OptimizationResult:
        """Run a single optimization tool."""
        print(f"🔧 Running {tool_config['name']}...")
        
        start_time = time.time()
        
        try:
            # Prepare command
            cmd = [sys.executable, tool_config['script']] + tool_config['args']
            
            # Run optimization tool with timeout
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=tool_config.get('timeout', 600),
                cwd=os.getcwd()
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = process.returncode == 0
            
            # Parse output for recommendations count (simplified)
            recommendations_count = self._parse_recommendations_count(process.stdout)
            high_priority_count = self._parse_high_priority_count(process.stdout)
            cost_impact = self._parse_cost_impact(process.stdout)
            
            result = OptimizationResult(
                optimizer_name=tool_config['name'],
                success=success,
                duration=duration,
                return_code=process.returncode,
                recommendations_count=recommendations_count,
                high_priority_count=high_priority_count,
                cost_impact=cost_impact,
                stdout=process.stdout,
                stderr=process.stderr
            )
            
            if success:
                print(f"✅ {tool_config['name']} completed successfully ({duration:.1f}s)")
                print(f"   Recommendations: {recommendations_count} (High Priority: {high_priority_count})")
            else:
                print(f"❌ {tool_config['name']} failed ({duration:.1f}s)")
                result.error_message = f"Optimization failed with return code {process.returncode}"
            
            return result
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ {tool_config['name']} timed out after {duration:.1f}s")
            
            return OptimizationResult(
                optimizer_name=tool_config['name'],
                success=False,
                duration=duration,
                return_code=-1,
                recommendations_count=0,
                high_priority_count=0,
                cost_impact="unknown",
                stdout="",
                stderr="",
                error_message=f"Optimization timed out after {tool_config.get('timeout', 600)} seconds"
            )
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"💥 {tool_config['name']} failed with exception: {e}")
            
            return OptimizationResult(
                optimizer_name=tool_config['name'],
                success=False,
                duration=duration,
                return_code=-2,
                recommendations_count=0,
                high_priority_count=0,
                cost_impact="unknown",
                stdout="",
                stderr=str(e),
                error_message=f"Optimization failed with exception: {e}"
            )
    
    def _parse_recommendations_count(self, stdout: str) -> int:
        """Parse recommendations count from tool output."""
        try:
            # Look for patterns like "Total Recommendations: 5"
            lines = stdout.split('\n')
            for line in lines:
                if 'Total Recommendations:' in line:
                    return int(line.split(':')[1].strip())
            return 0
        except Exception:
            return 0
    
    def _parse_high_priority_count(self, stdout: str) -> int:
        """Parse high priority recommendations count from tool output."""
        try:
            # Look for patterns like "High Priority Recommendations: 2"
            lines = stdout.split('\n')
            for line in lines:
                if 'High Priority Recommendations:' in line:
                    return int(line.split(':')[1].strip())
            return 0
        except Exception:
            return 0
    
    def _parse_cost_impact(self, stdout: str) -> str:
        """Parse overall cost impact from tool output."""
        try:
            # Analyze cost impact mentions in output
            positive_keywords = ['cost reduction', 'reduce costs', 'save money']
            negative_keywords = ['cost increase', 'additional costs', 'more expensive']
            
            stdout_lower = stdout.lower()
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in stdout_lower)
            negative_count = sum(1 for keyword in negative_keywords if keyword in stdout_lower)
            
            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    def run_all_optimizations(self, parallel: bool = False, 
                            max_workers: int = 2, apply_changes: bool = False) -> PerformanceOptimizationReport:
        """Run all optimization tools and generate comprehensive report."""
        print("🔬 AquaChain Performance Optimization Suite")
        print("=" * 60)
        print(f"Optimization Run ID: {self.optimization_run_id}")
        print(f"Total Optimization Tools: {len(self.optimization_tools)}")
        print(f"Parallel Execution: {'Yes' if parallel else 'No'}")
        print(f"Apply Changes: {'Yes' if apply_changes else 'No (Dry Run)'}")
        if parallel:
            print(f"Max Workers: {max_workers}")
        print("=" * 60)
        
        # Update tool arguments based on apply_changes flag
        for tool in self.optimization_tools:
            if apply_changes:
                # Remove --dry-run and add --apply
                tool['args'] = [arg for arg in tool['args'] if arg != '--dry-run']
                if '--apply' not in tool['args']:
                    tool['args'].append('--apply')
            else:
                # Ensure --dry-run is present
                if '--dry-run' not in tool['args']:
                    tool['args'].append('--dry-run')
        
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()
        
        if parallel:
            # Run optimizations in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_tool = {
                    executor.submit(self.run_optimization_tool, tool): tool 
                    for tool in self.optimization_tools
                }
                
                for future in concurrent.futures.as_completed(future_to_tool):
                    result = future.result()
                    self.results.append(result)
        else:
            # Run optimizations sequentially
            for tool in self.optimization_tools:
                result = self.run_optimization_tool(tool)
                self.results.append(result)
        
        end_time = time.time()
        end_timestamp = datetime.now(timezone.utc).isoformat()
        total_duration = end_time - start_time
        
        # Generate report
        report = self._generate_report(start_timestamp, end_timestamp, total_duration)
        
        return report
    
    def _generate_report(self, start_timestamp: str, end_timestamp: str, 
                        total_duration: float) -> PerformanceOptimizationReport:
        """Generate comprehensive performance optimization report."""
        successful_optimizers = sum(1 for result in self.results if result.success)
        failed_optimizers = len(self.results) - successful_optimizers
        
        total_recommendations = sum(result.recommendations_count for result in self.results)
        high_priority_recommendations = sum(result.high_priority_count for result in self.results)
        
        # Generate summary
        summary = {
            "overall_success": failed_optimizers == 0,
            "total_optimization_time": sum(result.duration for result in self.results),
            "average_optimization_duration": sum(result.duration for result in self.results) / len(self.results) if self.results else 0,
            "success_rate": (successful_optimizers / len(self.results)) * 100 if self.results else 0,
            "failed_optimizers": [result.optimizer_name for result in self.results if not result.success],
            "most_recommendations": max(self.results, key=lambda r: r.recommendations_count).optimizer_name if self.results else None,
            "longest_optimization": max(self.results, key=lambda r: r.duration).optimizer_name if self.results else None,
            "shortest_optimization": min(self.results, key=lambda r: r.duration).optimizer_name if self.results else None
        }
        
        # Cost analysis
        cost_impacts = [result.cost_impact for result in self.results if result.success]
        cost_analysis = {
            "positive_impact_count": cost_impacts.count("positive"),
            "negative_impact_count": cost_impacts.count("negative"),
            "neutral_impact_count": cost_impacts.count("neutral"),
            "overall_cost_impact": self._calculate_overall_cost_impact(cost_impacts),
            "estimated_monthly_savings": self._estimate_monthly_savings(),
            "estimated_monthly_costs": self._estimate_monthly_costs()
        }
        
        return PerformanceOptimizationReport(
            optimization_run_id=self.optimization_run_id,
            start_time=start_timestamp,
            end_time=end_timestamp,
            total_duration=total_duration,
            total_optimizers=len(self.results),
            successful_optimizers=successful_optimizers,
            failed_optimizers=failed_optimizers,
            total_recommendations=total_recommendations,
            high_priority_recommendations=high_priority_recommendations,
            optimization_results=self.results,
            summary=summary,
            cost_analysis=cost_analysis
        )
    
    def _calculate_overall_cost_impact(self, cost_impacts: List[str]) -> str:
        """Calculate overall cost impact from individual impacts."""
        if not cost_impacts:
            return "neutral"
        
        positive_count = cost_impacts.count("positive")
        negative_count = cost_impacts.count("negative")
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _estimate_monthly_savings(self) -> float:
        """Estimate monthly cost savings from optimizations."""
        # Simplified estimation based on optimization types
        savings = 0.0
        
        for result in self.results:
            if result.success and result.cost_impact == "positive":
                if "Lambda" in result.optimizer_name:
                    savings += 200.0  # Estimated Lambda cost savings
                elif "DynamoDB" in result.optimizer_name:
                    savings += 150.0  # Estimated DynamoDB cost savings
                elif "CDN" in result.optimizer_name:
                    savings += 100.0  # Estimated CDN cost savings
        
        return savings
    
    def _estimate_monthly_costs(self) -> float:
        """Estimate monthly additional costs from optimizations."""
        costs = 0.0
        
        for result in self.results:
            if result.success and result.cost_impact == "negative":
                if "Lambda" in result.optimizer_name:
                    costs += 100.0  # Estimated additional Lambda costs
                elif "DynamoDB" in result.optimizer_name:
                    costs += 75.0   # Estimated additional DynamoDB costs
                elif "Caching" in result.optimizer_name:
                    costs += 50.0   # Estimated caching costs
        
        return costs
    
    def print_report(self, report: PerformanceOptimizationReport):
        """Print formatted performance optimization report."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE OPTIMIZATION REPORT")
        print("=" * 60)
        print(f"Optimization Run ID: {report.optimization_run_id}")
        print(f"Start Time: {report.start_time}")
        print(f"End Time: {report.end_time}")
        print(f"Total Duration: {report.total_duration:.1f} seconds ({report.total_duration/60:.1f} minutes)")
        print(f"Total Optimizers: {report.total_optimizers}")
        print(f"Successful: {report.successful_optimizers}")
        print(f"Failed: {report.failed_optimizers}")
        print(f"Success Rate: {report.summary['success_rate']:.1f}%")
        
        print("\n📋 Optimization Results:")
        print("-" * 60)
        for result in report.optimization_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            cost_icon = "💰" if result.cost_impact == "positive" else "💸" if result.cost_impact == "negative" else "⚖️"
            print(f"{status} {result.optimizer_name} ({result.duration:.1f}s) {cost_icon}")
            print(f"    Recommendations: {result.recommendations_count} (High Priority: {result.high_priority_count})")
            if not result.success and result.error_message:
                print(f"    Error: {result.error_message}")
        
        print("\n📈 Summary:")
        print("-" * 60)
        print(f"Overall Success: {'✅ YES' if report.summary['overall_success'] else '❌ NO'}")
        print(f"Total Recommendations: {report.total_recommendations}")
        print(f"High Priority Recommendations: {report.high_priority_recommendations}")
        print(f"Total Optimization Time: {report.summary['total_optimization_time']:.1f}s")
        print(f"Average Optimization Duration: {report.summary['average_optimization_duration']:.1f}s")
        
        if report.summary['failed_optimizers']:
            print(f"Failed Optimizers: {', '.join(report.summary['failed_optimizers'])}")
        
        print(f"Most Recommendations: {report.summary['most_recommendations']}")
        print(f"Longest Optimization: {report.summary['longest_optimization']}")
        print(f"Shortest Optimization: {report.summary['shortest_optimization']}")
        
        print("\n💰 Cost Analysis:")
        print("-" * 60)
        print(f"Overall Cost Impact: {report.cost_analysis['overall_cost_impact'].title()}")
        print(f"Positive Impact Optimizations: {report.cost_analysis['positive_impact_count']}")
        print(f"Negative Impact Optimizations: {report.cost_analysis['negative_impact_count']}")
        print(f"Neutral Impact Optimizations: {report.cost_analysis['neutral_impact_count']}")
        print(f"Estimated Monthly Savings: ${report.cost_analysis['estimated_monthly_savings']:.2f}")
        print(f"Estimated Monthly Additional Costs: ${report.cost_analysis['estimated_monthly_costs']:.2f}")
        
        net_impact = report.cost_analysis['estimated_monthly_savings'] - report.cost_analysis['estimated_monthly_costs']
        print(f"Net Monthly Impact: ${net_impact:.2f}")
        
        # Overall assessment
        print("\n🏆 OVERALL ASSESSMENT:")
        print("=" * 60)
        if report.failed_optimizers == 0 and report.high_priority_recommendations > 0:
            print("✅ PERFORMANCE OPTIMIZATION SUCCESSFUL")
            print(f"   {report.high_priority_recommendations} high-priority improvements identified")
            if net_impact > 0:
                print(f"   Estimated monthly savings: ${net_impact:.2f}")
        elif report.failed_optimizers == 0:
            print("✅ PERFORMANCE ANALYSIS COMPLETED")
            print("   System is already well-optimized")
        else:
            print("⚠️  PERFORMANCE OPTIMIZATION COMPLETED WITH WARNINGS")
            print(f"   {report.failed_optimizers} optimizer(s) failed")
            print("   Review failed optimizations and retry")
    
    def save_report(self, report: PerformanceOptimizationReport, output_file: str):
        """Save performance optimization report to JSON file."""
        try:
            # Convert dataclass to dict for JSON serialization
            report_dict = asdict(report)
            
            with open(output_file, 'w') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            print(f"📄 Report saved to: {output_file}")
            
        except Exception as e:
            print(f"Warning: Could not save report to {output_file}: {e}")

def main():
    """Main function to run performance optimization suite."""
    parser = argparse.ArgumentParser(description='AquaChain Performance Optimization Suite')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--parallel', action='store_true', help='Run optimizations in parallel')
    parser.add_argument('--max-workers', type=int, default=2, help='Max parallel workers (default: 2)')
    parser.add_argument('--apply', action='store_true', help='Apply optimizations (default: dry run)')
    parser.add_argument('--output', type=str, default=f'performance_optimization_report_{int(time.time())}.json', 
                       help='Output report file')
    parser.add_argument('--quiet', action='store_true', help='Suppress detailed output')
    
    args = parser.parse_args()
    
    try:
        optimizer = PerformanceOptimizer(config_file=args.config)
        
        if args.config:
            optimizer.load_config(args.config)
        
        # Run all optimizations
        report = optimizer.run_all_optimizations(
            parallel=args.parallel,
            max_workers=args.max_workers,
            apply_changes=args.apply
        )
        
        # Print report unless quiet mode
        if not args.quiet:
            optimizer.print_report(report)
        
        # Save JSON report
        optimizer.save_report(report, args.output)
        
        # Return appropriate exit code
        if report.failed_optimizers == 0:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"💥 Performance optimization failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())