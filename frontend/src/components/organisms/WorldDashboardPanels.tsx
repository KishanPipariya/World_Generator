import { BookOpen, Database, FolderOpen, Shield, Wrench } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { World } from '../../lib/apiTypes';
import { RecentWorldLink, SectionHeader } from '../molecules';

export function WorldDashboardPanels({
  loading,
  recentWorlds,
}: {
  loading: boolean;
  recentWorlds: World[];
}) {
  return (
    <section className="dashboard-grid" aria-label="World wiki dashboard">
      <div className="dashboard-panel recent-panel">
        <SectionHeader icon={<FolderOpen size={18} aria-hidden="true" />} title="Recent Worlds" />
        {loading ? (
          <p className="text-muted">Loading worlds...</p>
        ) : recentWorlds.length === 0 ? (
          <div className="dashboard-empty">
            <Database size={26} aria-hidden="true" />
            <p>No worlds yet. Create one or use the demo to explore the wiki.</p>
          </div>
        ) : (
          <div className="recent-world-list">
            {recentWorlds.map((world) => <RecentWorldLink world={world} key={world.id} />)}
          </div>
        )}
      </div>

      <div className="dashboard-panel quick-panel">
        <SectionHeader icon={<BookOpen size={18} aria-hidden="true" />} title="Quick Links" />
        <Link to="/worlds" className="quick-link">
          <FolderOpen size={18} aria-hidden="true" />
          <span>
            <strong>World Management</strong>
            <small>Search, filter, open, and maintain worlds.</small>
          </span>
        </Link>
        {recentWorlds[0] ? (
          <>
            <Link to={`/wiki/${recentWorlds[0].id}`} className="quick-link">
              <BookOpen size={18} aria-hidden="true" />
              <span>
                <strong>Latest Wiki</strong>
                <small>Read the current world bible view.</small>
              </span>
            </Link>
            <Link to={`/worlds/${recentWorlds[0].id}`} className="quick-link">
              <Wrench size={18} aria-hidden="true" />
              <span>
                <strong>Workbench</strong>
                <small>Maintain canon, drafts, timeline, planning, and graph tools.</small>
              </span>
            </Link>
            <Link to={`/worlds/${recentWorlds[0].id}/dm`} className="quick-link">
              <Shield size={18} aria-hidden="true" />
              <span>
                <strong>DM Workflow</strong>
                <small>Sessions, lore notes, clocks, impact review, and handouts.</small>
              </span>
            </Link>
          </>
        ) : (
          <p className="text-muted">Quick wiki and workbench links appear after a world exists.</p>
        )}
      </div>
    </section>
  );
}
