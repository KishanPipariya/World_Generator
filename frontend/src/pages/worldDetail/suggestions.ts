import type { GenerationSuggestion } from '../../lib/apiTypes';

export type SuggestionApplyMode =
  | 'create_entity'
  | 'append_to_entity'
  | 'replace_entity'
  | 'discard'
  | 'create_relationship'
  | 'create_timeline_event'
  | 'create_lore_note';

export const buildSuggestionApplyPayload = (
  suggestion: GenerationSuggestion,
  mode: SuggestionApplyMode,
  options: {
    entityId?: string;
    name?: string;
    entityType?: string;
    fallbackName?: string;
    fallbackEntityType?: string;
  } = {},
) => ({
  mode,
  entity_id: mode === 'create_entity' || mode === 'discard' ? undefined : options.entityId,
  name: options.name?.trim() || suggestion.suggested_name || options.fallbackName || 'Generated Lore',
  entity_type: options.entityType || suggestion.suggested_type || options.fallbackEntityType || 'Concept',
});
