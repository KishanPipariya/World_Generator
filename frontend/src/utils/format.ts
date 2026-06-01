export const formatDate = (value: string) => new Date(value).toLocaleDateString();

export const formatDateTime = (value: string) => new Date(value).toLocaleString(undefined, {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
});

export const displayEntityType = (type: string) => {
  const normalized = type.trim().toLowerCase();
  if (['character', 'person', 'historical figure'].includes(normalized)) return 'Character';
  if (['location', 'city', 'region', 'landmark', 'continent'].includes(normalized)) return 'Location';
  if (['faction', 'guild', 'kingdom', 'organization'].includes(normalized)) return 'Faction';
  if (['concept', 'magic system', 'technology', 'term'].includes(normalized)) return 'Concept';
  if (['event', 'historical event', 'battle'].includes(normalized)) return 'Event';
  return 'Other';
};
