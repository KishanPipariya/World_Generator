import { Activity, ClipboardCheck, Clock, FileText, Flag, Sparkles } from 'lucide-react';
import type {
  CampaignSession,
  ConsistencyIssueState,
  DraftPassage,
  FactionClock,
  GenerationSuggestion,
  LoreNote,
  PlanningCard,
  TimelineEvent,
} from '../../../lib/api';
import { formatDateTime } from '../../../utils/format';
import type { WorkspaceView } from './WorkspaceTabs';

type PlanningCardSummary = PlanningCard & { boardName: string };

export function WorldDetailDashboardPanel({
  pendingSuggestions,
  openIssueStates,
  drafts,
  recentDrafts,
  timelineEvents,
  recentTimelineEvents,
  nextPlanningCards,
  recentCampaignSessions,
  recentLoreNotes,
  activeFactionClocks,
  busy,
  onViewChange,
  onRunReport,
  onIssueSelect,
  onDraftSelect,
}: {
  pendingSuggestions: GenerationSuggestion[];
  openIssueStates: ConsistencyIssueState[];
  drafts: DraftPassage[];
  recentDrafts: DraftPassage[];
  timelineEvents: TimelineEvent[];
  recentTimelineEvents: TimelineEvent[];
  nextPlanningCards: PlanningCardSummary[];
  recentCampaignSessions: CampaignSession[];
  recentLoreNotes: LoreNote[];
  activeFactionClocks: FactionClock[];
  busy: boolean;
  onViewChange: (view: WorkspaceView) => void;
  onRunReport: () => void;
  onIssueSelect: (issue: ConsistencyIssueState) => void;
  onDraftSelect: (draftId: string) => void;
}) {
  return (
    <section className="glass content-section dashboard-panel" id="dashboard-panel" role="tabpanel" aria-labelledby="dashboard-tab">
      <div className="section-header">
        <Activity className="text-primary" />
        <h2>World Dashboard</h2>
        <span className="review-badge">{pendingSuggestions.length + openIssueStates.length} review items</span>
      </div>

      <div className="dashboard-stats" aria-label="World workspace summary">
        <button className="dashboard-stat" type="button" onClick={() => onViewChange('canon')}>
          <span>{openIssueStates.length}</span>
          <strong>Open issues</strong>
        </button>
        <button className="dashboard-stat" type="button" onClick={() => onViewChange('drafts')}>
          <span>{drafts.length}</span>
          <strong>Drafts</strong>
        </button>
        <button className="dashboard-stat" type="button" onClick={() => onViewChange('timeline')}>
          <span>{timelineEvents.length}</span>
          <strong>Timeline</strong>
        </button>
        <button className="dashboard-stat" type="button" onClick={() => onViewChange('planning')}>
          <span>{nextPlanningCards.length}</span>
          <strong>Planning cards</strong>
        </button>
      </div>

      <div className="dashboard-grid">
        <article className="dashboard-card">
          <div className="dashboard-card-header">
            <ClipboardCheck size={18} />
            <h3>Canon Review</h3>
            <button className="btn btn-secondary compact-button" type="button" onClick={onRunReport} disabled={busy}>
              Run Report
            </button>
          </div>
          {openIssueStates.length === 0 ? (
            <p className="text-muted">No persisted open issues. Run a report to refresh canon health.</p>
          ) : (
            <div className="dashboard-list">
              {openIssueStates.slice(0, 3).map((issue) => (
                <button className="dashboard-list-item" key={issue.id} type="button" onClick={() => onIssueSelect(issue)}>
                  <span>{issue.severity}</span>
                  <strong>{issue.message}</strong>
                  <small>{issue.code.replaceAll('_', ' ')} · {formatDateTime(issue.last_seen)}</small>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-header">
            <Sparkles size={18} />
            <h3>Suggestion Inbox</h3>
            <span className="dashboard-count">{pendingSuggestions.length}</span>
          </div>
          {pendingSuggestions.length === 0 ? (
            <p className="text-muted">No pending suggestions.</p>
          ) : (
            <div className="dashboard-list">
              {pendingSuggestions.slice(0, 3).map((suggestion) => (
                <button className="dashboard-list-item" key={suggestion.id} type="button" onClick={() => onViewChange(suggestion.source_type === 'draft' ? 'drafts' : 'canon')}>
                  <span>{(suggestion.candidate_kind ?? 'entity').replace('_', ' ')}</span>
                  <strong>{suggestion.suggested_name || 'Generated lore'}</strong>
                  <small>{suggestion.source_type ?? 'generation'} · {formatDateTime(suggestion.created_at)}</small>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-header">
            <FileText size={18} />
            <h3>Recent Drafts</h3>
            <button className="btn btn-secondary compact-button" type="button" onClick={() => onViewChange('drafts')}>
              Open
            </button>
          </div>
          {recentDrafts.length === 0 ? (
            <p className="text-muted">No saved drafts yet.</p>
          ) : (
            <div className="dashboard-list">
              {recentDrafts.map((draft) => (
                <button className="dashboard-list-item" key={draft.id} type="button" onClick={() => {
                  onDraftSelect(draft.id);
                  onViewChange('drafts');
                }}>
                  <span>{draft.status}</span>
                  <strong>{draft.title}</strong>
                  <small>{draft.check_history.length} check{draft.check_history.length === 1 ? '' : 's'} · {formatDateTime(draft.updated_at)}</small>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-header">
            <Clock size={18} />
            <h3>Timeline Changes</h3>
            <button className="btn btn-secondary compact-button" type="button" onClick={() => onViewChange('timeline')}>
              Open
            </button>
          </div>
          {recentTimelineEvents.length === 0 ? (
            <p className="text-muted">No timeline events yet.</p>
          ) : (
            <div className="dashboard-list">
              {recentTimelineEvents.map((event) => (
                <button className="dashboard-list-item" key={event.id} type="button" onClick={() => onViewChange('timeline')}>
                  <span>#{event.event_order}</span>
                  <strong>{event.title}</strong>
                  <small>{[event.era_label, event.date_label].filter(Boolean).join(' / ') || `${event.participants.length} linked participant${event.participants.length === 1 ? '' : 's'}`}</small>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-header">
            <ClipboardCheck size={18} />
            <h3>Next Planning Cards</h3>
            <button className="btn btn-secondary compact-button" type="button" onClick={() => onViewChange('planning')}>
              Open
            </button>
          </div>
          {nextPlanningCards.length === 0 ? (
            <p className="text-muted">No planning cards yet.</p>
          ) : (
            <div className="dashboard-list">
              {nextPlanningCards.map((card) => (
                <button className="dashboard-list-item" key={card.id} type="button" onClick={() => onViewChange('planning')}>
                  <span>{card.lane}</span>
                  <strong>{card.title}</strong>
                  <small>{card.boardName}</small>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-header">
            <Flag size={18} />
            <h3>Campaign Notes</h3>
            <button className="btn btn-secondary compact-button" type="button" onClick={() => onViewChange('campaign')}>
              Open
            </button>
          </div>
          {recentCampaignSessions.length === 0 && recentLoreNotes.length === 0 && activeFactionClocks.length === 0 ? (
            <p className="text-muted">No campaign sessions, notes, or active clocks yet.</p>
          ) : (
            <div className="dashboard-list">
              {recentCampaignSessions.map((session) => (
                <button className="dashboard-list-item" key={session.id} type="button" onClick={() => onViewChange('campaign')}>
                  <span>Session {session.session_number}</span>
                  <strong>{session.title}</strong>
                  <small>{session.updated_at ? formatDateTime(session.updated_at) : 'Campaign session'}</small>
                </button>
              ))}
              {recentLoreNotes.map((note) => (
                <button className="dashboard-list-item" key={note.id} type="button" onClick={() => onViewChange('campaign')}>
                  <span>{note.visibility.replace('_', ' ')}</span>
                  <strong>{note.title}</strong>
                  <small>{formatDateTime(note.updated_at)}</small>
                </button>
              ))}
              {activeFactionClocks.map((clock) => (
                <button className="dashboard-list-item" key={clock.id} type="button" onClick={() => onViewChange('campaign')}>
                  <span>{clock.status}</span>
                  <strong>{clock.title}</strong>
                  <small>{clock.filled_segments}/{clock.segments} segments</small>
                </button>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
