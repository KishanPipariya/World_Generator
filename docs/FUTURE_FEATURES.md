# Future Feature Roadmap for Solo Writers

Literary World Generator already covers the first layer of a working world bible:
generation suggestions, timelines, graph views, planning boards, revisions, passage
checks, and exports. The next stage should make the app feel less like a set of
separate tools and more like a daily writing workspace where draft prose, canon,
planning, review, and export workflows stay connected.

## Product Direction

- Keep the graph-first world bible model central.
- Treat LLM output as reviewable suggestions until a writer explicitly accepts it.
- Preserve existing world, entity, relationship, timeline, and export response
  shapes while adding new resources alongside them.
- Prioritize workflows that reduce repeated manual bookkeeping for solo fiction
  writers.

## Near Term

### Draft-to-canon workspace

- Add saved passages and scenes with title, body, status, linked canon, and check
  history.
- Let writers run canon checks repeatedly against the same draft and compare new
  findings with previous checks.
- Convert selected prose into candidate entities, relationships, timeline events,
  or generation suggestions.
- Link draft sections to affected canon so writers can move from a scene to the
  relevant entity, relationship, or timeline context.

### Canon issue lifecycle (completed)

- Persist consistency issue state with issue code, target id, status, note, first
  seen timestamp, and last seen timestamp.
- Support ignored, resolved, and reopened states so recurring warnings do not
  flood dashboards.
- Let writers add short notes explaining why an issue was ignored or how it was
  resolved.
- Link issues back to affected canon. Draft-check issue lifecycle remains a
  separate follow-up.

### Smarter generation review

- Parse multiple candidate entities, relationships, timeline events, or edits
  from a single LLM result.
- Show an editable preview before anything is saved.
- Add a diff view when generated text would change existing canon.
- Store prompt, source context, model metadata, and acceptance history for saved
  generated lore.

## Mid Term

### Deeper timeline planning

- Add visual drag reordering for events with relative dates.
- Flag dependency warnings when reordered events contradict causes,
  consequences, or participant availability.
- Group events by era, arc, location, faction, or custom planning label.
- Add participant filters and summaries of what changed because of each event.

### Import workflows

- Import Markdown and Obsidian notes into a reviewable import job.
- Extract candidate entities, relationships, and timeline events into the existing
  suggestion inbox.
- Preserve source file metadata and extraction errors so writers can re-run or
  audit imports.
- Keep imported suggestions non-destructive until accepted.

### Writing-tool exports

- Expand export presets for Obsidian vaults, Scrivener-friendly Markdown,
  selected canon packets, and scene-specific context briefs.
- Include backlinks, tags, timeline snippets, and relationship summaries where the
  target format supports them.
- Let writers export only the canon connected to a scene, arc, faction, or
  selected set of entities.

## Long Term

### World analytics

- Surface thin lore, isolated entities, missing relationship pressure, overloaded
  protagonists, faction balance, and timeline density.
- Show analytics as actionable review queues rather than static charts.
- Let writers jump from each signal to the relevant canon, draft, or suggestion.

### Project templates

- Offer starter schemas for novels, TTRPG campaigns, epic fantasy, sci-fi
  settings, mysteries, and historical fiction.
- Preserve custom fields when a project switches templates or adds a specialized
  schema later.
- Seed templates with useful entity types, relationship categories, timeline
  fields, and export presets.

### Local-first reliability

- Add backup and restore for local project data.
- Add JSON export and import for worlds, canon, drafts, timeline data,
  suggestions, and issue states.
- Add health checks for Neo4j and LLM readiness.
- Make degraded-mode behavior clear when the graph database or LLM is
  unavailable.

## Public APIs and Data Model

- Add saved draft resources for passages and scenes with title, body, status,
  linked canon, and check history.
- Added persisted consistency issue resources with issue code, target id, status,
  note, first seen, and last seen fields.
- Add import job resources with source text or file metadata, extracted
  suggestions, status, and errors.
- Add export preset options without breaking existing export behavior.
- Avoid changing current world, entity, relationship, timeline, and suggestion
  response shapes.

## Test Plan

- Backend tests for draft CRUD, issue state transitions, import suggestion
  creation, export presets, and backward-compatible response shapes.
- LLM tests with fake services for extraction, canon checks, multi-suggestion
  parsing, diff generation, and unavailable-model fallbacks.
- Frontend tests for issue resolution, draft check flow, import review, timeline
  filtering, export selection, and degraded-mode messaging.

## Assumptions

- The primary audience remains solo fiction writers.
- The graph-first world bible model stays central.
- New LLM actions remain non-destructive until explicitly accepted by the writer.
