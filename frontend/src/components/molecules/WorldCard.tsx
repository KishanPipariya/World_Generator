import { BookOpen, Clock, Shield, Trash2, Wrench } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { World } from '../../lib/apiTypes';
import { Badge } from '../atoms';
import { formatDate } from '../../utils/format';

export function WorldCard({ world, onDelete }: { world: World; onDelete: (world: World) => void }) {
  return (
    <article className="world-card">
      <div className="world-card-header">
        <Link to={`/wiki/${world.id}`} className="world-card-title">
          <h2>{world.title}</h2>
        </Link>
      </div>
      <Link to={`/wiki/${world.id}`} className="world-card-body">
        {world.tone && <Badge variant="primary">{world.tone}</Badge>}
        <p className="world-era">{world.era_notes || 'No era notes'}</p>
      </Link>
      <div className="world-card-footer">
        <Link to={`/wiki/${world.id}`} className="world-card-action">
          <Clock size={16} aria-hidden="true" />
          <span>{formatDate(world.created_at)}</span>
        </Link>
        <Link to={`/wiki/${world.id}`} className="world-card-action">
          <BookOpen size={16} aria-hidden="true" />
          <span>Wiki</span>
        </Link>
        <Link to={`/worlds/${world.id}`} className="world-card-action">
          <Wrench size={16} aria-hidden="true" />
          <span>Workbench</span>
        </Link>
        <Link to={`/worlds/${world.id}/dm`} className="world-card-action">
          <Shield size={16} aria-hidden="true" />
          <span>DM</span>
        </Link>
        <button className="text-danger-button" type="button" onClick={() => onDelete(world)}>
          <Trash2 size={15} aria-hidden="true" />
          Delete
        </button>
      </div>
    </article>
  );
}
