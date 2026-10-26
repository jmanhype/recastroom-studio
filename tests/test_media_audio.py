# SPDX-License-Identifier: MIT
"""Local speech regression: export must not invent channels or attenuate audio."""
from array import array
import hashlib
import json
import math
from pathlib import Path
import subprocess

import pytest

from openjutsu.media import make_side_by_side, restore_source_audio


SPEECH = Path(__file__).parent / "fixtures" / "export_speech.wav"
# Declared before implementation: AAC is lossy, but must not change loudness
# materially, lose a channel, shift speech, or change decoded sample count.
MAX_RMS_DELTA_DB = 1.0
MIN_ZERO_LAG_CORRELATION = 0.98
MIN_PEAK = 1e-4


def probe(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)
    ])
    return json.loads(result)


def pcm(path):
    result = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ar", "48000",
        "-f", "f32le", "-"
    ])
    samples = array("f")
    samples.frombytes(result)
    return samples


def make_speech_source(path, layout):
    if layout == "mono":
        graph = "[1:a]anull[speech]"
    elif layout == "stereo":
        graph = "[1:a]pan=stereo|c0=c0|c1=0.75*c0[speech]"
    else:
        # LFE is deliberately band-limited; testing full-range speech in an
        # LFE channel would mistake the AAC encoder's low-pass for data loss.
        graph = (
            "[1:a]pan=5.1|FL=c0|FR=c0|FC=c0|LFE=c0|BL=c0|BR=c0,"
            "lowpass=f=120:c=LFE[speech]"
        )
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
        "color=c=navy:s=160x96:r=24:d=2", "-i", str(SPEECH),
        "-filter_complex", graph, "-map", "0:v:0", "-map", "[speech]",
        "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000", str(path)
    ], check=True)


@pytest.mark.parametrize("layout,count", [("mono", 1), ("stereo", 2), ("5.1", 6)])
def test_exports_preserve_speech_layout_and_loudness(tmp_path, layout, count):
    source = tmp_path / "source.mp4"
    final = tmp_path / "final.mp4"
    comparison = tmp_path / "comparison.mp4"
    make_speech_source(source, layout)
    restore_source_audio(source, source, final)
    make_side_by_side(source, final, comparison, width=160, height=96)
    source_audio = next(s for s in probe(source)["streams"] if s["codec_type"] == "audio")
    assert source_audio["channels"] == count
    assert source_audio["channel_layout"] == layout
    original = pcm(source)
    metrics = {"source_layout": layout, "source_channels": count, "outputs": {}}
    for output in (final, comparison):
        audio = next(s for s in probe(output)["streams"] if s["codec_type"] == "audio")
        assert audio["channels"] == count
        assert audio["channel_layout"] == layout
        restored = pcm(output)
        assert len(original) == len(restored)
        channel_metrics = []
        for channel in range(count):
            x, y = original[channel::count], restored[channel::count]
            xx, yy = sum(v*v for v in x), sum(v*v for v in y)
            xy = sum(v*w for v, w in zip(x, y))
            source_peak, output_peak = max(map(abs, x)), max(map(abs, y))
            assert min(source_peak, output_peak) > MIN_PEAK
            delta = 10 * math.log10(yy / xx)
            correlation = xy / math.sqrt(xx * yy)
            assert abs(delta) <= MAX_RMS_DELTA_DB
            assert correlation >= MIN_ZERO_LAG_CORRELATION
            channel_metrics.append({
                "channel": channel, "samples": len(x),
                "source_peak": source_peak, "output_peak": output_peak,
                "source_rms": math.sqrt(xx/len(x)), "output_rms": math.sqrt(yy/len(y)),
                "rms_delta_db": delta, "zero_lag_correlation": correlation,
                "gain": xy/xx,
            })
        metrics["outputs"][output.name] = {
            "layout": audio["channel_layout"], "channels": audio["channels"],
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "channel_metrics": channel_metrics,
        }
    (tmp_path / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
