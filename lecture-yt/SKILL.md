---
name: lecture-yt
description: Fetch a YouTube lecture transcript and turn it straight into a readable, typeset HTML study document in one step. PRIMARY TRIGGER is the slash command /lecture-yt URL-or-video-id. Chains a bundled fetch_transcript.py script with the lecture-reader skill cleaning, reconstruction, and typesetting steps. Do NOT trigger when the user already has a transcript file or pasted transcript text in hand - use lecture-reader directly for those. Do NOT trigger for non-YouTube content.
---

# Lecture from YouTube

One-shot pipeline: YouTube URL -> raw transcript -> cleaned text -> readable typeset HTML study document. This skill is a thin front end that fetches, then hands off to the `lecture-reader` skill for the actual reading-document craft.

## Inputs

`$ARGUMENTS` is a YouTube URL or bare video ID. If empty, ask for one in one line before proceeding - do not guess a video.

## Workflow

### Step 1: Fetch the transcript

Run the bundled fetch script from a scratch working directory so it writes into a `transcripts/` subfolder there (the script needs `youtube-transcript-api` installed - `pip install youtube-transcript-api`):

```bash
mkdir -p /tmp/lecture-yt-scratch/transcripts && cd /tmp/lecture-yt-scratch && python3 ~/.claude/skills/lecture-yt/scripts/fetch_transcript.py "<url-or-id>"
```

Read the printed output line (`Saved transcript to transcripts/<video_id>.txt`) to get the exact file path and video ID.

If the command fails - no captions available, invalid URL/ID, network error - report the actual error to the user and stop. Do not fabricate a transcript or fall back to summarizing from general knowledge.

### Step 2: Hand off to lecture-reader

`fetch_transcript.py` writes lines as `[HH:MM:SS] text`, which is exactly the "timestamped plain text" format `clean_transcript.py` auto-detects - no reformatting needed. Continue directly with the `lecture-reader` skill's pipeline, using:

- Input file: `/tmp/lecture-yt-scratch/transcripts/<video_id>.txt`
- Cleaner: `python3 ~/.claude/skills/lecture-reader/scripts/clean_transcript.py <input_file> -o /tmp/lecture-clean.txt`
- Template: `~/.claude/skills/lecture-reader/assets/lecture-template.html`

Follow `lecture-reader`'s Step 2 (size the job), Step 3 (reconstruct: classify blocks, rebuild LaTeX, flag visuals), and Step 4 (typeset into the template) exactly as written there - this skill only replaces lecture-reader's Step 1 (deterministic clean) input source and Step 5 (save) output location, per below.

### Step 3: Save the finished document

Save finished lecture notes to the user's notes directory. If the user hasn't told you where that is, ask once, or default to `~/lecture-notes/` (create it if it doesn't exist; `git init` it the first time only). Raw transcripts in `/tmp/lecture-yt-scratch/` are regenerable scratch and never get copied into the notes directory.

Name the file `<lecture-slug>--<video_id>.html`, or `<lecture-slug>--<video_id>-part<N>.html` for a segmented lecture (no part suffix for a single-segment doc). `<lecture-slug>` is a short, lowercase, hyphenated slug (3-6 words, ASCII only) drawn from the lecture's actual title or central topic - the same understanding already used to write the document's masthead headline in Step 4, so no extra lookup is needed. Example: `machine-learning-is-a-loop--ROEad3SDI9Q.html`.

If the notes directory is a git repo, do not `git add` or `git commit` the new file - leave it staged for the user to review and commit when they're ready.

### Step 4: Report

Tell the user, in one or two lines: what the document covers, the saved local file path, and - if segmented - what to say ("next") for the following part. Do not summarize the lecture's content in chat.
