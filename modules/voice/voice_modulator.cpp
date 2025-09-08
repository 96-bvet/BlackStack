// modules/voice_modulator.cpp
#include <sndfile.h>
#include <portaudio.h>
#include <iostream>
#include <cmath>

#define FRAMES_PER_BUFFER 512

// Simple pitch shift placeholder (scales amplitude, not true pitch)
void modulate_voice(const char* input_path, const char* output_path, float pitch_shift) {
    SF_INFO sfinfo;
    SNDFILE* infile = sf_open(input_path, SFM_READ, &sfinfo);
    if (!infile) {
        std::cerr << "Failed to open input file\n";
        return;
    }

    float* buffer = new float[sfinfo.frames * sfinfo.channels];
    sf_readf_float(infile, buffer, sfinfo.frames);
    sf_close(infile);

    // Apply naive pitch shift (amplitude scaling placeholder)
    for (int i = 0; i < sfinfo.frames * sfinfo.channels; ++i) {
        buffer[i] *= pitch_shift;
    }

    SNDFILE* outfile = sf_open(output_path, SFM_WRITE, &sfinfo);
    if (!outfile) {
        std::cerr << "Failed to open output file\n";
        delete[] buffer;
        return;
    }

    sf_writef_float(outfile, buffer, sfinfo.frames);
    sf_close(outfile);
    delete[] buffer;

    std::cout << "Voice modulation complete → " << output_path << "\n";
}
