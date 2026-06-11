# Future Features

This roadmap describes likely product direction for Literary World Generator.
It is intentionally practical: items here should be suitable starting points for
issues, design notes, or implementation plans. It does not commit the project to
delivery dates.

## Product Direction

Literary World Generator should remain a graph-first world bible for fiction
writers and campaign runners. The core workflow is to capture canon, connect it
to drafts and sessions, review generated or extracted suggestions, and export
useful writing context without losing track of what is true in the world.

Near-term work should make the current FastAPI and React app feel more connected
across canon, drafts, timelines, graph views, planning boards, campaign notes,
lore visibility, consistency reports, LLM suggestions, and Markdown exports.

## Near-Term Priorities

### Canon Graph Improvements

- Improve saved graph views with direct focus links, clearer filter state, and
  better handling for dense relationship networks.
- Add graph-aware review queues for isolated entities, weak relationships,
  overloaded nodes, and missing relationship context.
- Make relationship metadata easier to compare and edit, especially stance,
  category, strength, display priority, and history.

### Draft-to-Canon Workflows

- Promote draft extraction into a primary review workflow.
- Let writers preview and edit candidate entities, relationships, timeline
  events, and lore notes before they enter the suggestion inbox.
- Show which canon items a draft already links to and what changed after each
  passage check or extraction.
- Compare draft check history across revisions so resolved and newly introduced
  issues are visible.

### Generation Review

- Parse multiple structured candidates from one LLM result instead of storing
  large generated text as a single suggestion.
- Add editable previews and diffs for generated changes to existing canon.
- Store provenance for generated material, including prompt, source context,
  model details, acceptance state, and target resource.
- Keep generated and extracted material non-destructive until explicitly
  accepted, replaced, appended, or discarded.

### Consistency Checks

- Expand canon checks beyond duplicates, thin lore, orphaned entities, weak
  relationships, contradictions, and timeline gaps.
- Track issue lifecycle more deeply with assignment, recurring issue history,
  and links back to drafts, sessions, suggestions, and affected canon.
- Provide targeted fix actions where possible, such as linking an orphaned
  entity, adding relationship pressure, or updating a timeline dependency.

## Mid-Term Feature Areas

### Campaign and Session Tooling

- Turn session impact reviews into a complete post-session workflow that can
  propose canon updates, timeline changes, lore notes, and faction clock
  movement.
- Add better prep views that combine active clocks, unresolved lore, linked
  entities, recent sessions, and player-visible handouts.
- Support session and campaign summaries that can be exported without exposing
  private notes.

### Lore Visibility and Handouts

- Expand lore note visibility states into a stronger player-facing review flow.
- Add redaction previews so a GM can verify what a player or collaborator will
  see.
- Link handouts back to their source canon, session, timeline event, or draft
  excerpt for auditability.
- Add export presets for selected player-safe packets, scene briefs, and session
  briefs.

### Import and Export Workflows

- Add import jobs for Markdown, Obsidian notes, and structured JSON.
- Route imported candidates through the existing suggestion review model instead
  of writing directly to canon.
- Preserve import source metadata, warnings, errors, and rerun history.
- Expand Markdown export into folder-based Obsidian vault exports,
  Scrivener-friendly Markdown, JSON backups, and selected canon packets.

### Planning and Timeline

- Add drag reordering and grouping for timeline events by era, arc, faction,
  location, draft, or session.
- Warn when event reordering conflicts with dependencies, causes,
  consequences, or participant availability.
- Make planning cards easier to connect to timeline events, drafts, lore notes,
  sessions, and faction clocks.

## Longer-Term Ideas

### Collaboration and Permissions

- Add multi-user worlds with owner, editor, viewer, and player-facing roles.
- Keep private notes, DM-only lore, generated drafts, and player-visible
  handouts behind explicit permissions.
- Add an activity trail for accepted suggestions, canon edits, exports, imports,
  visibility changes, and session updates.

### Project Templates

- Provide starter templates for novels, TTRPG campaigns, mysteries, epic
  fantasy, science fiction, and historical fiction.
- Seed templates with useful entity types, structured fields, relationship
  categories, planning lanes, lore visibility defaults, and export presets.
- Preserve custom fields when a world adopts or changes templates.

### World Analytics

- Surface thin lore, relationship imbalance, timeline density, unresolved
  contradictions, missing faction pressure, and protagonist overuse as
  actionable review queues.
- Let each analytic signal link directly to the relevant canon, draft, timeline
  event, session, lore note, graph view, or suggestion.

### Local-First Reliability

- Add backup and restore workflows for local project data.
- Improve degraded-mode messaging when SQLite storage or the configured LLM provider is
  unavailable.
- Add operator-facing readiness checks for database connectivity, migrations,
  authentication settings, and LLM configuration.

## Non-Goals For Now

- Do not make LLM output automatically overwrite canon.
- Do not replace the graph-first canon model with unstructured notes.
- Do not require an LLM provider for core world-building workflows.
- Do not introduce real-time collaboration until permissions and audit trails
  are designed.
- Do not break existing API response shapes for worlds, entities,
  relationships, timelines, suggestions, drafts, sessions, lore notes, faction
  clocks, consistency issues, graph views, planning boards, or Markdown exports.
