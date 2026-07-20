import re
import sys
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")

    if parsed.hostname and "youtube.com" in parsed.hostname:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
            if video_id:
                return video_id
        match = re.match(r"^/(embed|shorts|live)/([^/?]+)", parsed.path)
        if match:
            return match.group(2)

    # Fall back to treating the input as a bare video ID
    return url


url = sys.argv[1] if len(sys.argv) > 1 else input("Enter YouTube URL: ")
video_id = extract_video_id(url)
out_path = sys.argv[2] if len(sys.argv) > 2 else f"transcripts/{video_id}.txt"

api = YouTubeTranscriptApi()
fetched = api.fetch(video_id)

with open(out_path, "w", encoding="utf-8") as f:
    for s in fetched:
        h, rem = divmod(int(s.start), 3600)
        m, sec = divmod(rem, 60)
        f.write(f"[{h:02d}:{m:02d}:{sec:02d}] {s.text}\n")

print(f"Saved transcript to {out_path}")
