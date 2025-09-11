/**
 * Python bindings for the optimized Qwen inference engine
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "qwen_inference.hpp"

namespace py = pybind11;

PYBIND11_MODULE(qwen_inference_cpp, m) {
    m.doc() = "High-performance Qwen inference engine for BlackStack";
    
    py::class_<QwenInferenceEngine>(m, "QwenInferenceEngine")
        .def(py::init<const std::string&, torch::Device>(),
             py::arg("model_path"), py::arg("device") = torch::kCUDA,
             "Initialize the inference engine")
        .def("generate_sync", &QwenInferenceEngine::generate_sync,
             py::arg("prompt"), py::arg("max_tokens") = 1024,
             py::arg("temperature") = 0.6f, py::arg("top_p") = 0.95f,
             py::arg("top_k") = 20, py::arg("do_sample") = true,
             "Generate text synchronously")
        .def("generate_batch", &QwenInferenceEngine::generate_batch,
             py::arg("prompts"), py::arg("max_tokens") = 1024,
             py::arg("temperature") = 0.6f, py::arg("top_p") = 0.95f,
             py::arg("top_k") = 20, py::arg("do_sample") = true,
             "Generate text for multiple prompts")
        .def("load_model", &QwenInferenceEngine::load_model,
             py::arg("model_path"), "Load a model from file")
        .def("unload_model", &QwenInferenceEngine::unload_model,
             "Unload the current model")
        .def("is_model_loaded", &QwenInferenceEngine::is_model_loaded,
             "Check if a model is loaded")
        .def("get_total_requests", &QwenInferenceEngine::get_total_requests,
             "Get total number of processed requests")
        .def("get_average_latency", &QwenInferenceEngine::get_average_latency,
             "Get average latency in milliseconds")
        .def("get_queue_size", &QwenInferenceEngine::get_queue_size,
             "Get current queue size")
        .def("get_available_memory", &QwenInferenceEngine::get_available_memory,
             "Get available GPU memory")
        .def("set_max_sequence_length", &QwenInferenceEngine::set_max_sequence_length,
             py::arg("length"), "Set maximum sequence length")
        .def("optimize_for_throughput", &QwenInferenceEngine::optimize_for_throughput,
             "Optimize settings for maximum throughput")
        .def("optimize_for_latency", &QwenInferenceEngine::optimize_for_latency,
             "Optimize settings for minimum latency");
    
    py::class_<MemoryManager>(m, "MemoryManager")
        .def(py::init<size_t>(), py::arg("total_vram") = 12ULL * 1024 * 1024 * 1024,
             "Initialize memory manager")
        .def("get_available_memory", &MemoryManager::get_available_memory,
             "Get available memory in bytes")
        .def("clear_cache", &MemoryManager::clear_cache,
             "Clear memory cache");
}