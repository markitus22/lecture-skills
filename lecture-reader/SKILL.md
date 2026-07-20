---
name: lecture-reader
description: 'Transform a raw YouTube lecture transcript (VTT auto-captions, SRT, or plain text) into a beautifully readable HTML study document with rendered LaTeX equations, imposed logical structure, visual-gap flags, and margin reading prompts. PRIMARY TRIGGER is the slash command "/lecture": when the user types this, ALWAYS trigger this skill. Also trigger on "/transcript" (alias) and on explicit phrases like "make this transcript readable", "clean up this lecture transcript", "turn this transcript into a study doc", "process the transcript from my script", or whenever the user uploads or pastes a lecture transcript and wants to read or study it. Reading front-end for the user''s WSL transcript-fetch script (ML, AI, data science, maths lectures). Do NOT trigger to summarize (this skill never summarizes), to drill or quiz (that is /drill), to build interactive visuals (that is /aha), or to typeset non-transcript content (that is /paper).'
---

# Lecture Reader

Turn a raw lecture transcript into one readable HTML study document. The transcript loses the visual channel and mangles the math; this skill repairs what is repairable (structure, equations) and honestly flags what is not (missing visuals). It never summarizes: a summary of a transcript is a worse transcript. The output preserves the lecture's full argument, just structured for a reader instead of a listener.

Output: one .html file per segment, in the user's established reading design (warm paper, serif, blueprint accents), saved to `./lecture-notes/` in the current working directory (create it if missing).

## Inputs it accepts

1. **An uploaded transcript file** (.vtt, .srt, .txt, .md).
2. **Pasted transcript text** in the message.
3. **Bare invocation** ("/lecture" with nothing): ask for the transcript in one line. Do not proceed empty.

## Workflow

### Step 1: Clean deterministically

Run the bundled cleaner on the raw input:

```bash
python3 ~/.claude/skills/lecture-reader/scripts/clean_transcript.py <input_file> -o /tmp/lecture-clean.txt
```

It auto-detects VTT / SRT / timestamped-plain / plain, strips timestamps and cue metadata, deduplicates the rolling-overlap lines that YouTube auto-captions produce, joins fragments into sentences, and reports word count and estimated lecture minutes. If input was pasted, save it to a file first. Read the cleaned output, not the raw file.

### Step 2: Size the job

Estimated minutes come from the cleaner (~150 words per minute).

- **Under ~45 minutes (~7,000 words):** process the whole transcript into one document.
- **Longer:** split at topic boundaries into segments of roughly 20 to 30 minutes each. Emit the document for segment 1, and open it with a segment map (a `.rows` list of all segments with their rough timestamps and one-line topics). Tell the user to say "next" for the following segment. Never cram a multi-hour lecture into one document; an unfinishable document is a failed one.

### Step 3: Reconstruct (the model pass)

Read the cleaned text and do three things in one pass:

1. **Classify.** Break the flow into blocks and tag each: SETUP (problem being motivated), DEFINITION, DERIVATION, CLAIM, EXAMPLE, ASIDE (tangents, admin, jokes). Filler that carries nothing is dropped silently. Asides are kept but rendered visually quiet so the eye can skip them. Do not reorder the lecture; impose headings on the existing order.
2. **Rebuild equations.** Every spoken equation ("soft max of q k transpose over root d k") becomes proper LaTeX. Under each display equation, write a one-line plain-words gloss saying what it does and why ("divide by \(\sqrt{d_k}\) so large dot products do not saturate softmax"). If the speech is too mangled to reconstruct confidently, render the best guess and mark it `.eq-unsure` with a note; never silently invent math. Use standard notation for the field even if the ASR text differs.
3. **Flag visuals.** Wherever the lecturer references something visible ("as you can see here", "this plot", "on the board"), insert a gap box stating what the visual most likely showed and, when inferable, the approximate timestamp so the user can jump to it in the video. Do not fabricate detailed descriptions of visuals; state the likely type and role in one or two lines.

### Step 4: Typeset

Copy `~/.claude/skills/lecture-reader/assets/lecture-template.html` and fill only the content inside `.wrap`. Keep the CSS byte-identical. The template extends the user's paper design with lecture components; read the comment block at the top of the template for the component list and usage rules:

- `.eq` for display equations with `.gloss` underneath (MathJax renders `\( \)` and `\[ \]`).
- `.gap` for missing-visual boxes.
- `.ask` for the reading prompt at each section start: one line, "what problem is this section solving?" phrased for that section. This bakes active reading into the page.
- `.aside` for quiet tangents.
- Section kickers carry the block type (SETUP, DERIVATION, ...).
- Masthead standfirst states lecture title, source, and which segment this is.
- No thesis panel invention: the thesis slot carries the lecture's own central claim, in the lecturer's framing.

Writing rules: the words are the lecturer's argument, lightly repaired for grammar and ASR errors, not paraphrased into your own voice. Fix broken technical terms (ASR writes "grade in descent", you write "gradient descent"). Simple connective edits only. No em dashes. Zero JavaScript beyond the MathJax include.

### Step 5: Save and present

Name the file `<lecture-slug>-part<N>.html` (or no part suffix for single-segment), save to `./lecture-notes/`. In chat: state the saved file path, one line on what the segment covers, and, if segmented, what is next. Do not summarize the content in chat.

## Hand-offs, not scope creep

This skill ends at "readable document". It does not generate questions, flashcards, or drills. When presenting, one short closing line may point at the natural next step ("when you have read it, /drill attention-scaling" or "/aha for the flagged softmax geometry"), chosen from what the document actually flagged. One pointer, not a menu.

## Quality floor

Before presenting, verify: single file renders with only the MathJax CDN request; readable at 360px; every display equation has a gloss; every "as you can see"-type reference in the cleaned text got a gap box or was genuinely non-visual; no section is a summary of dropped content; heading hierarchy intact (one h1, sections h2); ASR-mangled technical terms repaired consistently throughout.
