import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, Clock, Download, FileText, Plus, Sparkles } from 'lucide-react';
import {
  createDmFactionClock,
  createDmImpactReview,
  createDmLoreNote,
  createDmSession,
  exportDmMarkdown,
  fetchDmFactionClocks,
  fetchDmLoreNotes,
  fetchDmSessions,
  fetchDmSuggestions,
} from '../lib/api/campaign';
import { fetchEntities } from '../lib/api/canon';
import { applySuggestion } from '../lib/api/generation';
import { fetchTimelineEvents } from '../lib/api/planning';
import { fetchWorld } from '../lib/api/worlds';
import type {
  CampaignSession,
  FactionClock,
  GenerationSuggestion,
  LoreNote,
  World,
} from '../lib/apiTypes';
import { formatDateTime } from '../utils/format';
import './WorldDetail.css';
import { buildSuggestionApplyPayload, type SuggestionApplyMode } from './worldDetail/suggestions';

const DM_EXPORT_PRESETS = [
  ['player_handout', 'Player Handout'],
  ['session_brief', 'Session Brief'],
  ['dm_campaign_brief', 'DM Brief'],
] as const;

const WorldDm = () => {
  const { id } = useParams<{ id: string }>();
  const [world, setWorld] = useState<World | null>(null);
  const [sessions, setSessions] = useState<CampaignSession[]>([]);
  const [notes, setNotes] = useState<LoreNote[]>([]);
  const [clocks, setClocks] = useState<FactionClock[]>([]);
  const [suggestions, setSuggestions] = useState<GenerationSuggestion[]>([]);
  const [exportPreset, setExportPreset] = useState<(typeof DM_EXPORT_PRESETS)[number][0]>('dm_campaign_brief');
  const [sessionForm, setSessionForm] = useState({ session_number: 1, title: '', recap: '', player_actions: '', consequences: '' });
  const [noteForm, setNoteForm] = useState({ title: '', body: '', visibility: 'dm_only' as LoreNote['visibility'] });
  const [clockForm, setClockForm] = useState({ title: '', segments: 6, filled_segments: 0, stakes: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const pendingSuggestions = useMemo(
    () => suggestions.filter((suggestion) => suggestion.status === 'pending'),
    [suggestions],
  );

  const loadDmWorkspace = async (worldId: string) => {
    const [worldData, sessionData, noteData, clockData, suggestionData] = await Promise.all([
      fetchWorld(worldId),
      fetchDmSessions(worldId).catch(() => []),
      fetchDmLoreNotes(worldId).catch(() => []),
      fetchDmFactionClocks(worldId).catch(() => []),
      fetchDmSuggestions(worldId).catch(() => []),
    ]);
    setWorld(worldData);
    setSessions(sessionData);
    setNotes(noteData);
    setClocks(clockData);
    setSuggestions(suggestionData);
    setSessionForm((current) => ({
      ...current,
      session_number: sessionData.length ? Math.max(...sessionData.map((session) => session.session_number)) + 1 : current.session_number,
    }));
  };

  useEffect(() => {
    if (!id) return;
    loadDmWorkspace(id)
      .catch(() => setErrorMessage('Unable to load DM workflow.'))
      .finally(() => setLoading(false));
  }, [id]);

  const refreshSuggestions = async () => {
    if (!id) return;
    setSuggestions(await fetchDmSuggestions(id).catch(() => []));
  };

  const handleCreateSession = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !sessionForm.title.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const session = await createDmSession(id, {
        session_number: sessionForm.session_number,
        title: sessionForm.title.trim(),
        played_date: null,
        in_world_date: null,
        recap: sessionForm.recap,
        player_actions: sessionForm.player_actions,
        consequences: sessionForm.consequences,
        linked_entity_ids: [],
        linked_relationship_ids: [],
        linked_timeline_event_ids: [],
      });
      setSessions(await fetchDmSessions(id));
      setSessionForm({ session_number: session.session_number + 1, title: '', recap: '', player_actions: '', consequences: '' });
      setStatusMessage('Session added.');
    } catch {
      setErrorMessage('Unable to create session.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateNote = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !noteForm.title.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createDmLoreNote(id, {
        title: noteForm.title.trim(),
        body: noteForm.body,
        subject_type: 'world',
        subject_id: null,
        visibility: noteForm.visibility,
        truth_state: 'unknown',
        reveal_condition: null,
        handout_text: noteForm.visibility === 'dm_only' ? null : noteForm.body,
      });
      setNotes(await fetchDmLoreNotes(id));
      setNoteForm({ title: '', body: '', visibility: 'dm_only' });
      setStatusMessage('Lore note added.');
    } catch {
      setErrorMessage('Unable to create lore note.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateClock = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !clockForm.title.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createDmFactionClock(id, {
        title: clockForm.title.trim(),
        linked_entity_id: null,
        segments: clockForm.segments,
        filled_segments: clockForm.filled_segments,
        stakes: clockForm.stakes,
        status: 'active',
        linked_session_ids: [],
        linked_entity_ids: [],
        linked_relationship_ids: [],
        linked_timeline_event_ids: [],
      });
      setClocks(await fetchDmFactionClocks(id));
      setClockForm({ title: '', segments: 6, filled_segments: 0, stakes: '' });
      setStatusMessage('Faction clock added.');
    } catch {
      setErrorMessage('Unable to create faction clock.');
    } finally {
      setBusy(false);
    }
  };

  const handleImpactReview = async (sessionId: string) => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const suggestion = await createDmImpactReview(id, sessionId);
      await refreshSuggestions();
      setStatusMessage(`Impact review queued: ${suggestion.suggested_name ?? 'DM suggestion'}.`);
    } catch {
      setErrorMessage('Unable to create impact review.');
    } finally {
      setBusy(false);
    }
  };

  const handleApplySuggestion = async (
    suggestion: GenerationSuggestion,
    mode: Extract<SuggestionApplyMode, 'create_entity' | 'create_timeline_event' | 'create_lore_note' | 'discard'>,
  ) => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await applySuggestion(
        id,
        suggestion.id,
        buildSuggestionApplyPayload(suggestion, mode, {
          fallbackName: 'DM Impact',
          fallbackEntityType: 'Event',
        }),
      );
      await Promise.all([
        refreshSuggestions(),
        fetchDmLoreNotes(id).then(setNotes).catch(() => []),
        fetchTimelineEvents(id).catch(() => []),
        fetchEntities(id).catch(() => []),
      ]);
      setStatusMessage(mode === 'discard' ? 'Suggestion discarded.' : 'Suggestion applied.');
    } catch {
      setErrorMessage('Unable to apply suggestion.');
    } finally {
      setBusy(false);
    }
  };

  const handleExport = async () => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const exported = await exportDmMarkdown(id, exportPreset);
      const blob = new Blob([exported.content], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exported.filename;
      link.click();
      URL.revokeObjectURL(url);
      setStatusMessage('DM Markdown exported.');
    } catch {
      setErrorMessage('Unable to export DM Markdown.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <div className="loading-state" role="status">Loading DM workflow...</div>;

  if (!world) {
    return (
      <div className="empty-state glass">
        <h3>World not found</h3>
        <Link to="/worlds" className="btn btn-primary mt-4">Back to Worlds</Link>
      </div>
    );
  }

  return (
    <div className="world-detail-container">
      <div className="back-nav">
        <Link to={`/worlds/${world.id}`} className="back-link">
          <ArrowLeft size={20} />
          <span>Back to Author Workspace</span>
        </Link>
      </div>

      <div className="world-header">
        <div className="world-header-main">
          <div className="title-section">
            <h1>{world.title} DM Workflow</h1>
            <div className="tags">
              {world.tone && <span className="badge badge-primary">{world.tone}</span>}
              <span className="badge">{sessions.length} sessions</span>
              <span className="badge">{pendingSuggestions.length} pending DM suggestions</span>
            </div>
          </div>
          <div className="world-primary-actions">
            <Link to={`/wiki/${world.id}`} className="btn btn-secondary">
              <BookOpen size={16} />
              Wiki
            </Link>
          </div>
        </div>
        <div className="meta-section" aria-label="DM exports">
          <select
            className="form-input compact-select"
            aria-label="DM export preset"
            value={exportPreset}
            onChange={(event) => setExportPreset(event.target.value as typeof exportPreset)}
          >
            {DM_EXPORT_PRESETS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <button className="btn btn-secondary" onClick={handleExport} disabled={busy} type="button">
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {(statusMessage || errorMessage) && (
        <div className={`workspace-alert ${errorMessage ? 'error' : 'success'}`} role={errorMessage ? 'alert' : 'status'}>
          {errorMessage || statusMessage}
        </div>
      )}

      <div className="demo-review-grid">
        <section className="glass content-section">
          <div className="section-header">
            <FileText className="text-primary" />
            <h2>Sessions</h2>
          </div>
          <form className="planning-form" onSubmit={handleCreateSession}>
            <label className="field-label">
              <span>Session number</span>
              <input className="form-input" type="number" min={1} value={sessionForm.session_number} onChange={(event) => setSessionForm({ ...sessionForm, session_number: Number(event.target.value) })} />
            </label>
            <label className="field-label">
              <span>Session title</span>
              <input className="form-input" value={sessionForm.title} onChange={(event) => setSessionForm({ ...sessionForm, title: event.target.value })} placeholder="Session title" />
            </label>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              <Plus size={16} />
              Add Session
            </button>
            <label className="field-label full-width">
              <span>Recap</span>
              <textarea className="form-input" rows={3} value={sessionForm.recap} onChange={(event) => setSessionForm({ ...sessionForm, recap: event.target.value })} />
            </label>
            <label className="field-label">
              <span>Player actions</span>
              <textarea className="form-input" rows={3} value={sessionForm.player_actions} onChange={(event) => setSessionForm({ ...sessionForm, player_actions: event.target.value })} />
            </label>
            <label className="field-label">
              <span>Consequences</span>
              <textarea className="form-input" rows={3} value={sessionForm.consequences} onChange={(event) => setSessionForm({ ...sessionForm, consequences: event.target.value })} />
            </label>
          </form>
          <div className="planning-board-strip">
            {sessions.length === 0 ? <p className="text-muted">No sessions yet.</p> : sessions.map((session) => (
              <article className="planning-card" key={session.id}>
                <small>Session {session.session_number}</small>
                <strong>{session.title}</strong>
                {session.recap && <span>{session.recap}</span>}
                <button className="btn btn-secondary compact-button" type="button" onClick={() => handleImpactReview(session.id)} disabled={busy}>
                  Review Impact
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="glass content-section">
          <div className="section-header">
            <Sparkles className="text-primary" />
            <h2>DM Suggestions</h2>
            <span className="review-badge">{pendingSuggestions.length} pending</span>
          </div>
          <div className="suggestion-list">
            {suggestions.length === 0 ? <p className="text-muted">No DM suggestions yet.</p> : suggestions.map((suggestion) => (
              <article className="suggestion-item" key={suggestion.id}>
                <div>
                  <strong>{suggestion.suggested_name || 'DM suggestion'}</strong>
                  <p className="text-muted">{suggestion.status} · {formatDateTime(suggestion.created_at)}</p>
                  <pre className="lore-content compact-lore">{suggestion.content}</pre>
                </div>
                <div className="form-actions">
                  {suggestion.status === 'pending' && (
                    <>
                      <button className="btn btn-secondary" type="button" onClick={() => handleApplySuggestion(suggestion, 'create_entity')} disabled={busy}>Canon Entity</button>
                      <button className="btn btn-secondary" type="button" onClick={() => handleApplySuggestion(suggestion, 'create_timeline_event')} disabled={busy}>Timeline Event</button>
                      <button className="btn btn-secondary" type="button" onClick={() => handleApplySuggestion(suggestion, 'create_lore_note')} disabled={busy}>Lore Note</button>
                    </>
                  )}
                  <button className="btn btn-danger" type="button" onClick={() => handleApplySuggestion(suggestion, 'discard')} disabled={busy || suggestion.status !== 'pending'}>Discard</button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="glass content-section">
          <div className="section-header">
            <BookOpen className="text-secondary" />
            <h2>Lore Notes</h2>
          </div>
          <form className="planning-form" onSubmit={handleCreateNote}>
            <label className="field-label">
              <span>Note title</span>
              <input className="form-input" value={noteForm.title} onChange={(event) => setNoteForm({ ...noteForm, title: event.target.value })} placeholder="World note" />
            </label>
            <label className="field-label">
              <span>Visibility</span>
              <select className="form-input" value={noteForm.visibility} onChange={(event) => setNoteForm({ ...noteForm, visibility: event.target.value as LoreNote['visibility'] })}>
                <option value="dm_only">DM only</option>
                <option value="player_visible">Player visible</option>
                <option value="discovered">Discovered</option>
                <option value="redacted">Redacted</option>
              </select>
            </label>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              <Plus size={16} />
              Add Note
            </button>
            <label className="field-label full-width">
              <span>Note body</span>
              <textarea className="form-input" rows={3} value={noteForm.body} onChange={(event) => setNoteForm({ ...noteForm, body: event.target.value })} />
            </label>
          </form>
          <div className="suggestion-list">
            {notes.slice(0, 8).map((note) => (
              <article className="suggestion-item" key={note.id}>
                <div>
                  <strong>{note.title}</strong>
                  <p className="text-muted">{note.visibility.replace('_', ' ')} · {note.truth_state}</p>
                  {note.body && <pre className="lore-content compact-lore">{note.body}</pre>}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="glass content-section">
          <div className="section-header">
            <Clock className="text-primary" />
            <h2>Faction Clocks</h2>
          </div>
          <form className="planning-form" onSubmit={handleCreateClock}>
            <label className="field-label">
              <span>Clock title</span>
              <input className="form-input" value={clockForm.title} onChange={(event) => setClockForm({ ...clockForm, title: event.target.value })} placeholder="Clock title" />
            </label>
            <label className="field-label">
              <span>Segments</span>
              <input className="form-input" min={1} max={20} type="number" value={clockForm.segments} onChange={(event) => setClockForm({ ...clockForm, segments: Number(event.target.value) })} />
            </label>
            <label className="field-label">
              <span>Filled</span>
              <input className="form-input" min={0} max={clockForm.segments} type="number" value={clockForm.filled_segments} onChange={(event) => setClockForm({ ...clockForm, filled_segments: Number(event.target.value) })} />
            </label>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              <Plus size={16} />
              Add Clock
            </button>
            <label className="field-label full-width">
              <span>Stakes</span>
              <input className="form-input" value={clockForm.stakes} onChange={(event) => setClockForm({ ...clockForm, stakes: event.target.value })} />
            </label>
          </form>
          <div className="planning-board-strip">
            {clocks.map((clock) => (
              <article className="planning-card" key={clock.id}>
                <small>{clock.status}</small>
                <strong>{clock.title}</strong>
                <span>{clock.filled_segments}/{clock.segments} segments</span>
                {clock.stakes && <span>{clock.stakes}</span>}
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default WorldDm;
