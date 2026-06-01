import { FilterSelect, SearchField } from '../molecules';

export function WorldToolbar({
  query,
  toneFilter,
  tones,
  onQueryChange,
  onToneFilterChange,
}: {
  query: string;
  toneFilter: string;
  tones: string[];
  onQueryChange: (value: string) => void;
  onToneFilterChange: (value: string) => void;
}) {
  return (
    <div className="worlds-toolbar" aria-label="World filters">
      <SearchField
        className="world-search"
        label="Search worlds"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        placeholder="Search title, tone, notes, or seed"
      />
      <FilterSelect
        className="world-filter"
        label="Tone"
        value={toneFilter}
        onChange={(event) => onToneFilterChange(event.target.value)}
      >
        <option>All</option>
        {tones.map((tone) => <option key={tone}>{tone}</option>)}
      </FilterSelect>
    </div>
  );
}
