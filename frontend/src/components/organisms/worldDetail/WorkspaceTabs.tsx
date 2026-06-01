import { Activity, ClipboardCheck, Clock, FileText, Network, Pencil } from 'lucide-react';

export type WorkspaceView = 'dashboard' | 'canon' | 'drafts' | 'timeline' | 'planning' | 'graph';

const tabs: { id: WorkspaceView; label: string; icon: typeof Activity }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Activity },
  { id: 'canon', label: 'Canon', icon: Pencil },
  { id: 'drafts', label: 'Drafts', icon: FileText },
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'planning', label: 'Planning', icon: ClipboardCheck },
  { id: 'graph', label: 'Graph', icon: Network },
];

export function WorkspaceTabs({
  activeView,
  onChange,
}: {
  activeView: WorkspaceView;
  onChange: (view: WorkspaceView) => void;
}) {
  return (
    <div className="workspace-tabs glass" role="tablist" aria-label="Workspace views">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const active = activeView === tab.id;
        return (
          <button
            className={active ? 'active' : ''}
            onClick={() => onChange(tab.id)}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls={`${tab.id}-panel`}
            id={`${tab.id}-tab`}
            key={tab.id}
          >
            <Icon size={16} />
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
