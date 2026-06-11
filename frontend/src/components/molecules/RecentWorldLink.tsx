import { Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { World } from '../../lib/apiTypes';
import { formatDate } from '../../utils/format';

export function RecentWorldLink({ world }: { world: World }) {
  return (
    <Link className="recent-world" to={`/wiki/${world.id}`}>
      <span>
        <strong>{world.title}</strong>
        <small>{world.tone || 'No tone set'}</small>
      </span>
      <span className="recent-date">
        <Clock size={14} aria-hidden="true" />
        {formatDate(world.created_at)}
      </span>
    </Link>
  );
}
