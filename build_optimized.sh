#!/bin/bash

# Build script for BlackStack optimization modules
# Optimized for RTX 3060 and AMD Ryzen 7 7700

set -e

echo "Building BlackStack optimization modules..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check for Rust
    if command -v rustc &> /dev/null; then
        RUST_VERSION=$(rustc --version)
        print_status "Found Rust: $RUST_VERSION"
    else
        print_error "Rust not found. Please install Rust from https://rustup.rs/"
        exit 1
    fi
    
    # Check for CMake
    if command -v cmake &> /dev/null; then
        CMAKE_VERSION=$(cmake --version | head -n1)
        print_status "Found CMake: $CMAKE_VERSION"
    else
        print_error "CMake not found. Please install CMake >= 3.18"
        exit 1
    fi
    
    # Check for Python development headers
    if python3-config --includes &> /dev/null; then
        print_status "Found Python development headers"
    else
        print_warning "Python development headers not found. Install python3-dev or python3-devel"
    fi
    
    # Check for CUDA (optional)
    if command -v nvcc &> /dev/null; then
        CUDA_VERSION=$(nvcc --version | grep "release" | cut -d" " -f6)
        print_status "Found CUDA: $CUDA_VERSION"
        export CUDA_AVAILABLE=1
    else
        print_warning "CUDA not found. GPU acceleration will be limited."
        export CUDA_AVAILABLE=0
    fi
}

# Build Rust audio processor
build_rust_audio() {
    print_status "Building Rust audio processor..."
    
    cd modules/voice/audio_processor_rs
    
    # Set optimization flags for Ryzen 7 7700
    export RUSTFLAGS="-C target-cpu=native -C opt-level=3"
    
    # Build the library
    if cargo build --release; then
        print_status "Rust audio processor built successfully"
        
        # Copy the built library to the Python modules directory
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            LIB_EXT="so"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            LIB_EXT="dylib"
        else
            LIB_EXT="dll"
        fi
        
        LIB_FILE="target/release/libaudio_processor.$LIB_EXT"
        if [ -f "$LIB_FILE" ]; then
            cp "$LIB_FILE" "../audio_processor.$LIB_EXT"
            print_status "Copied library to modules directory"
        fi
    else
        print_error "Failed to build Rust audio processor"
        exit 1
    fi
    
    cd ../../..
}

# Build C++ inference engine
build_cpp_inference() {
    print_status "Building C++ inference engine..."
    
    cd models/qwen_inference_cpp
    
    # Create build directory
    mkdir -p build
    cd build
    
    # Configure with CMake
    CMAKE_FLAGS="-DCMAKE_BUILD_TYPE=Release"
    CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_CXX_FLAGS_RELEASE='-O3 -march=native -mtune=native -DNDEBUG'"
    
    if [ "$CUDA_AVAILABLE" = "1" ]; then
        CMAKE_FLAGS="$CMAKE_FLAGS -DWITH_CUDA=ON"
        print_status "Building with CUDA support"
    else
        CMAKE_FLAGS="$CMAKE_FLAGS -DWITH_CUDA=OFF"
        print_warning "Building without CUDA support"
    fi
    
    if cmake $CMAKE_FLAGS ..; then
        print_status "CMake configuration successful"
    else
        print_error "CMake configuration failed"
        exit 1
    fi
    
    # Build with optimal parallelization for Ryzen 7 7700 (16 threads)
    if make -j$(nproc); then
        print_status "C++ inference engine built successfully"
        
        # Copy the built library
        if [ -f "qwen_inference_cpp*.so" ]; then
            cp qwen_inference_cpp*.so ../../
            print_status "Copied library to models directory"
        fi
    else
        print_error "Failed to build C++ inference engine"
        exit 1
    fi
    
    cd ../../..
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing optimized Python dependencies..."
    
    # Install with pip optimizations
    pip install --upgrade pip setuptools wheel
    
    # Install PyTorch with CUDA support if available
    if [ "$CUDA_AVAILABLE" = "1" ]; then
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        print_status "Installed PyTorch with CUDA support"
    else
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        print_warning "Installed PyTorch CPU-only version"
    fi
    
    # Install other dependencies
    pip install -r requirements.txt
    
    print_status "Python dependencies installed"
}

# Performance optimization
apply_system_optimizations() {
    print_status "Applying system optimizations..."
    
    # CPU frequency scaling (requires root)
    if [ "$EUID" -eq 0 ]; then
        echo "performance" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
        print_status "Set CPU governor to performance mode"
    else
        print_warning "Root privileges needed for CPU optimization. Run: sudo cpupower frequency-set -g performance"
    fi
    
    # GPU optimizations (if NVIDIA)
    if command -v nvidia-smi &> /dev/null; then
        # Set maximum performance mode
        nvidia-smi -pm 1 2>/dev/null || print_warning "Could not set GPU persistence mode"
        nvidia-smi -ac 1215,1860 2>/dev/null || print_warning "Could not set GPU clocks"
        print_status "Applied GPU optimizations"
    fi
    
    # Memory optimizations
    echo 1 > /proc/sys/vm/drop_caches 2>/dev/null || print_warning "Could not clear memory caches"
}

# Test the built modules
test_modules() {
    print_status "Testing built modules..."
    
    # Test Python imports
    python3 -c "
try:
    import torch
    print('✓ PyTorch imported successfully')
    if torch.cuda.is_available():
        print(f'✓ CUDA available: {torch.cuda.get_device_name(0)}')
    else:
        print('! CUDA not available')
except ImportError as e:
    print(f'✗ PyTorch import failed: {e}')

try:
    import audio_processor
    print('✓ Rust audio processor imported successfully')
except ImportError:
    print('! Rust audio processor not available')

try:
    import qwen_inference_cpp
    print('✓ C++ inference engine imported successfully')
except ImportError:
    print('! C++ inference engine not available')

# Test optimized modules
try:
    from models.qwen_wrapper_optimized import OptimizedQwenModel
    print('✓ Optimized Qwen wrapper available')
except ImportError as e:
    print(f'! Optimized Qwen wrapper failed: {e}')

try:
    from modules.voice.audio_processor_optimized import OptimizedAudioProcessor
    print('✓ Optimized audio processor available')
except ImportError as e:
    print(f'! Optimized audio processor failed: {e}')
"
}

# Main build process
main() {
    print_status "Starting BlackStack optimization build process"
    print_status "Target hardware: RTX 3060 + AMD Ryzen 7 7700"
    
    check_dependencies
    install_python_deps
    build_rust_audio
    build_cpp_inference
    apply_system_optimizations
    test_modules
    
    print_status "Build process completed successfully!"
    echo
    print_status "Optimized modules built for maximum performance on your hardware:"
    echo "  • Rust audio processor: Real-time audio processing with minimal latency"
    echo "  • C++ inference engine: GPU-optimized AI inference with efficient memory management"
    echo "  • Optimized Python wrappers: Seamless integration with existing codebase"
    echo
    print_status "Performance tips:"
    echo "  • Run with: sudo cpupower frequency-set -g performance"
    echo "  • Monitor GPU memory: nvidia-smi -l 1"
    echo "  • Use batch processing for maximum throughput"
}

# Run main function
main "$@"