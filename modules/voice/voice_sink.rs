// modules/voice_sink.rs
use rodio::{Decoder, OutputStream, Sink};
use std::fs::File;

pub fn play_audio(path: &str) {
    let (_stream, handle) = OutputStream::try_default().unwrap();
    let sink = Sink::try_new(&handle).unwrap();
    let file = File::open(path).unwrap();
    let source = Decoder::new(std::io::BufReader::new(file)).unwrap();
    sink.append(source);
    sink.sleep_until_end();
}
