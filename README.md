# lecture-skills

Two [Claude Code](https://claude.com/claude-code) skills that turn a lecture - YouTube video or raw transcript - into a clean, typeset HTML study document with rendered LaTeX and reading prompts.

- **`lecture-yt`** - one-shot pipeline: give it a YouTube URL, it fetches the transcript and hands off to `lecture-reader`. Slash command: `/lecture-yt <youtube-url-or-video-id>`.
- **`lecture-reader`** - takes a transcript file (VTT, SRT, or plain text) you already have and produces the typeset HTML document. Slash command: `/lecture-reader` (also invoked internally by `lecture-yt`).

## Install

Copy both skill folders into your Claude Code skills directory:

```bash
git clone https://github.com/<your-username>/lecture-skills.git
cp -r lecture-skills/lecture-yt lecture-skills/lecture-reader ~/.claude/skills/
```

`lecture-yt` needs the [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) Python package to fetch captions:

```bash
pip install youtube-transcript-api
```

## Usage

```
/lecture-yt https://www.youtube.com/watch?v=XXXXXXXXXXX
```

or, if you already have a transcript file:

```
/lecture-reader
```

(then point it at your transcript when asked)

By default, finished documents are saved to `~/lecture-notes/` (created automatically on first run). Tell Claude a different directory if you keep notes elsewhere.

## How it works

`lecture-yt` is a thin front end: it runs the bundled `fetch_transcript.py` script to pull a transcript from YouTube's caption track, then hands off to `lecture-reader`'s pipeline (clean → reconstruct/classify → typeset into `assets/lecture-template.html`) to produce the final document.

## License

MIT — see [LICENSE](LICENSE).
