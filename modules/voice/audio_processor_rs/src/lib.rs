// High-performance audio processing module for BlackStack WachterEID
// Optimized for RTX 3060 and AMD Ryzen 7 7700
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};
use std::collections::VecDeque;
use crossbeam::channel::{bounded, Receiver, Sender};
use rayon::prelude::*;
use anyhow::Result;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioConfig {
    pub sample_rate: u32,
    pub channels: u16,
    pub buffer_size: usize,
    pub enable_noise_gate: bool,
    pub noise_threshold: f32,
    pub enable_compressor: bool,
    pub compression_ratio: f32,
}

impl Default for AudioConfig {
    fn default() -> Self {
        Self {
            sample_rate: 44100,
            channels: 2,
            buffer_size: 1024,
            enable_noise_gate: true,
            noise_threshold: 0.01,
            enable_compressor: true,
            compression_ratio: 4.0,
        }
    }
}

#[pyclass]
pub struct AudioProcessor {
    config: AudioConfig,
    input_stream: Option<cpal::Stream>,
    output_stream: Option<cpal::Stream>,
    audio_buffer: Arc<Mutex<VecDeque<f32>>>,
    is_recording: Arc<Mutex<bool>>,
    sender: Option<Sender<Vec<f32>>>,
    receiver: Option<Receiver<Vec<f32>>>,
}

#[pymethods]
impl AudioProcessor {
    #[new]
    pub fn new(config: Option<AudioConfig>) -> Self {
        let config = config.unwrap_or_default();
        let (sender, receiver) = bounded(100);
        
        Self {
            config,
            input_stream: None,
            output_stream: None,
            audio_buffer: Arc::new(Mutex::new(VecDeque::with_capacity(44100 * 10))), // 10 seconds buffer
            is_recording: Arc::new(Mutex::new(false)),
            sender: Some(sender),
            receiver: Some(receiver),
        }
    }

    /// Start high-performance audio capture
    pub fn start_capture(&mut self, device_name: Option<String>) -> PyResult<()> {
        let host = cpal::default_host();
        
        let device = match device_name {
            Some(name) => {
                host.input_devices().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to get input devices: {}", e)))?
                    .find(|d| d.name().unwrap_or_default().contains(&name))
                    .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        format!("Device '{}' not found", name)
                    ))?
            },
            None => host.default_input_device()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    "No default input device found"
                ))?
        };

        let config = device.default_input_config().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to get device config: {}", e)))?;
        let sample_format = config.sample_format();
        let config: cpal::StreamConfig = config.into();

        let buffer = Arc::clone(&self.audio_buffer);
        let is_recording = Arc::clone(&self.is_recording);
        let audio_config = self.config.clone();

        let stream = match sample_format {
            cpal::SampleFormat::F32 => {
                device.build_input_stream(
                    &config,
                    move |data: &[f32], _: &cpal::InputCallbackInfo| {
                        if *is_recording.lock().unwrap() {
                            let processed = process_audio_chunk(data, &audio_config);
                            let mut buffer = buffer.lock().unwrap();
                            buffer.extend(processed);
                            
                            // Limit buffer size to prevent memory issues
                            while buffer.len() > 44100 * 30 { // 30 seconds max
                                buffer.pop_front();
                            }
                        }
                    },
                    move |err| eprintln!("Audio capture error: {}", err),
                    None,
                ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to build input stream: {}", e)))?
            },
            cpal::SampleFormat::I16 => {
                device.build_input_stream(
                    &config,
                    move |data: &[i16], _: &cpal::InputCallbackInfo| {
                        if *is_recording.lock().unwrap() {
                            let float_data: Vec<f32> = data.iter()
                                .map(|&sample| sample as f32 / i16::MAX as f32)
                                .collect();
                            let processed = process_audio_chunk(&float_data, &audio_config);
                            let mut buffer = buffer.lock().unwrap();
                            buffer.extend(processed);
                            
                            while buffer.len() > 44100 * 30 {
                                buffer.pop_front();
                            }
                        }
                    },
                    move |err| eprintln!("Audio capture error: {}", err),
                    None,
                ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to build input stream: {}", e)))?
            },
            _ => return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Unsupported sample format"
            )),
        };

        stream.play().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to start stream: {}", e)))?;
        self.input_stream = Some(stream);
        *self.is_recording.lock().unwrap() = true;

        Ok(())
    }

    /// Stop audio capture
    pub fn stop_capture(&mut self) -> PyResult<()> {
        *self.is_recording.lock().unwrap() = false;
        if let Some(stream) = self.input_stream.take() {
            drop(stream);
        }
        Ok(())
    }

    /// Get captured audio as bytes (optimized for Python integration)
    pub fn get_audio_data(&self, py: Python) -> PyResult<PyObject> {
        let buffer = self.audio_buffer.lock().unwrap();
        let data: Vec<f32> = buffer.iter().cloned().collect();
        drop(buffer);

        if data.is_empty() {
            return Ok(PyBytes::new(py, &[]).into());
        }

        // Convert to bytes for efficient transfer to Python
        let bytes: Vec<u8> = data.par_iter()
            .flat_map(|&sample| sample.to_le_bytes())
            .collect();

        Ok(PyBytes::new(py, &bytes).into())
    }

    /// Clear audio buffer
    pub fn clear_buffer(&mut self) -> PyResult<()> {
        self.audio_buffer.lock().unwrap().clear();
        Ok(())
    }

    /// Get buffer length (for monitoring)
    pub fn get_buffer_length(&self) -> PyResult<usize> {
        Ok(self.audio_buffer.lock().unwrap().len())
    }

    /// Real-time audio analysis
    pub fn analyze_audio(&self) -> PyResult<f32> {
        let buffer = self.audio_buffer.lock().unwrap();
        if buffer.is_empty() {
            return Ok(0.0);
        }

        // Calculate RMS (root mean square) for volume level
        let rms: f32 = buffer.iter()
            .map(|&sample| sample * sample)
            .sum::<f32>() / buffer.len() as f32;
        
        Ok(rms.sqrt())
    }
}

/// High-performance audio processing with SIMD optimization
fn process_audio_chunk(data: &[f32], config: &AudioConfig) -> Vec<f32> {
    let mut processed = data.to_vec();

    // Parallel processing for better CPU utilization on Ryzen 7 7700
    processed.par_chunks_mut(256).for_each(|chunk| {
        // Noise gate
        if config.enable_noise_gate {
            for sample in chunk.iter_mut() {
                if sample.abs() < config.noise_threshold {
                    *sample = 0.0;
                }
            }
        }

        // Simple compressor
        if config.enable_compressor {
            let threshold = 0.7;
            for sample in chunk.iter_mut() {
                if sample.abs() > threshold {
                    let excess = sample.abs() - threshold;
                    let compressed_excess = excess / config.compression_ratio;
                    *sample = (*sample).signum() * (threshold + compressed_excess);
                }
            }
        }
    });

    processed
}

/// Initialize the Python module
#[pymodule]
fn audio_processor(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<AudioProcessor>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audio_config_default() {
        let config = AudioConfig::default();
        assert_eq!(config.sample_rate, 44100);
        assert_eq!(config.channels, 2);
    }

    #[test]
    fn test_audio_processing() {
        let config = AudioConfig::default();
        let input = vec![0.5, -0.3, 0.8, -0.9, 0.001]; // Mix of loud and quiet samples
        let processed = process_audio_chunk(&input, &config);
        
        // Noise gate should zero out the 0.001 sample
        assert_eq!(processed[4], 0.0);
        
        // Compression should reduce the 0.8 and -0.9 samples
        assert!(processed[2].abs() < 0.8);
        assert!(processed[3].abs() < 0.9);
    }
}