import { Globe2 } from 'lucide-react';
import type { World } from '../../lib/api';
import { Button, EmptyState } from '../atoms';
import { WorldCard } from '../molecules';

export function WorldGrid({
  worlds,
  onDelete,
  onClearFilters,
}: {
  worlds: World[];
  onDelete: (world: World) => void;
  onClearFilters: () => void;
}) {
  if (worlds.length === 0) {
    return (
      <EmptyState className="compact-empty">
        <Globe2 size={34} className="text-muted" aria-hidden="true" />
        <h3>No worlds match these filters</h3>
        <p>Adjust the search or tone filter to return to your saved worlds.</p>
        <Button variant="secondary" onClick={onClearFilters}>Clear Filters</Button>
      </EmptyState>
    );
  }

  return (
    <div className="worlds-grid">
      {worlds.map((world) => <WorldCard key={world.id} world={world} onDelete={onDelete} />)}
    </div>
  );
}
