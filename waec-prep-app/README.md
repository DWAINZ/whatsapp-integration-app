# D'WAINZ — WAEC & JAMB Exam Prep

A subscription-style exam-prep platform for Nigerian WAEC/JAMB students, built around
short "lesson reel" cards (story → deep-understanding lesson → gated quiz) plus a
**Fast Exam Prep** track of past questions cross-referenced back to the exact lesson
card that explains the answer.

**Biology is now complete**: all 22 topics of the standard WAEC/NECO/JAMB syllabus,
grouped into 7 themes (Organisation of Life; Diversity of Organisms; Nutrition,
Transport & Gas Exchange; Excretion, Support & Growth; Reproduction & Coordination;
Ecology; Genetics, Evolution & Applications), 49 sub-topics total, each a full
story/lesson/quiz reel. This validated the content model, app shell and
cross-referencing mechanic, now proven at full-subject scale — the same pattern is
ready to scale to the rest of the WAEC subjects (Physics, Chemistry, Mathematics, etc.).

## Status

- ✅ Content model: Subject → Topic → Sub-topic → Lessons (JSON, not hardcoded per-page)
- ✅ Reusable reel engine (stories, gated quizzes with 3-try retry, stats, voice narration,
  press-and-hold pause, tap-to-jump progress bar, Previous/Play-Pause/Next transport
  buttons) — generalized into `src/engine/`
- ✅ App shell: subject picker → subject topic list → sub-topic list with progress →
  lesson reel, with a clickable breadcrumb at every level
- ✅ Fast Exam Prep: syllabus browser showing every past question per topic/sub-topic,
  answers withheld until attempted, with a **"Review the lesson card that explains
  this"** link that deep-links into the exact card and can return to where you came from
- ✅ Per-topic certificate, unlocked once every sub-topic is completed
- ✅ Per-topic accent colour, cycled from a shared palette, for visual variety across topics
- ✅ **Biology: all 22 syllabus topics built** (49 sub-topics)
- ⚠️ **Past-exam questions are placeholder/fabricated** — see below
- 🔲 Not yet built: user accounts, payments/subscriptions, backend/database (this phase
  is a static, localStorage-backed prototype of the real product); other WAEC subjects
  beyond Biology

## Placeholder exam data — read before using this for real study

`data/past-questions/biology.json` contains `"placeholder": true` and a `disclaimer`
field. The questions in it were **written by the content team to test the platform's
structure** — they are not verified WAEC past questions, and years/papers are
illustrative. Per the agreed Phase 1 plan, real WAEC past questions will be supplied
later and dropped into files with this same shape, so no re-architecture is needed —
just replace the data.

## How the content model works

```
data/subjects/biology.json
  subject, subjectTitle
  topics: [
    { id, title, description,
      subtopics: [
        { id, title,
          stories: [ { tag, sub, heading, list[], narration } ],
          lessons: [ { eyebrow, heading, list[], sub, narration } ],
          quiz:    [ { question, options[], correctIdx, explainCorrect, explainWrong,
                       refCard (1-based lesson number), narration } ]
        }
      ]
    }
  ]

data/past-questions/biology.json
  subject, placeholder, disclaimer
  topics: {
    "<topic-id>": {
      "<subtopic-id>": [
        { id, year, paper, question, options[], answer (letter), explanation,
          ref: { subtopic, card (1-based lesson number) } }
      ]
    }
  }
```

Each sub-topic is one self-contained reel (its own stories/lessons/quiz), matching the
existing WAEC-topic reel format. `refCard` / `ref.card` point at a **lesson** card
number within that sub-topic — the engine converts that into an absolute card index
and can jump straight to it from either a wrong quiz answer (inside the reel) or a
past-question review link (from Fast Exam Prep, anywhere in the app), then offers a way
back to exactly where the student came from.

## Adding a new subject or topic

1. Add a new file under `data/subjects/<subject>.json` following the shape above.
2. Add a matching `data/past-questions/<subject>.json` (or omit it — Fast Exam Prep
   simply skips topics with no question bank yet).
3. Add the subject to the list in `src/app/index.html` (`status: 'live'`).

No engine or page code needs to change — everything reads from the JSON.

## Running locally

This is a static site (no build step, no backend yet). Serve the folder over HTTP
(needed for `fetch()` to load the JSON — opening the HTML files directly via `file://`
will not work):

```
cd waec-prep-app
python3 -m http.server 8080
```

Then open `http://localhost:8080/src/app/index.html`.

## Architecture notes for later phases

- **Content addressing**: a lesson card is addressed as
  `{subject, topic, subtopic, card}` — stable enough to reference from anywhere else in
  the app (past questions today; could later support "related lesson" links between
  subtopics too).
- **Progress**: currently stored in `localStorage` (`dwainz_progress_v1`), keyed by
  subject/topic/subtopic. This is a placeholder for real per-user progress once accounts
  exist — swapping it for an API call is a small change localized to `shared.js`.
- **Scaling past Biology**: the same JSON shape should move into a real database (so
  content can be authored/edited without redeploying static files) and the
  past-question bank should grow to cover every WAEC topic with real questions.
  Nigeria-specific items still to decide before public launch: payment gateway
  (Paystack/Flutterwave), NDPR-compliant handling of any student data, and
  hosting/domain.

## Things that need your input / access before going further

- **Real past WAEC questions** for Biology (and eventually other subjects) — you
  mentioned you'd supply these; the data shape above is ready for them.
- **Hosting + domain** for a public deployment (this currently only runs locally / from
  this repo).
- **Payment gateway account** (Paystack or Flutterwave) once subscriptions are wired up.
- Confirmation of which WAEC subject to build next after Biology (Physics, Chemistry,
  Mathematics, etc.).
