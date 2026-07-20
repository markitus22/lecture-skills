#!/usr/bin/env python3
"""Clean a YouTube lecture transcript into plain readable text.

Handles: WebVTT (.vtt), SubRip (.srt), timestamped plain text
(e.g. "0:00 hello" or "[00:12] hello"), and already-plain text.

Fixes the two problems raw captions have:
1. Timestamps and cue metadata mixed into the text.
2. Rolling-window duplication in auto-captions, where each cue
   repeats the tail of the previous one.

Usage:
    python3 clean_transcript.py INPUT [-o OUTPUT]

Prints stats (word count, estimated minutes) to stderr so the
caller can decide whether to segment the document.
"""

import argparse
import html
import re
import sys

TS_LINE = re.compile(
    r"^\s*(\d{1,2}:)?\d{1,2}:\d{2}([.,]\d{1,3})?\s*-->\s*(\d{1,2}:)?\d{1,2}:\d{2}([.,]\d{1,3})?"
)
LEADING_TS = re.compile(r"^\s*[\[\(]?\s*(\d{1,2}:)?\d{1,2}:\d{2}([.,]\d{1,3})?\s*[\]\)]?\s+")
INLINE_TAG = re.compile(r"<[^>]+>")  # vtt word-timing tags like <00:00:01.000><c>
CUE_SETTINGS = re.compile(r"\b(align|position|size|line):\S+", re.I)
MUSIC = re.compile(r"\[(music|applause|laughter|inaudible|silence)[^\]]*\]", re.I)

WORDS_PER_MIN = 150


def detect_and_extract(text: str) -> list[str]:
    """Return caption lines with timestamps/metadata removed."""
    lines = text.splitlines()
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.upper().startswith(("WEBVTT", "NOTE ", "NOTE\t", "STYLE", "REGION", "Kind:", "KIND:", "Language:", "LANGUAGE:")):
            continue
        if TS_LINE.match(s):
            continue
        if s.isdigit():  # srt cue numbers
            continue
        if CUE_SETTINGS.search(s) and "-->" in s:
            continue
        s = LEADING_TS.sub("", s)
        s = INLINE_TAG.sub("", s)
        s = MUSIC.sub("", s)
        s = html.unescape(s).strip()
        if s:
            out.append(s)
    return out


def dedupe_rolling(lines: list[str]) -> list[str]:
    """Collapse the overlap pattern of YouTube auto-captions.

    Auto-caption cues often appear twice: once as the second line of
    cue N and again as the first line of cue N+1. Also, each cue can
    end with the words the next cue starts with. Handle both:
    exact-duplicate consecutive lines, and word-level suffix/prefix
    overlap between consecutive lines.
    """
    result: list[str] = []
    for line in lines:
        if result and line == result[-1]:
            continue
        if result:
            prev_words = result[-1].split()
            cur_words = line.split()
            max_k = min(len(prev_words), len(cur_words), 12)
            overlap = 0
            for k in range(max_k, 0, -1):
                if prev_words[-k:] == cur_words[:k]:
                    overlap = k
                    break
            if overlap:
                line = " ".join(cur_words[overlap:])
                if not line:
                    continue
        result.append(line)
    return result


def join_text(lines: list[str]) -> str:
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    # Break into paragraphs at sentence boundaries, ~90 words each,
    # purely for readability of the intermediate file.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    paras, cur, count = [], [], 0
    for s in sentences:
        cur.append(s)
        count += len(s.split())
        if count >= 90:
            paras.append(" ".join(cur))
            cur, count = [], 0
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(paras)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="transcript file (vtt/srt/txt)")
    ap.add_argument("-o", "--output", help="write cleaned text here (default: stdout)")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8", errors="replace") as f:
        raw = f.read()

    lines = detect_and_extract(raw)
    lines = dedupe_rolling(lines)
    cleaned = join_text(lines)

    words = len(cleaned.split())
    minutes = round(words / WORDS_PER_MIN)
    sys.stderr.write(f"words={words} est_minutes={minutes}\n")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(cleaned + "\n")
    else:
        print(cleaned)


if __name__ == "__main__":
    main()
