"""Unit tests for large-file chunking and timestamp merge.

These tests are pure/fast and do not call OpenAI or ffmpeg.
"""

from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.audio_preprocessor import (
    estimate_bytes_per_second,
    plan_chunk_duration_seconds,
    plan_nominal_chunk_seconds_for_max_duration,
)
from services.transcript_merger import merge_chunk_segments, merge_transcripts


def test_plan_chunk_duration_seconds_respects_target_budget():
    target_bytes = 24 * 1024 * 1024
    bitrate_kbps = 48
    overlap_sec = 0.8

    nominal = plan_chunk_duration_seconds(
        target_upload_bytes=target_bytes,
        audio_bitrate_kbps=bitrate_kbps,
        chunk_overlap_sec=overlap_sec,
        safety_factor=0.95,
        min_chunk_sec=30,
    )

    assert nominal >= 30

    # Worst-case chunk includes leading overlap
    bytes_per_sec = estimate_bytes_per_second(bitrate_kbps)
    worst_duration = nominal + overlap_sec
    estimated = worst_duration * bytes_per_sec

    assert estimated < target_bytes


def test_plan_nominal_chunk_seconds_for_max_duration_respects_overlap_budget():
    max_total_sec = 1400
    overlap_sec = 0.8

    nominal = plan_nominal_chunk_seconds_for_max_duration(
        max_total_duration_sec=max_total_sec,
        chunk_overlap_sec=overlap_sec,
        safety_factor=0.98,
        min_chunk_sec=30,
    )

    # Worst-case chunk (after the first) includes leading overlap.
    assert (nominal + overlap_sec) <= (max_total_sec * 0.98) + 1e-6


def test_plan_nominal_chunk_seconds_for_max_duration_works_for_900s_guard():
    # Default reliability guard in AudioPreprocessor is 900 seconds.
    max_total_sec = 900
    overlap_sec = 0.8

    nominal = plan_nominal_chunk_seconds_for_max_duration(
        max_total_duration_sec=max_total_sec,
        chunk_overlap_sec=overlap_sec,
        safety_factor=0.98,
        min_chunk_sec=30,
    )

    assert (nominal + overlap_sec) <= (max_total_sec * 0.98) + 1e-6


def test_merge_chunk_segments_applies_offset_and_drops_leading_overlap():
    segs = [
        {"start": 0.0, "end": 0.5, "text": "overlap"},
        {"start": 0.5, "end": 1.2, "text": "keep"},
    ]

    merged = merge_chunk_segments(
        segs,
        start_offset_sec=10.0,
        drop_leading_overlap_sec=0.8,
    )

    # First segment ends at 0.5 <= 0.8, should be dropped
    assert len(merged) == 1
    assert merged[0]["text"] == "keep"
    assert merged[0]["start"] == 10.5
    assert merged[0]["end"] == 11.2


def test_merge_transcripts_offsets_segments_and_is_monotonic():
    chunks = [
        (
            "hello",
            [{"start": 0.0, "end": 1.0, "text": "hello"}],
            0.0,
        ),
        (
            "world",
            [
                {"start": 0.0, "end": 0.7, "text": "overlap"},
                {"start": 0.7, "end": 1.5, "text": "world"},
            ],
            9.2,
        ),
    ]

    merged = merge_transcripts(chunks, overlap_sec=0.8)

    # Overlap segment should be removed from second chunk
    assert [s["text"] for s in merged.segments] == ["hello", "world"]

    # Offsets applied
    assert merged.segments[0]["start"] == 0.0
    assert merged.segments[1]["start"] == 9.9

    # Monotonic
    assert merged.segments[0]["end"] <= merged.segments[1]["start"]
