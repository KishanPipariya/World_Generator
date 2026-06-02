import type { DraftExtractionCandidateKind, DraftPassage, GraphLayoutMode } from '../../lib/apiTypes';

export const ENTITY_GROUPS = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
export const ENTITY_TYPES = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
export const EXPORT_PRESETS = [
  ['full_bible', 'Full Bible'],
  ['character_dossier', 'Characters'],
  ['faction_brief', 'Factions'],
  ['location_gazetteer', 'Locations'],
  ['timeline_only', 'Timeline'],
  ['obsidian', 'Obsidian'],
] as const;
export const GRAPH_LAYOUTS: { value: GraphLayoutMode; label: string }[] = [
  { value: 'manual', label: 'Manual' },
  { value: 'force', label: 'Relationship' },
  { value: 'type_columns', label: 'Type columns' },
  { value: 'faction_clusters', label: 'Faction clusters' },
  { value: 'timeline_order', label: 'Timeline' },
];
export const DRAFT_STATUSES: DraftPassage['status'][] = ['draft', 'revising', 'ready', 'archived'];
export const DRAFT_CANDIDATE_KINDS: DraftExtractionCandidateKind[] = ['entity', 'relationship', 'timeline_event', 'lore_note'];
export const TEMPLATE_FIELDS: Record<string, string[]> = {
  Character: ['goal', 'secret', 'fear', 'voice'],
  Location: ['hazards', 'economy', 'culture', 'landmark'],
  Faction: ['resources', 'rivals', 'public_goal', 'secret'],
  Event: ['causes', 'consequences', 'participants', 'date'],
  Concept: ['rules', 'limits', 'cost', 'symbols'],
  Other: ['role', 'origin', 'constraints'],
};
export const PROMPTS = [
  {
    label: 'Faction Pressure',
    value: 'For The Ember Archipelago, generate three factions with public goals, secret leverage, scarce resources, and one unresolved conflict tying each faction to existing canon.',
  },
  {
    label: 'Timeline Crisis',
    value: 'For The Ember Archipelago, generate five escalating timeline events around the Night of Falling Bells, each with a cause, consequence, and entity most changed by it.',
  },
  {
    label: 'Secrets',
    value: 'For The Ember Archipelago, generate four canon-safe secrets. Each secret should name who knows it, who would suffer if revealed, and which saved entity it complicates.',
  },
  {
    label: 'Expand Selected',
    value: 'Expand the selected entity with history, sensory details, story pressure, a secret, and two relationship hooks that can be added to canon.',
  },
];
