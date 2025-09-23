"""
Pipeline Performance Monitor

Tracks timing, cost, and performance metrics for the FreeWorld job processing pipeline.
Provides detailed logging, memory usage optimization, and API rate limiting.
"""

import time
import psutil
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage"""
    stage_name: str
    start_time: float
    end_time: float
    duration_seconds: float
    memory_usage_mb: float
    cpu_percent: float
    api_calls_made: int
    api_cost_usd: float
    jobs_processed: int
    errors_count: int
    success_rate: float

@dataclass  
class PipelineRunMetrics:
    """Complete metrics for a pipeline run"""
    run_id: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    total_jobs_input: int
    total_jobs_output: int
    total_api_calls: int
    total_cost_usd: float
    total_memory_peak_mb: float
    stages: List[StageMetrics]
    market: str
    mode: str
    success: bool
    error_message: Optional[str] = None

class PerformanceMonitor:
    """Performance monitoring and optimization for pipeline runs"""
    
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stages: List[StageMetrics] = []
        self.current_stage: Optional[str] = None
        self.stage_start_time: Optional[float] = None
        self.run_start_time = time.time()
        self.run_start_datetime = datetime.now(timezone.utc)
        
        # Performance tracking
        self.memory_peak = 0.0
        self.total_api_calls = 0
        self.total_cost = 0.0
        self.total_jobs_input = 0
        self.total_jobs_output = 0
        
        # Logging setup
        self.logger = logging.getLogger(f'performance.{self.run_id}')
        self.logger.setLevel(logging.INFO)
        
        # Create performance logs directory
        log_dir = Path('logs/performance')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for this run
        log_file = log_dir / f'{self.run_id}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"Performance monitoring started for run: {self.run_id}")
    
    def start_stage(self, stage_name: str) -> None:
        """Start monitoring a pipeline stage"""
        if self.current_stage:
            self.logger.warning(f"Stage {self.current_stage} not properly ended before starting {stage_name}")
            self.end_stage()
        
        self.current_stage = stage_name
        self.stage_start_time = time.time()
        
        # Reset stage-specific counters
        self._stage_api_calls = 0
        self._stage_cost = 0.0
        self._stage_errors = 0
        
        self.logger.info(f"Started stage: {stage_name}")
        print(f"🔄 Starting {stage_name}...")
    
    def end_stage(self, jobs_processed: int = 0) -> StageMetrics:
        """End monitoring current stage and record metrics"""
        if not self.current_stage or not self.stage_start_time:
            raise ValueError("No stage currently being monitored")
        
        end_time = time.time()
        duration = end_time - self.stage_start_time
        
        # Get current system metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        # Update peak memory
        self.memory_peak = max(self.memory_peak, memory_mb)
        
        # Calculate success rate
        success_rate = 1.0 if self._stage_errors == 0 else max(0.0, 1.0 - (self._stage_errors / max(1, jobs_processed)))
        
        stage_metrics = StageMetrics(
            stage_name=self.current_stage,
            start_time=self.stage_start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent,
            api_calls_made=self._stage_api_calls,
            api_cost_usd=self._stage_cost,
            jobs_processed=jobs_processed,
            errors_count=self._stage_errors,
            success_rate=success_rate
        )
        
        self.stages.append(stage_metrics)
        
        # Update totals
        self.total_api_calls += self._stage_api_calls
        self.total_cost += self._stage_cost
        
        # Log completion
        self.logger.info(f"Completed stage: {self.current_stage} in {duration:.2f}s")
        print(f"✅ {self.current_stage} completed: {duration:.2f}s, {jobs_processed} jobs, ${self._stage_cost:.4f}")
        
        # Reset current stage
        self.current_stage = None
        self.stage_start_time = None
        
        return stage_metrics
    
    def log_api_call(self, service: str, cost: float = 0.0) -> None:
        """Log an API call and its cost"""
        if self.current_stage:
            self._stage_api_calls += 1
            self._stage_cost += cost
        
        self.logger.debug(f"API call to {service}: ${cost:.4f}")
    
    def log_error(self, error_msg: str, stage: Optional[str] = None) -> None:
        """Log an error occurrence"""
        target_stage = stage or self.current_stage
        if target_stage == self.current_stage:
            self._stage_errors += 1
        
        self.logger.error(f"Error in {target_stage}: {error_msg}")
    
    def finalize_run(self, market: str, mode: str, jobs_input: int, jobs_output: int, 
                     success: bool = True, error_message: Optional[str] = None) -> PipelineRunMetrics:
        """Finalize the pipeline run and generate complete metrics"""
        
        # End any ongoing stage
        if self.current_stage:
            self.end_stage()
        
        run_end_time = time.time()
        total_duration = run_end_time - self.run_start_time
        
        # Store totals
        self.total_jobs_input = jobs_input
        self.total_jobs_output = jobs_output
        
        metrics = PipelineRunMetrics(
            run_id=self.run_id,
            start_time=self.run_start_datetime.isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            total_duration_seconds=total_duration,
            total_jobs_input=jobs_input,
            total_jobs_output=jobs_output,
            total_api_calls=self.total_api_calls,
            total_cost_usd=self.total_cost,
            total_memory_peak_mb=self.memory_peak,
            stages=self.stages,
            market=market,
            mode=mode,
            success=success,
            error_message=error_message
        )
        
        # Save metrics to file
        self._save_metrics(metrics)
        
        # Log summary
        self.logger.info(f"Pipeline run completed: {total_duration:.2f}s total")
        self.logger.info(f"Jobs processed: {jobs_input} → {jobs_output}")
        self.logger.info(f"Total cost: ${self.total_cost:.4f}")
        self.logger.info(f"Peak memory: {self.memory_peak:.1f}MB")
        
        print(f"\n📊 Pipeline Performance Summary:")
        print(f"   ⏱️  Total time: {total_duration:.2f}s")
        print(f"   📋 Jobs: {jobs_input} → {jobs_output} ({jobs_output/max(1,jobs_input)*100:.1f}%)")
        print(f"   💰 Cost: ${self.total_cost:.4f}")
        print(f"   🧠 Peak memory: {self.memory_peak:.1f}MB")
        print(f"   🔄 API calls: {self.total_api_calls}")
        
        return metrics
    
    def _save_metrics(self, metrics: PipelineRunMetrics) -> None:
        """Save metrics to JSON file"""
        metrics_dir = Path('logs/metrics')
        metrics_dir.mkdir(parents=True, exist_ok=True)
        
        metrics_file = metrics_dir / f'{self.run_id}_metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2, default=str)
        
        print(f"📈 Metrics saved: {metrics_file}")

class PerformanceAnalyzer:
    """Analyze historical performance data"""
    
    @staticmethod
    def load_recent_runs(limit: int = 10) -> List[PipelineRunMetrics]:
        """Load recent pipeline run metrics"""
        metrics_dir = Path('logs/metrics')
        if not metrics_dir.exists():
            return []
        
        metrics_files = sorted(metrics_dir.glob('*_metrics.json'), reverse=True)[:limit]
        runs = []
        
        for file_path in metrics_files:
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    # Convert stages back to StageMetrics objects
                    stages = [StageMetrics(**stage) for stage in data['stages']]
                    data['stages'] = stages
                    runs.append(PipelineRunMetrics(**data))
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
        
        return runs
    
    @staticmethod
    def generate_performance_report(runs: List[PipelineRunMetrics]) -> Dict[str, Any]:
        """Generate performance analysis report"""
        if not runs:
            return {"error": "No performance data available"}
        
        total_runs = len(runs)
        successful_runs = [r for r in runs if r.success]
        success_rate = len(successful_runs) / total_runs
        
        # Timing analysis
        durations = [r.total_duration_seconds for r in successful_runs]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Cost analysis
        costs = [r.total_cost_usd for r in successful_runs]
        avg_cost = sum(costs) / len(costs) if costs else 0
        
        # Memory analysis
        memory_peaks = [r.total_memory_peak_mb for r in successful_runs]
        avg_memory = sum(memory_peaks) / len(memory_peaks) if memory_peaks else 0
        
        # Stage performance
        stage_performance = {}
        for run in successful_runs:
            for stage in run.stages:
                if stage.stage_name not in stage_performance:
                    stage_performance[stage.stage_name] = {
                        'durations': [],
                        'success_rates': [],
                        'costs': []
                    }
                stage_performance[stage.stage_name]['durations'].append(stage.duration_seconds)
                stage_performance[stage.stage_name]['success_rates'].append(stage.success_rate)
                stage_performance[stage.stage_name]['costs'].append(stage.api_cost_usd)
        
        # Calculate stage averages
        stage_summary = {}
        for stage_name, data in stage_performance.items():
            stage_summary[stage_name] = {
                'avg_duration': sum(data['durations']) / len(data['durations']),
                'avg_success_rate': sum(data['success_rates']) / len(data['success_rates']),
                'avg_cost': sum(data['costs']) / len(data['costs'])
            }
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'total_runs_analyzed': total_runs,
            'success_rate': success_rate,
            'performance_metrics': {
                'avg_duration_seconds': avg_duration,
                'avg_cost_usd': avg_cost,
                'avg_memory_peak_mb': avg_memory
            },
            'stage_performance': stage_summary,
            'recommendations': PerformanceAnalyzer._generate_recommendations(
                avg_duration, avg_cost, avg_memory, stage_summary
            )
        }
    
    @staticmethod
    def _generate_recommendations(avg_duration: float, avg_cost: float, 
                                avg_memory: float, stages: Dict) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if avg_duration > 60:  # More than 1 minute
            recommendations.append("Consider optimizing slow pipeline stages - average runtime exceeds 60s")
        
        if avg_cost > 0.50:  # More than 50 cents per run
            recommendations.append("API costs are high - consider implementing more aggressive caching")
        
        if avg_memory > 500:  # More than 500MB
            recommendations.append("Memory usage is high - optimize data structures and implement batch processing")
        
        # Stage-specific recommendations
        slowest_stage = max(stages.items(), key=lambda x: x[1]['avg_duration'], default=(None, None))
        if slowest_stage[0]:
            recommendations.append(f"Focus optimization on '{slowest_stage[0]}' stage - highest average duration")
        
        if not recommendations:
            recommendations.append("Performance metrics look good - system is operating efficiently")
        
        return recommendations

def benchmark_pipeline(market: str, mode: str = 'sample') -> None:
    """Run performance benchmark for pipeline"""
    print(f"🚀 Starting performance benchmark: {market} ({mode})")
    
    monitor = PerformanceMonitor(f"benchmark_{market}_{mode}")
    
    try:
        # Import here to avoid circular dependencies
        from terminal_job_search import main as terminal_main
        import sys
        
        # Mock command line args for benchmark
        original_argv = sys.argv
        sys.argv = [
            'terminal_job_search.py',
            '--market', market,
            '--mode', mode,
            '--performance-monitor', monitor.run_id
        ]
        
        # Run the pipeline with monitoring
        terminal_main()
        
    except Exception as e:
        monitor.log_error(f"Benchmark failed: {e}")
        print(f"❌ Benchmark failed: {e}")
    finally:
        # Restore original argv
        if 'original_argv' in locals():
            sys.argv = original_argv

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline Performance Monitor')
    parser.add_argument('--market', default='houston', help='Market to benchmark')
    parser.add_argument('--benchmark', action='store_true', help='Run performance benchmark')
    parser.add_argument('--analyze', action='store_true', help='Analyze recent performance data')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    
    args = parser.parse_args()
    
    if args.benchmark:
        benchmark_pipeline(args.market)
    elif args.analyze or args.report:
        analyzer = PerformanceAnalyzer()
        recent_runs = analyzer.load_recent_runs()
        
        if not recent_runs:
            print("No performance data found. Run some pipeline operations first.")
        else:
            report = analyzer.generate_performance_report(recent_runs)
            
            print("\n📊 Performance Analysis Report")
            print("=" * 50)
            print(f"Analyzed {report['total_runs_analyzed']} runs")
            print(f"Success rate: {report['success_rate']:.1%}")
            print(f"Average duration: {report['performance_metrics']['avg_duration_seconds']:.2f}s")
            print(f"Average cost: ${report['performance_metrics']['avg_cost_usd']:.4f}")
            print(f"Average memory: {report['performance_metrics']['avg_memory_peak_mb']:.1f}MB")
            
            print("\n🎯 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
    else:
        print("Use --benchmark, --analyze, or --report flags")