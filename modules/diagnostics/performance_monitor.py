#!/usr/bin/env python3
"""
BlackStack Performance Diagnostics and Monitoring
Optimized for RTX 3060 and AMD Ryzen 7 7700 hardware
"""

import os
import sys
import time
import psutil
import logging
import platform
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

try:
    import nvidia_ml_py3 as nvml
    nvml.nvmlInit()
    HAS_NVML = True
except ImportError:
    HAS_NVML = False

@dataclass
class SystemSpecs:
    """System specifications for optimization reference."""
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    total_ram: int  # GB
    gpu_model: Optional[str]
    gpu_vram: Optional[int]  # GB
    os_info: str
    python_version: str

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    gpu_memory_usage: Optional[float]
    gpu_temperature: Optional[float]
    disk_io: Dict[str, float]
    network_io: Dict[str, float]

class OptimizedDiagnostics:
    """
    Comprehensive diagnostics and monitoring for BlackStack optimization.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system_specs = self._detect_system_specs()
        self.baseline_metrics = None
        self.optimization_recommendations = []
        
        self.logger.info("Diagnostics system initialized")
        self._log_system_specs()
    
    def _detect_system_specs(self) -> SystemSpecs:
        """Detect and analyze system specifications."""
        # CPU information
        cpu_info = platform.processor()
        if not cpu_info:
            try:
                cpu_info = subprocess.check_output(
                    ["cat", "/proc/cpuinfo"], universal_newlines=True
                ).split('\n')[4].split(':')[1].strip()
            except:
                cpu_info = "Unknown CPU"
        
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        
        # Memory information
        total_ram = round(psutil.virtual_memory().total / (1024**3))
        
        # GPU information
        gpu_model = None
        gpu_vram = None
        
        if HAS_NVML:
            try:
                handle = nvml.nvmlDeviceGetHandleByIndex(0)
                gpu_model = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                gpu_memory = nvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_vram = round(gpu_memory.total / (1024**3))
            except:
                pass
        elif HAS_TORCH and torch.cuda.is_available():
            gpu_model = torch.cuda.get_device_name(0)
            gpu_vram = round(torch.cuda.get_device_properties(0).total_memory / (1024**3))
        
        return SystemSpecs(
            cpu_model=cpu_info,
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            total_ram=total_ram,
            gpu_model=gpu_model,
            gpu_vram=gpu_vram,
            os_info=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version()
        )
    
    def _log_system_specs(self):
        """Log detected system specifications."""
        specs = self.system_specs
        self.logger.info("=== System Specifications ===")
        self.logger.info(f"CPU: {specs.cpu_model}")
        self.logger.info(f"Cores/Threads: {specs.cpu_cores}/{specs.cpu_threads}")
        self.logger.info(f"RAM: {specs.total_ram} GB")
        if specs.gpu_model:
            self.logger.info(f"GPU: {specs.gpu_model}")
            self.logger.info(f"VRAM: {specs.gpu_vram} GB")
        self.logger.info(f"OS: {specs.os_info}")
        self.logger.info(f"Python: {specs.python_version}")
        self.logger.info("=" * 30)
    
    def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        timestamp = datetime.now()
        
        # CPU and memory metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent
        
        # Disk I/O metrics
        disk_io = psutil.disk_io_counters()
        disk_metrics = {
            'read_mb_s': 0,
            'write_mb_s': 0
        } if disk_io is None else {
            'read_mb_s': disk_io.read_bytes / (1024**2),
            'write_mb_s': disk_io.write_bytes / (1024**2)
        }
        
        # Network I/O metrics
        net_io = psutil.net_io_counters()
        network_metrics = {
            'sent_mb_s': 0,
            'recv_mb_s': 0
        } if net_io is None else {
            'sent_mb_s': net_io.bytes_sent / (1024**2),
            'recv_mb_s': net_io.bytes_recv / (1024**2)
        }
        
        # GPU metrics
        gpu_usage = None
        gpu_memory_usage = None
        gpu_temperature = None
        
        if HAS_NVML:
            try:
                handle = nvml.nvmlDeviceGetHandleByIndex(0)
                gpu_util = nvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_usage = gpu_util.gpu
                
                gpu_memory = nvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_memory_usage = (gpu_memory.used / gpu_memory.total) * 100
                
                gpu_temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                gpu_temperature = gpu_temp
            except Exception as e:
                self.logger.debug(f"GPU metrics collection failed: {e}")
        
        return PerformanceMetrics(
            timestamp=timestamp,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            gpu_usage=gpu_usage,
            gpu_memory_usage=gpu_memory_usage,
            gpu_temperature=gpu_temperature,
            disk_io=disk_metrics,
            network_io=network_metrics
        )
    
    def set_baseline(self):
        """Set baseline performance metrics."""
        self.logger.info("Collecting baseline performance metrics...")
        self.baseline_metrics = self.collect_metrics()
        self.logger.info("Baseline metrics collected")
    
    def analyze_performance(self, current_metrics: PerformanceMetrics) -> Dict:
        """Analyze current performance against baseline and optimal parameters."""
        analysis = {
            'cpu_status': 'optimal',
            'memory_status': 'optimal',
            'gpu_status': 'optimal',
            'recommendations': [],
            'bottlenecks': [],
            'optimization_score': 100
        }
        
        # CPU Analysis
        if current_metrics.cpu_usage > 90:
            analysis['cpu_status'] = 'critical'
            analysis['bottlenecks'].append('CPU overloaded')
            analysis['recommendations'].append('Reduce concurrent processes or upgrade CPU')
            analysis['optimization_score'] -= 30
        elif current_metrics.cpu_usage > 70:
            analysis['cpu_status'] = 'warning'
            analysis['recommendations'].append('Monitor CPU usage, consider optimization')
            analysis['optimization_score'] -= 15
        
        # Memory Analysis
        if current_metrics.memory_usage > 90:
            analysis['memory_status'] = 'critical'
            analysis['bottlenecks'].append('Memory exhaustion')
            analysis['recommendations'].append('Free memory or add more RAM')
            analysis['optimization_score'] -= 25
        elif current_metrics.memory_usage > 80:
            analysis['memory_status'] = 'warning'
            analysis['recommendations'].append('Monitor memory usage')
            analysis['optimization_score'] -= 10
        
        # GPU Analysis (if available)
        if current_metrics.gpu_usage is not None:
            if current_metrics.gpu_memory_usage > 95:
                analysis['gpu_status'] = 'critical'
                analysis['bottlenecks'].append('GPU memory exhaustion')
                analysis['recommendations'].append('Reduce batch size or model precision')
                analysis['optimization_score'] -= 35
            elif current_metrics.gpu_memory_usage > 85:
                analysis['gpu_status'] = 'warning'
                analysis['recommendations'].append('Monitor GPU memory usage')
                analysis['optimization_score'] -= 15
            
            if current_metrics.gpu_temperature and current_metrics.gpu_temperature > 85:
                analysis['gpu_status'] = 'warning'
                analysis['recommendations'].append('GPU running hot, check cooling')
                analysis['optimization_score'] -= 10
        
        return analysis
    
    def benchmark_inference(self, model=None, iterations: int = 10) -> Dict:
        """Benchmark AI inference performance."""
        self.logger.info("Running inference benchmark...")
        
        if not HAS_TORCH:
            return {'error': 'PyTorch not available for benchmarking'}
        
        results = {
            'iterations': iterations,
            'times': [],
            'memory_usage': [],
            'gpu_utilization': []
        }
        
        # Create dummy data for benchmarking
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        dummy_input = torch.randn(1, 512, 768).to(device)  # Typical transformer input size
        
        for i in range(iterations):
            start_time = time.time()
            
            # Record initial GPU memory
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
                initial_memory = torch.cuda.memory_allocated()
            
            # Perform dummy computation (matrix multiplication)
            with torch.no_grad():
                result = torch.matmul(dummy_input, dummy_input.transpose(-2, -1))
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
            
            end_time = time.time()
            iteration_time = end_time - start_time
            results['times'].append(iteration_time)
            
            # Record memory usage
            if torch.cuda.is_available():
                peak_memory = torch.cuda.max_memory_allocated()
                results['memory_usage'].append(peak_memory - initial_memory)
            
            # Collect metrics
            metrics = self.collect_metrics()
            if metrics.gpu_usage is not None:
                results['gpu_utilization'].append(metrics.gpu_usage)
        
        # Calculate statistics
        avg_time = sum(results['times']) / len(results['times'])
        min_time = min(results['times'])
        max_time = max(results['times'])
        
        benchmark_results = {
            'average_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_dev': (sum((t - avg_time) ** 2 for t in results['times']) / len(results['times'])) ** 0.5,
            'throughput': 1.0 / avg_time,  # operations per second
        }
        
        if results['memory_usage']:
            benchmark_results['avg_memory_mb'] = sum(results['memory_usage']) / len(results['memory_usage']) / (1024**2)
        
        if results['gpu_utilization']:
            benchmark_results['avg_gpu_util'] = sum(results['gpu_utilization']) / len(results['gpu_utilization'])
        
        self.logger.info(f"Benchmark completed: {avg_time:.3f}s avg, {benchmark_results['throughput']:.1f} ops/s")
        return benchmark_results
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get hardware-specific optimization recommendations."""
        recommendations = []
        specs = self.system_specs
        
        # CPU-specific recommendations
        if "ryzen" in specs.cpu_model.lower():
            recommendations.extend([
                "Enable CPU boost mode: sudo cpupower frequency-set -g performance",
                "Use AMD-optimized libraries (MKL-DNN, BLIS)",
                "Consider enabling SMT (Simultaneous Multithreading)",
                "Set CPU affinity for critical processes"
            ])
        
        # GPU-specific recommendations
        if specs.gpu_model and "3060" in specs.gpu_model:
            recommendations.extend([
                "Use 4-bit quantization to maximize VRAM efficiency",
                "Optimize batch sizes for 12GB VRAM (recommended: 4-8)",
                "Enable GPU persistence mode: nvidia-smi -pm 1",
                "Monitor temperature: keep under 80°C for optimal performance",
                "Use mixed precision training (fp16) when possible"
            ])
        
        # Memory recommendations
        if specs.total_ram >= 32:
            recommendations.extend([
                "Enable memory prefetching for large models",
                "Use memory-mapped files for large datasets",
                "Consider RAM disk for temporary files"
            ])
        else:
            recommendations.extend([
                "Monitor memory usage closely",
                "Use gradient checkpointing to reduce memory",
                "Consider model sharding for large models"
            ])
        
        # General optimization
        recommendations.extend([
            "Use optimized BLAS libraries (OpenBLAS, Intel MKL)",
            "Enable CPU features: AVX, AVX2, FMA",
            "Disable unnecessary background processes",
            "Use SSD for model storage and temporary files",
            "Monitor system temperatures under load"
        ])
        
        return recommendations
    
    def run_comprehensive_diagnostic(self) -> Dict:
        """Run a comprehensive system diagnostic."""
        self.logger.info("Running comprehensive diagnostic...")
        
        diagnostic_results = {
            'system_specs': self.system_specs,
            'baseline_metrics': self.baseline_metrics,
            'current_metrics': self.collect_metrics(),
            'benchmark_results': self.benchmark_inference(),
            'optimization_recommendations': self.get_optimization_recommendations(),
            'hardware_compatibility': self._check_hardware_compatibility(),
            'software_compatibility': self._check_software_compatibility()
        }
        
        # Performance analysis
        if self.baseline_metrics:
            diagnostic_results['performance_analysis'] = self.analyze_performance(
                diagnostic_results['current_metrics']
            )
        
        self.logger.info("Comprehensive diagnostic completed")
        return diagnostic_results
    
    def _check_hardware_compatibility(self) -> Dict:
        """Check hardware compatibility with optimization requirements."""
        compatibility = {
            'cpu_compatible': True,
            'gpu_compatible': True,
            'memory_sufficient': True,
            'warnings': []
        }
        
        specs = self.system_specs
        
        # Check CPU compatibility
        if specs.cpu_threads < 8:
            compatibility['cpu_compatible'] = False
            compatibility['warnings'].append("CPU has fewer than 8 threads, may impact performance")
        
        # Check GPU compatibility
        if not specs.gpu_model:
            compatibility['gpu_compatible'] = False
            compatibility['warnings'].append("No GPU detected, will use CPU-only inference")
        elif specs.gpu_vram and specs.gpu_vram < 8:
            compatibility['warnings'].append("GPU has less than 8GB VRAM, use smaller models or quantization")
        
        # Check memory
        if specs.total_ram < 16:
            compatibility['memory_sufficient'] = False
            compatibility['warnings'].append("Less than 16GB RAM, may encounter memory issues")
        
        return compatibility
    
    def _check_software_compatibility(self) -> Dict:
        """Check software compatibility and versions."""
        compatibility = {
            'python_version_ok': True,
            'pytorch_available': HAS_TORCH,
            'cuda_available': False,
            'recommended_versions': {},
            'issues': []
        }
        
        # Check Python version
        python_version = tuple(map(int, platform.python_version().split('.')))
        if python_version < (3, 8):
            compatibility['python_version_ok'] = False
            compatibility['issues'].append("Python 3.8+ recommended for optimal performance")
        
        # Check PyTorch and CUDA
        if HAS_TORCH:
            compatibility['pytorch_version'] = torch.__version__
            compatibility['cuda_available'] = torch.cuda.is_available()
            if torch.cuda.is_available():
                compatibility['cuda_version'] = torch.version.cuda
        else:
            compatibility['issues'].append("PyTorch not installed, required for AI functionality")
        
        return compatibility


def main():
    """Main diagnostic entry point."""
    logging.basicConfig(level=logging.INFO)
    
    diagnostics = OptimizedDiagnostics()
    diagnostics.set_baseline()
    
    # Run comprehensive diagnostic
    results = diagnostics.run_comprehensive_diagnostic()
    
    print("\n" + "="*60)
    print("BlackStack Performance Diagnostic Report")
    print("="*60)
    
    # System specifications
    specs = results['system_specs']
    print(f"\nSystem: {specs.cpu_model}")
    print(f"CPU: {specs.cpu_cores} cores / {specs.cpu_threads} threads")
    print(f"RAM: {specs.total_ram} GB")
    if specs.gpu_model:
        print(f"GPU: {specs.gpu_model} ({specs.gpu_vram} GB VRAM)")
    
    # Performance metrics
    metrics = results['current_metrics']
    print(f"\nCurrent Performance:")
    print(f"CPU Usage: {metrics.cpu_usage:.1f}%")
    print(f"Memory Usage: {metrics.memory_usage:.1f}%")
    if metrics.gpu_usage is not None:
        print(f"GPU Usage: {metrics.gpu_usage:.1f}%")
        print(f"GPU Memory: {metrics.gpu_memory_usage:.1f}%")
        if metrics.gpu_temperature:
            print(f"GPU Temperature: {metrics.gpu_temperature}°C")
    
    # Benchmark results
    if 'benchmark_results' in results and 'average_time' in results['benchmark_results']:
        bench = results['benchmark_results']
        print(f"\nBenchmark Results:")
        print(f"Average Inference Time: {bench['average_time']*1000:.1f}ms")
        print(f"Throughput: {bench['throughput']:.1f} ops/sec")
    
    # Optimization recommendations
    print(f"\nOptimization Recommendations:")
    for i, rec in enumerate(results['optimization_recommendations'][:5], 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()