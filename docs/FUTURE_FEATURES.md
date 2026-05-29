# Future Feature Roadmap for Solo Writers

Literary World Generator has moved beyond a basic world bible. The app now
includes canon entities and relationships, timeline planning, graph views,
planning boards, revision history, generation suggestions, persisted canon
issues, saved drafts with check history, draft extraction, campaign sessions,
lore notes, faction clocks, wiki/player visibility, and multiple Markdown export
presets. The world workspace also has a dashboard tab that surfaces review
queues and links into the main writing workflows.

The next product step is workflow polish: make canon, drafts, timelines,
campaign notes, wiki views, suggestions, and exports feel like one connected
daily writing workspace instead of separate panels.

## Product Direction

- Keep the graph-first world bible model central.
- Treat LLM output as reviewable suggestions until a writer explicitly accepts
  it.
- Preserve existing world, entity, relationship, timeline, suggestion, draft,
  campaign, lore-note, clock, and export response shapes while adding new
  resources alongside them.
- Prioritize workflows that reduce repeated manual bookkeeping for solo fiction
  writers, with TTRPG support as a strong secondary path.

## Near Term

### World dashboard (frontend foundation complete)

- Completed: the world detail page now opens to a dashboard tab summarizing open
  canon issues, recent drafts, pending suggestions, timeline activity, campaign
  notes, active faction clocks, and next planning cards.
- Completed: dashboard cards link into the relevant workflow tabs for canon
  review, suggestion handling, draft work, timeline planning, campaign notes, and
  planning boards.
- Remaining: add a backend dashboard summary resource so the frontend does not
  have to aggregate multiple endpoint responses.
- Remaining: add durable activity history for accepted suggestions, draft
  checks, updated lore notes, faction clock movement, exports, and wiki/share
  events.
- Remaining: deepen item-level links for timeline events, individual planning
  cards, lore notes, and export packets once those views support direct item
  focus.

### Draft-to-canon polish

- Make draft extraction a primary workflow instead of a secondary action.
- Let writers select prose, preview candidate entities, relationships, timeline
  events, and lore notes, then edit candidates before sending them to the
  suggestion inbox.
- Show which canon links and timeline events a draft already touches before and
  after extraction.
- Compare repeated draft checks so a writer can see whether a revision resolved
  or introduced canon issues.

### Smarter generation review

- Parse multiple candidate entities, relationships, timeline events, lore notes,
  or edits from a single LLM result.
- Show an editable preview before anything is saved.
- Add a diff view when generated text would change existing canon.
- Store prompt, source context, model metadata, provenance, and acceptance
  history for saved generated lore.

## Mid Term

### Stronger wiki and player view

- Expand player-visible lore with redactions, discovered-state history, and
  handout-ready text.
- Add share/export modes for TTRPG players and collaborators without exposing
  DM-only notes.
- Link wiki entries back to source sessions, drafts, suggestions, timeline
  events, and canon changes.
- Add preview controls so a GM can inspect exactly what a player-facing view
  contains before sharing it.

### Import workflows

- Import Markdown and Obsidian notes into reviewable import jobs.
- Extract candidate entities, relationships, timeline events, and lore notes into
  the existing suggestion inbox.
- Preserve source file metadata, extraction warnings, and errors so writers can
  re-run or audit imports.
- Keep imported suggestions non-destructive until accepted.

### Deeper timeline planning

- Add visual drag reordering for events with relative dates.
- Flag dependency warnings when reordered events contradict causes,
  consequences, or participant availability.
- Group events by era, arc, location, faction, session, draft, or custom planning
  label.
- Add participant filters and summaries of what changed because of each event.

### Writing-tool exports

- Expand the existing Markdown presets into folder-based Obsidian vault exports,
  Scrivener-friendly Markdown, selected canon packets, player handouts, and
  scene-specific context briefs.
- Include backlinks, tags, timeline snippets, relationship summaries, lore-note
  visibility, and campaign-session context where the target format supports
  them.
- Let writers export only the canon connected to a scene, arc, faction, session,
  draft, or selected set of entities.

## Long Term

### World analytics

- Surface thin lore, isolated entities, missing relationship pressure, overloaded
  protagonists, faction balance, timeline density, and unresolved
  contradictions.
- Show analytics as actionable review queues rather than static charts.
- Let writers jump from each signal to the relevant canon, draft, timeline event,
  session, lore note, faction clock, or suggestion.

### Project templates

- Offer starter schemas for novels, TTRPG campaigns, epic fantasy, sci-fi
  settings, mysteries, and historical fiction.
- Preserve custom fields when a project switches templates or adds a specialized
  schema later.
- Seed templates with useful entity types, relationship categories, timeline
  fields, planning-board lanes, lore-note visibility defaults, faction clocks,
  and export presets.

### Local-first reliability

- Add backup and restore for local project data.
- Add JSON export and import for worlds, canon, drafts, timeline data,
  suggestions, issue states, campaign sessions, lore notes, faction clocks, graph
  views, and planning boards.
- Add deeper readiness checks for Neo4j and LLM configuration for local
  operators.
- Make degraded-mode behavior clear when the graph database or LLM is
  unavailable.

## Public APIs and Data Model

- Add backend dashboard summary resources that aggregate existing issues, drafts,
  suggestions, timeline events, campaign notes, faction clocks, and planning
  cards without changing those resource shapes. The current dashboard frontend
  uses existing endpoints as an interim implementation.
- Add review metadata for generated and imported suggestions: prompt, source
  context, model metadata, provenance, accepted-at timestamp, accepted target,
  and diff information where relevant.
- Add import job resources with source text or file metadata, extracted
  suggestions, status, warnings, and errors.
- Add export job or preset options for multi-file exports without breaking the
  current Markdown export endpoint.
- Avoid changing current world, entity, relationship, timeline, suggestion,
  draft, campaign, lore-note, faction-clock, and issue response shapes.

## Test Plan

- Frontend dashboard link coverage exists. Add/keep tests for draft extraction
  preview, suggestion acceptance, wiki visibility, player-safe exports, and
  export preset selection.
- Backend tests for dashboard summaries, suggestion review metadata, import
  suggestion creation, JSON backup/restore, export presets, and
  backward-compatible response shapes.
- LLM tests with fake services for extraction, canon checks, multi-suggestion
  parsing, diff generation, and unavailable-model fallbacks.
- Regression tests that keep existing draft, campaign-session, lore-note,
  faction-clock, issue lifecycle, and Markdown export behavior stable.

## Assumptions

- The primary audience remains solo fiction writers.
- TTRPG campaign support remains a strong secondary path.
- The graph-first world bible model stays central.
- New LLM actions remain non-destructive until explicitly accepted by the writer.
