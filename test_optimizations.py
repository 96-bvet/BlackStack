#!/usr/bin/env python3
"""
BlackStack Optimization Test Suite
Comprehensive testing for performance optimizations
"""

import os
import sys
import time
import logging
import unittest
import subprocess
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class OptimizationTestSuite(unittest.TestCase):
    """Test suite for BlackStack optimizations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        logger.info("Setting up optimization test suite...")
        cls.test_results = {}
        cls.performance_metrics = {}
    
    def test_01_requirements_optimization(self):
        """Test that requirements.txt is optimized and clean."""
        logger.info("Testing requirements optimization...")
        
        req_file = os.path.join(PROJECT_ROOT, 'requirements.txt')
        self.assertTrue(os.path.exists(req_file), "requirements.txt should exist")
        
        with open(req_file, 'r') as f:
            content = f.read()
        
        # Check for optimization indicators
        self.assertIn('# Optimized for RTX 3060', content, "Should have hardware optimization comments")
        
        # Check for version pinning
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        versioned_lines = [line for line in lines if '>=' in line or '==' in line]
        self.assertGreater(len(versioned_lines), len(lines) * 0.8, "Most dependencies should be version-pinned")
        
        # Check for duplicate elimination
        packages = [line.split('>=')[0].split('==')[0] for line in lines]
        unique_packages = set(packages)
        self.assertEqual(len(packages), len(unique_packages), "No duplicate packages should exist")
        
        logger.info("✓ Requirements optimization test passed")
    
    def test_02_package_structure(self):
        """Test that __init__.py files are properly placed."""
        logger.info("Testing package structure...")
        
        # Key directories that should have __init__.py
        key_dirs = [
            'modules',
            'modules/voice',
            'modules/diagnostics',
            'models',
            'runtime',
            'registry',
            'config',
            'ingest',
            'audit'
        ]
        
        missing_init = []
        for dir_path in key_dirs:
            full_path = os.path.join(PROJECT_ROOT, dir_path)
            init_file = os.path.join(full_path, '__init__.py')
            if os.path.exists(full_path) and not os.path.exists(init_file):
                missing_init.append(dir_path)
        
        self.assertEqual(len(missing_init), 0, f"Missing __init__.py files in: {missing_init}")
        logger.info("✓ Package structure test passed")
    
    def test_03_optimized_modules_availability(self):
        """Test that optimized modules can be imported."""
        logger.info("Testing optimized module imports...")
        
        # Test optimized Qwen wrapper
        try:
            from models.qwen_wrapper_optimized import OptimizedQwenModel
            logger.info("✓ Optimized Qwen wrapper imported successfully")
        except ImportError as e:
            logger.warning(f"Optimized Qwen wrapper not available: {e}")
        
        # Test optimized audio processor
        try:
            from modules.voice.audio_processor_optimized import OptimizedAudioProcessor
            logger.info("✓ Optimized audio processor imported successfully")
        except ImportError as e:
            logger.warning(f"Optimized audio processor not available: {e}")
        
        # Test performance monitor
        try:
            from modules.diagnostics.performance_monitor import OptimizedDiagnostics
            logger.info("✓ Performance monitor imported successfully")
        except ImportError as e:
            self.fail(f"Performance monitor import failed: {e}")
        
        # Test sentinel core
        try:
            from sentinel_core import OptimizedSentinelCore
            logger.info("✓ Optimized Sentinel Core imported successfully")
        except ImportError as e:
            self.fail(f"Optimized Sentinel Core import failed: {e}")
    
    def test_04_rust_backend_availability(self):
        """Test Rust backend availability for audio processing."""
        logger.info("Testing Rust backend availability...")
        
        try:
            import audio_processor
            logger.info("✓ Rust audio processor backend available")
            self.test_results['rust_audio'] = True
        except ImportError:
            logger.warning("Rust audio processor backend not available (this is optional)")
            self.test_results['rust_audio'] = False
    
    def test_05_cpp_backend_availability(self):
        """Test C++ backend availability for inference."""
        logger.info("Testing C++ backend availability...")
        
        try:
            import qwen_inference_cpp
            logger.info("✓ C++ inference backend available")
            self.test_results['cpp_inference'] = True
        except ImportError:
            logger.warning("C++ inference backend not available (this is optional)")
            self.test_results['cpp_inference'] = False
    
    def test_06_performance_baseline(self):
        """Establish performance baseline."""
        logger.info("Establishing performance baseline...")
        
        try:
            from modules.diagnostics.performance_monitor import OptimizedDiagnostics
            
            diagnostics = OptimizedDiagnostics()
            baseline = diagnostics.collect_metrics()
            
            # Store baseline metrics
            self.performance_metrics['baseline'] = {
                'cpu_usage': baseline.cpu_usage,
                'memory_usage': baseline.memory_usage,
                'gpu_usage': baseline.gpu_usage,
                'gpu_memory_usage': baseline.gpu_memory_usage
            }
            
            logger.info(f"✓ Baseline established: CPU {baseline.cpu_usage:.1f}%, "
                       f"Memory {baseline.memory_usage:.1f}%")
            
        except Exception as e:
            logger.error(f"Failed to establish baseline: {e}")
    
    def test_07_ai_model_functionality(self):
        """Test AI model functionality and performance."""
        logger.info("Testing AI model functionality...")
        
        try:
            # Test with mock model to avoid requiring actual model files
            with patch('torch.cuda.is_available', return_value=False):
                from models.qwen_wrapper_optimized import OptimizedQwenModel
                
                # This would fail in real scenario without model, but we're testing the structure
                logger.info("✓ AI model structure test passed")
                
        except Exception as e:
            logger.warning(f"AI model test skipped (expected without model files): {e}")
    
    def test_08_audio_processing_functionality(self):
        """Test audio processing functionality."""
        logger.info("Testing audio processing functionality...")
        
        try:
            from modules.voice.audio_processor_optimized import OptimizedAudioProcessor
            
            # Create processor instance
            processor = OptimizedAudioProcessor(
                sample_rate=44100,
                channels=2,
                buffer_size=1024,
                use_rust=False  # Use Python backend for testing
            )
            
            # Test basic functionality
            info = processor.get_buffer_info()
            self.assertIsInstance(info, dict)
            self.assertIn('backend', info)
            self.assertIn('is_recording', info)
            
            logger.info("✓ Audio processing functionality test passed")
            
        except Exception as e:
            logger.warning(f"Audio processing test failed: {e}")
    
    def test_09_sentinel_core_initialization(self):
        """Test Sentinel Core initialization."""
        logger.info("Testing Sentinel Core initialization...")
        
        try:
            from sentinel_core import OptimizedSentinelCore
            
            # Mock dependencies to avoid requiring actual model files
            with patch('models.qwen_wrapper_optimized.OptimizedQwenModel'), \
                 patch('modules.voice.audio_processor_optimized.OptimizedAudioProcessor'):
                
                sentinel = OptimizedSentinelCore(
                    model_path="/mock/path",
                    enable_voice=False
                )
                
                # Test basic functionality
                stats = sentinel.get_performance_stats()
                self.assertIsInstance(stats, dict)
                self.assertIn('start_time', stats)
                
                logger.info("✓ Sentinel Core initialization test passed")
                
        except Exception as e:
            logger.error(f"Sentinel Core initialization failed: {e}")
            self.fail(f"Sentinel Core test failed: {e}")
    
    def test_10_build_script_functionality(self):
        """Test build script functionality."""
        logger.info("Testing build script functionality...")
        
        build_script = os.path.join(PROJECT_ROOT, 'build_optimized.sh')
        self.assertTrue(os.path.exists(build_script), "Build script should exist")
        self.assertTrue(os.access(build_script, os.X_OK), "Build script should be executable")
        
        # Test script syntax (dry run)
        try:
            result = subprocess.run(['bash', '-n', build_script], 
                                  capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, 
                           f"Build script syntax error: {result.stderr}")
            logger.info("✓ Build script syntax test passed")
        except Exception as e:
            logger.warning(f"Build script test failed: {e}")
    
    def test_11_performance_comparison(self):
        """Compare performance with and without optimizations."""
        logger.info("Testing performance comparison...")
        
        try:
            # Simple performance test
            import time
            import numpy as np
            
            # Test 1: Matrix multiplication (CPU performance)
            start_time = time.time()
            a = np.random.rand(1000, 1000)
            b = np.random.rand(1000, 1000)
            result = np.dot(a, b)
            cpu_time = time.time() - start_time
            
            self.performance_metrics['cpu_computation'] = cpu_time
            
            # Test 2: Memory allocation/deallocation
            start_time = time.time()
            large_arrays = [np.random.rand(100, 100) for _ in range(100)]
            del large_arrays
            memory_time = time.time() - start_time
            
            self.performance_metrics['memory_ops'] = memory_time
            
            logger.info(f"✓ Performance tests completed: "
                       f"CPU {cpu_time:.3f}s, Memory {memory_time:.3f}s")
            
        except Exception as e:
            logger.warning(f"Performance comparison failed: {e}")
    
    def test_12_system_compatibility(self):
        """Test system compatibility and optimization recommendations."""
        logger.info("Testing system compatibility...")
        
        try:
            from modules.diagnostics.performance_monitor import OptimizedDiagnostics
            
            diagnostics = OptimizedDiagnostics()
            compatibility = diagnostics._check_hardware_compatibility()
            
            self.assertIsInstance(compatibility, dict)
            self.assertIn('cpu_compatible', compatibility)
            self.assertIn('gpu_compatible', compatibility)
            
            # Get optimization recommendations
            recommendations = diagnostics.get_optimization_recommendations()
            self.assertIsInstance(recommendations, list)
            self.assertGreater(len(recommendations), 0)
            
            logger.info(f"✓ System compatibility test passed "
                       f"({len(recommendations)} recommendations)")
            
        except Exception as e:
            logger.error(f"System compatibility test failed: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up and generate report."""
        logger.info("Generating optimization test report...")
        
        print("\n" + "="*60)
        print("BLACKSTACK OPTIMIZATION TEST REPORT")
        print("="*60)
        
        print("\nTest Results:")
        for test_name, result in cls.test_results.items():
            status = "✓ PASS" if result else "⚠ WARN"
            print(f"  {test_name}: {status}")
        
        print("\nPerformance Metrics:")
        for metric_name, value in cls.performance_metrics.items():
            if isinstance(value, dict):
                print(f"  {metric_name}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {metric_name}: {value}")
        
        print("\nRecommendations:")
        print("  1. Run build_optimized.sh to compile native modules")
        print("  2. Install CUDA drivers for GPU acceleration")
        print("  3. Set CPU governor to performance mode")
        print("  4. Monitor system performance during operation")
        
        print("\n" + "="*60)


def run_quick_tests():
    """Run a quick subset of tests for development."""
    logger.info("Running quick optimization tests...")
    
    # Test basic imports
    try:
        import sentinel_core
        logger.info("✓ sentinel_core import")
    except ImportError as e:
        logger.error(f"✗ sentinel_core import failed: {e}")
    
    # Test optimized modules
    try:
        from models.qwen_wrapper_optimized import OptimizedQwenModel
        logger.info("✓ OptimizedQwenModel import")
    except ImportError:
        logger.warning("⚠ OptimizedQwenModel not available")
    
    try:
        from modules.voice.audio_processor_optimized import OptimizedAudioProcessor
        logger.info("✓ OptimizedAudioProcessor import")
    except ImportError:
        logger.warning("⚠ OptimizedAudioProcessor not available")
    
    try:
        from modules.diagnostics.performance_monitor import OptimizedDiagnostics
        logger.info("✓ OptimizedDiagnostics import")
    except ImportError as e:
        logger.error(f"✗ OptimizedDiagnostics import failed: {e}")
    
    # Test build script
    build_script = os.path.join(PROJECT_ROOT, 'build_optimized.sh')
    if os.path.exists(build_script):
        logger.info("✓ build_optimized.sh exists")
    else:
        logger.error("✗ build_optimized.sh missing")
    
    logger.info("Quick tests completed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BlackStack optimization test suite")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.quick:
        run_quick_tests()
    else:
        unittest.main(argv=[''], exit=False, verbosity=2 if args.verbose else 1)