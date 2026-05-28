import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Activity,
  Bot,
  BookOpen,
  Check,
  ClipboardCheck,
  Clock,
  Download,
  EyeOff,
  FileText,
  Flag,
  Link2,
  Network,
  Pencil,
  Plus,
  RefreshCcw,
  Save,
  Search,
  Sparkles,
  Trash2,
} from 'lucide-react';
import {
  applySuggestion,
  createCampaignImpactReview,
  createCampaignSession,
  createFactionClock,
  createLoreNote,
  checkDraft,
  checkPassage,
  createTimelineEvent,
  createEntity,
  createDraft,
  createGraphView,
  createPlanningBoard,
  createPlanningCard,
  createRelationship,
  deleteEntity,
  deleteWorld,
  deleteRelationship,
  exportMarkdown,
  extractDraftExcerpt,
  fetchConsistencyIssues,
  fetchConsistencyReport,
  fetchCampaignSessions,
  fetchEntities,
  fetchFactionClocks,
  fetchGraphViews,
  fetchHealth,
  fetchDrafts,
  fetchLoreNotes,
  fetchPlanningBoards,
  fetchRelationships,
  fetchRevisions,
  fetchSuggestions,
  fetchTimelineEvents,
  fetchWorld,
  generateAgentic,
  restoreRevision,
  updateConsistencyIssue,
  type CampaignSession,
  type ConsistencyIssueState,
  type ConsistencyIssueStatus,
  updateEntity,
  updateDraft,
  type ConsistencyReport,
  type DraftPassage,
  type Entity,
  type FactionClock,
  type GenerationSuggestion,
  type GraphLayoutMode,
  type GraphView,
  type HealthStatus,
  type LoreNote,
  type PassageCheck,
  type PlanningBoard,
  type Relationship,
  type RevisionVersion,
  type TimelineEvent,
  type World,
} from '../lib/api';
import { buildWorldGraph, searchWorldGraph } from '../lib/worldGraph';
import './WorldDetail.css';

const WorldGraphView = lazy(() => import('./WorldGraphView'));

const ENTITY_GROUPS = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
const ENTITY_TYPES = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
const EXPORT_PRESETS = [
  ['full_bible', 'Full Bible'],
  ['character_dossier', 'Characters'],
  ['faction_brief', 'Factions'],
  ['location_gazetteer', 'Locations'],
  ['timeline_only', 'Timeline'],
  ['obsidian', 'Obsidian'],
  ['player_handout', 'Player Handout'],
  ['session_brief', 'Session Brief'],
  ['dm_campaign_brief', 'DM Brief'],
] as const;
const GRAPH_LAYOUTS: { value: GraphLayoutMode; label: string }[] = [
  { value: 'manual', label: 'Manual' },
  { value: 'force', label: 'Relationship' },
  { value: 'type_columns', label: 'Type columns' },
  { value: 'faction_clusters', label: 'Faction clusters' },
  { value: 'timeline_order', label: 'Timeline' },
];
const TEMPLATE_FIELDS: Record<string, string[]> = {
  Character: ['goal', 'secret', 'fear', 'voice'],
  Location: ['hazards', 'economy', 'culture', 'landmark'],
  Faction: ['resources', 'rivals', 'public_goal', 'secret'],
  Event: ['causes', 'consequences', 'participants', 'date'],
  Concept: ['rules', 'limits', 'cost', 'symbols'],
  Other: ['role', 'origin', 'constraints'],
};
const PROMPTS = [
  {
    label: 'Faction Pressure',
    value: 'For The Ember Archipelago, generate three factions with public goals, secret leverage, scarce resources, and one unresolved conflict tying each faction to existing canon.',
  },
  {
    label: 'Timeline Crisis',
    value: 'For The Ember Archipelago, generate five escalating timeline events around the Night of Falling Bells, each with a cause, consequence, and entity most changed by it.',
  },
  {
    label: 'Secrets',
    value: 'For The Ember Archipelago, generate four canon-safe secrets. Each secret should name who knows it, who would suffer if revealed, and which saved entity it complicates.',
  },
  {
    label: 'Expand Selected',
    value: 'Expand the selected entity with history, sensory details, story pressure, a secret, and two relationship hooks that can be added to canon.',
  },
];

type EntityForm = Pick<Entity, 'name' | 'entity_type' | 'description' | 'structured_fields'>;
type WorkspaceView = 'canon' | 'drafts' | 'timeline' | 'planning' | 'campaign' | 'graph';

const blankEntity: EntityForm = {
  name: '',
  entity_type: 'Character',
  description: '',
  structured_fields: {},
};

const displayType = (type: string) => {
  const normalized = type.trim().toLowerCase();
  if (['character', 'person', 'historical figure'].includes(normalized)) return 'Character';
  if (['location', 'city', 'region', 'landmark', 'continent'].includes(normalized)) return 'Location';
  if (['faction', 'guild', 'kingdom', 'organization'].includes(normalized)) return 'Faction';
  if (['concept', 'magic system', 'technology', 'term'].includes(normalized)) return 'Concept';
  if (['event', 'historical event', 'battle'].includes(normalized)) return 'Event';
  return 'Other';
};

const WorldDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [world, setWorld] = useState<World | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [suggestions, setSuggestions] = useState<GenerationSuggestion[]>([]);
  const [drafts, setDrafts] = useState<DraftPassage[]>([]);
  const [selectedDraftId, setSelectedDraftId] = useState<string | null>(null);
  const [draftForm, setDraftForm] = useState({ title: '', body: '' });
  const [draftSelection, setDraftSelection] = useState('');
  const [draftInstruction, setDraftInstruction] = useState('');
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [graphViews, setGraphViews] = useState<GraphView[]>([]);
  const [planningBoards, setPlanningBoards] = useState<PlanningBoard[]>([]);
  const [campaignSessions, setCampaignSessions] = useState<CampaignSession[]>([]);
  const [loreNotes, setLoreNotes] = useState<LoreNote[]>([]);
  const [factionClocks, setFactionClocks] = useState<FactionClock[]>([]);
  const [revisions, setRevisions] = useState<RevisionVersion[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<WorkspaceView>('canon');
  const [showAllRelationships, setShowAllRelationships] = useState(false);
  const [showAllTimeline, setShowAllTimeline] = useState(false);
  const [confirmReplaceGenerated, setConfirmReplaceGenerated] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [graphTypeFilter, setGraphTypeFilter] = useState('All');
  const [graphLayoutMode, setGraphLayoutMode] = useState<GraphLayoutMode>('manual');
  const [graphViewName, setGraphViewName] = useState('');
  const [graphPositions, setGraphPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [graphResetKey, setGraphResetKey] = useState(0);
  const [entityForm, setEntityForm] = useState<EntityForm>(blankEntity);
  const [relationshipForm, setRelationshipForm] = useState({
    source_entity_id: '',
    target_entity_id: '',
    relation_type: '',
    notes: '',
    category: '',
    strength: 3,
    history: '',
  });
  const [timelineForm, setTimelineForm] = useState({
    title: '',
    event_order: 1,
    description: '',
    causes: '',
    consequences: '',
    date_label: '',
    era_label: '',
    depends_on: '',
  });
  const [planningForm, setPlanningForm] = useState({
    boardName: '',
    boardType: 'plot_thread' as PlanningBoard['board_type'],
    cardTitle: '',
    cardLane: 'Draft',
  });
  const [campaignForm, setCampaignForm] = useState({
    sessionTitle: '',
    sessionNumber: 1,
    recap: '',
    noteTitle: '',
    noteBody: '',
    noteVisibility: 'dm_only' as LoreNote['visibility'],
    clockTitle: '',
    clockSegments: 6,
    clockFilled: 0,
    clockStakes: '',
  });
  const [passageText, setPassageText] = useState('');
  const [passageReport, setPassageReport] = useState<PassageCheck | null>(null);
  const [exportPreset, setExportPreset] = useState<(typeof EXPORT_PRESETS)[number][0]>('full_bible');
  const [issueStates, setIssueStates] = useState<ConsistencyIssueState[]>([]);
  const [issueNotes, setIssueNotes] = useState<Record<string, string>>({});
  const [agenticInstruction, setAgenticInstruction] = useState('');
  const [saveGenerated, setSaveGenerated] = useState(false);
  const [generatedName, setGeneratedName] = useState('');
  const [generatedType, setGeneratedType] = useState('Concept');
  const [agenticResult, setAgenticResult] = useState<{ content: string; entity_id?: string } | null>(null);
  const [report, setReport] = useState<ConsistencyReport | null>(null);
  const [markdownPreview, setMarkdownPreview] = useState<{ filename: string; content: string } | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const selectedEntity = useMemo(
    () => entities.find((entity) => entity.id === selectedEntityId) ?? null,
    [entities, selectedEntityId],
  );

  const selectedRelationship = useMemo(
    () => relationships.find((relationship) => relationship.id === selectedRelationshipId) ?? null,
    [relationships, selectedRelationshipId],
  );

  const selectedDraft = useMemo(
    () => drafts.find((draft) => draft.id === selectedDraftId) ?? null,
    [drafts, selectedDraftId],
  );

  const entityFormDirty = useMemo(
    () => Boolean(selectedEntity) && (
      entityForm.name !== selectedEntity?.name
      || entityForm.entity_type !== selectedEntity?.entity_type
      || entityForm.description !== selectedEntity?.description
    ),
    [entityForm, selectedEntity],
  );

  const searchResult = useMemo(
    () => searchWorldGraph(entities, relationships, searchQuery),
    [entities, relationships, searchQuery],
  );

  const groupedEntities = useMemo(
    () =>
      ENTITY_GROUPS.map((group) => ({
        group,
        items: searchResult.filteredEntities.filter((entity) => displayType(entity.entity_type) === group),
      })),
    [searchResult.filteredEntities],
  );

  const pendingSuggestions = useMemo(
    () => suggestions.filter((suggestion) => suggestion.status === 'pending'),
    [suggestions],
  );

  const archivedIssueStates = useMemo(
    () => issueStates.filter((issue) => issue.status === 'ignored' || issue.status === 'resolved'),
    [issueStates],
  );

  const templateFields = useMemo(
    () => TEMPLATE_FIELDS[displayType(entityForm.entity_type)] ?? TEMPLATE_FIELDS.Other,
    [entityForm.entity_type],
  );

  const graphEntities = useMemo(
    () => entities.filter((entity) => (
      graphTypeFilter === 'All' || displayType(entity.entity_type) === graphTypeFilter
    )),
    [entities, graphTypeFilter],
  );

  const graphRelationships = useMemo(() => {
    const entityIds = new Set(graphEntities.map((entity) => entity.id));
    return relationships.filter((relationship) => (
      entityIds.has(relationship.source_entity_id) && entityIds.has(relationship.target_entity_id)
    ));
  }, [graphEntities, relationships]);

  const graphHighlights = useMemo(() => {
    const entityIds = new Set(searchResult.highlightedEntityIds);
    const relationshipIds = new Set(searchResult.highlightedRelationshipIds);
    if (selectedEntityId) {
      entityIds.add(selectedEntityId);
      relationships.forEach((relationship) => {
        if (
          relationship.source_entity_id === selectedEntityId
          || relationship.target_entity_id === selectedEntityId
        ) {
          relationshipIds.add(relationship.id);
          entityIds.add(relationship.source_entity_id);
          entityIds.add(relationship.target_entity_id);
        }
      });
    }
    return { entityIds, relationshipIds };
  }, [relationships, searchResult.highlightedEntityIds, searchResult.highlightedRelationshipIds, selectedEntityId]);

  const graphData = useMemo(
    () => buildWorldGraph(
      graphEntities,
      graphRelationships,
      selectedEntityId,
      selectedRelationshipId,
      graphHighlights.entityIds,
      graphHighlights.relationshipIds,
      graphPositions,
      graphLayoutMode,
      timelineEvents,
    ),
    [
      graphEntities,
      graphRelationships,
      selectedEntityId,
      selectedRelationshipId,
      graphHighlights.entityIds,
      graphHighlights.relationshipIds,
      graphPositions,
      graphLayoutMode,
      timelineEvents,
    ],
  );

  const graphRelationshipRows = useMemo(() => {
    const entityNames = new Map(graphEntities.map((entity) => [entity.id, entity.name]));
    return graphRelationships.map((relationship) => ({
      ...relationship,
      sourceName: entityNames.get(relationship.source_entity_id) ?? relationship.source_entity_name,
      targetName: entityNames.get(relationship.target_entity_id) ?? relationship.target_entity_name,
    }));
  }, [graphEntities, graphRelationships]);

  const visibleRelationships = useMemo(() => {
    if (!selectedEntityId || showAllRelationships) return relationships;
    return relationships.filter((relationship) => (
      relationship.source_entity_id === selectedEntityId || relationship.target_entity_id === selectedEntityId
    ));
  }, [relationships, selectedEntityId, showAllRelationships]);

  const visibleTimelineEvents = useMemo(() => {
    if (!selectedEntityId || showAllTimeline) return timelineEvents;
    return timelineEvents.filter((event) => event.participants.includes(selectedEntityId));
  }, [selectedEntityId, showAllTimeline, timelineEvents]);

  const selectedContextLabel = selectedEntity ? selectedEntity.name : 'selected entity';

  const loadWorkspace = async (worldId: string) => {
    setErrorMessage('');
    const [worldData, entityData, relationshipData, suggestionData, timelineData, graphViewData, boardData, sessionData, noteData, clockData, draftData, healthData] = await Promise.all([
      fetchWorld(worldId),
      fetchEntities(worldId),
      fetchRelationships(worldId),
      fetchSuggestions(worldId).catch(() => []),
      fetchTimelineEvents(worldId).catch(() => []),
      fetchGraphViews(worldId).catch(() => []),
      fetchPlanningBoards(worldId).catch(() => []),
      fetchCampaignSessions(worldId).catch(() => []),
      fetchLoreNotes(worldId).catch(() => []),
      fetchFactionClocks(worldId).catch(() => []),
      fetchDrafts(worldId).catch(() => []),
      fetchHealth().catch(() => null),
    ]);
    setWorld(worldData);
    setEntities(entityData);
    setRelationships(relationshipData);
    setSuggestions(suggestionData);
    setTimelineEvents(timelineData);
    setGraphViews(graphViewData);
    setPlanningBoards(boardData);
    setCampaignSessions(sessionData);
    setLoreNotes(noteData);
    setFactionClocks(clockData);
    setDrafts(draftData);
    const nextDraft = draftData[0] ?? null;
    setSelectedDraftId((current) => current ?? nextDraft?.id ?? null);
    if (nextDraft) {
      setDraftForm((current) => current.title || current.body ? current : { title: nextDraft.title, body: nextDraft.body });
    }
    setHealth(healthData);
    setSelectedEntityId((current) => current ?? entityData[0]?.id ?? null);
  };

  useEffect(() => {
    if (!id) return;
    const savedPositions = window.localStorage.getItem(`world-graph-positions:${id}`);
    try {
      setGraphPositions(savedPositions ? JSON.parse(savedPositions) : {});
    } catch {
      setGraphPositions({});
    }
    loadWorkspace(id)
      .catch(() => setErrorMessage('Unable to load this world.'))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    window.localStorage.setItem(`world-graph-positions:${id}`, JSON.stringify(graphPositions));
  }, [graphPositions, id]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!entityFormDirty) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [entityFormDirty]);

  useEffect(() => {
    if (selectedEntity) {
      setEntityForm({
        name: selectedEntity.name,
        entity_type: selectedEntity.entity_type,
        description: selectedEntity.description,
        structured_fields: selectedEntity.structured_fields ?? {},
      });
      if (id) {
        fetchRevisions(id, selectedEntity.id).then(setRevisions).catch(() => setRevisions([]));
      }
    } else {
      setEntityForm(blankEntity);
      setRevisions([]);
    }
  }, [id, selectedEntity]);

  useEffect(() => {
    if (!selectedDraft) return;
    setDraftForm({ title: selectedDraft.title, body: selectedDraft.body });
    setDraftSelection('');
  }, [selectedDraft]);

  const refreshEntities = async () => {
    if (!id) return;
    const [entityData, relationshipData] = await Promise.all([
      fetchEntities(id),
      fetchRelationships(id),
    ]);
    setEntities(entityData);
    setRelationships(relationshipData);
  };

  const refreshReviewData = async () => {
    if (!id) return;
    const [suggestionData, timelineData] = await Promise.all([
      fetchSuggestions(id).catch(() => []),
      fetchTimelineEvents(id).catch(() => []),
    ]);
    setSuggestions(suggestionData);
    setTimelineEvents(timelineData);
  };

  const refreshDrafts = async () => {
    if (!id) return;
    const draftData = await fetchDrafts(id).catch(() => []);
    setDrafts(draftData);
    setSelectedDraftId((current) => current ?? draftData[0]?.id ?? null);
  };

  const handleDraftSelect = (draftId: string) => {
    const draft = drafts.find((item) => item.id === draftId);
    setSelectedDraftId(draftId || null);
    if (draft) setDraftForm({ title: draft.title, body: draft.body });
    setDraftSelection('');
  };

  const selectEntity = (entityId: string | null) => {
    if (entityFormDirty && !window.confirm('Discard unsaved entity edits?')) return;
    setSelectedEntityId(entityId);
    setSelectedRelationshipId(null);
  };

  const handleDraftSave = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !draftForm.title.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const saved = selectedDraft
        ? await updateDraft(id, selectedDraft.id, { title: draftForm.title.trim(), body: draftForm.body })
        : await createDraft(id, { title: draftForm.title.trim(), body: draftForm.body });
      await refreshDrafts();
      setSelectedDraftId(saved.id);
      setDraftSelection('');
      setStatusMessage(selectedDraft ? 'Draft saved.' : 'Draft created.');
    } catch {
      setErrorMessage('Unable to save draft.');
    } finally {
      setBusy(false);
    }
  };

  const handleDraftTextSelect = (event: React.SyntheticEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget;
    setDraftSelection(target.value.slice(target.selectionStart, target.selectionEnd).trim());
  };

  const handleDraftExtract = async () => {
    if (!id || !selectedDraft || !draftSelection) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const result = await extractDraftExcerpt(id, selectedDraft.id, {
        excerpt: draftSelection,
        instruction: draftInstruction.trim() || undefined,
        max_candidates: 6,
      });
      await refreshReviewData();
      setStatusMessage(`${result.suggestions.length} canon suggestion(s) queued.`);
    } catch {
      setErrorMessage('Unable to extract canon suggestions from draft selection.');
    } finally {
      setBusy(false);
    }
  };

  const handleDraftCheck = async () => {
    if (!id || !selectedDraft) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const reportResult = await checkDraft(id, selectedDraft.id);
      setPassageReport(reportResult);
      await refreshDrafts();
      setStatusMessage(reportResult.summary);
    } catch {
      setErrorMessage('Unable to check draft.');
    } finally {
      setBusy(false);
    }
  };

  const handleEntitySubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !entityForm.name.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const saved = selectedEntity
        ? await updateEntity(id, selectedEntity.id, entityForm)
        : await createEntity(id, entityForm);
      await refreshEntities();
      setSelectedEntityId(saved.id);
      setStatusMessage(selectedEntity ? 'Entity updated.' : 'Entity created.');
    } catch {
      setErrorMessage('Unable to save entity.');
    } finally {
      setBusy(false);
    }
  };

  const handleDuplicateEntity = async () => {
    if (!id || !selectedEntity) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const copy = await createEntity(id, {
        name: `${selectedEntity.name} Copy`,
        entity_type: selectedEntity.entity_type,
        description: selectedEntity.description,
      });
      await refreshEntities();
      setSelectedEntityId(copy.id);
      setStatusMessage('Entity duplicated.');
    } catch {
      setErrorMessage('Unable to duplicate entity.');
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteEntity = async () => {
    if (!id || !selectedEntity) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await deleteEntity(id, selectedEntity.id);
      await refreshEntities();
      setSelectedEntityId(null);
      setStatusMessage('Entity deleted.');
    } catch {
      setErrorMessage('Unable to delete entity.');
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteWorld = async () => {
    if (!id || !world) return;
    const confirmation = window.prompt(`Type "${world.title}" to delete this world and all of its entities and relationships.`);
    if (confirmation !== world.title) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await deleteWorld(id);
      navigate('/worlds');
    } catch {
      setErrorMessage('Unable to delete this world.');
    } finally {
      setBusy(false);
    }
  };

  const handleAgenticGen = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !agenticInstruction.trim()) return;
    setGenerating(true);
    setErrorMessage('');
    try {
      const result = await generateAgentic(
        id,
        agenticInstruction,
        saveGenerated && generatedName.trim()
          ? { entityType: generatedType, name: generatedName.trim() }
          : undefined,
      );
      setAgenticResult(result);
      if (result.entity_id) {
        await refreshEntities();
        setSelectedEntityId(result.entity_id);
        setStatusMessage('Generated lore saved.');
      } else {
        await refreshReviewData();
        setStatusMessage('Generated lore added to the canon inbox.');
      }
    } catch {
      setErrorMessage('Unable to generate lore.');
    } finally {
      setGenerating(false);
    }
  };

  const resetGeneratorState = () => {
    setAgenticInstruction('');
    setSaveGenerated(false);
    setGeneratedName('');
    setGeneratedType('Concept');
    setAgenticResult(null);
    setConfirmReplaceGenerated(false);
  };

  const handleApplyGenerated = async (mode: 'append' | 'replace') => {
    if (!id || !selectedEntity || !agenticResult) return;
    if (mode === 'replace' && !confirmReplaceGenerated) {
      setConfirmReplaceGenerated(true);
      return;
    }
    const description =
      mode === 'append'
        ? `${selectedEntity.description.trim()}\n\n${agenticResult.content}`.trim()
        : agenticResult.content;
    setBusy(true);
    try {
      const updated = await updateEntity(id, selectedEntity.id, { description });
      await refreshEntities();
      setSelectedEntityId(updated.id);
      setStatusMessage(mode === 'append' ? 'Generated lore appended.' : 'Description replaced.');
      resetGeneratorState();
    } catch {
      setErrorMessage('Unable to apply generated lore.');
    } finally {
      setBusy(false);
    }
  };

  const handleSaveGeneratedAsEntity = async () => {
    if (!id || !agenticResult || !generatedName.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const created = await createEntity(id, {
        name: generatedName.trim(),
        entity_type: generatedType,
        description: agenticResult.content,
      });
      await refreshEntities();
      setSelectedEntityId(created.id);
      setStatusMessage('Generated lore saved as a new entity.');
      resetGeneratorState();
    } catch {
      setErrorMessage('Unable to save generated lore as an entity.');
    } finally {
      setBusy(false);
    }
  };

  const handleRelationshipSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (
      !id
      || !relationshipForm.source_entity_id
      || !relationshipForm.target_entity_id
      || !relationshipForm.relation_type.trim()
      || relationshipForm.source_entity_id === relationshipForm.target_entity_id
    ) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createRelationship(id, {
        ...relationshipForm,
        relation_type: relationshipForm.relation_type.trim(),
        notes: relationshipForm.notes || undefined,
        category: relationshipForm.category || undefined,
        strength: relationshipForm.strength || undefined,
        stance: relationshipForm.category.toLowerCase() === 'alliance'
          ? 'alliance'
          : relationshipForm.category.toLowerCase() === 'conflict'
            ? 'conflict'
            : undefined,
      });
      setRelationshipForm({
        source_entity_id: '',
        target_entity_id: '',
        relation_type: '',
        notes: '',
        category: '',
        strength: 3,
        history: '',
      });
      setRelationships(await fetchRelationships(id));
      setStatusMessage('Relationship created.');
    } catch {
      setErrorMessage('Unable to create relationship.');
    } finally {
      setBusy(false);
    }
  };

  const handleExport = async () => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const exported = await exportMarkdown(id, exportPreset);
      const blob = new Blob([exported.content], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exported.filename;
      link.click();
      URL.revokeObjectURL(url);
      setStatusMessage('Markdown exported.');
    } catch {
      setErrorMessage('Unable to export Markdown.');
    } finally {
      setBusy(false);
    }
  };

  const handlePreviewExport = async () => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const exported = await exportMarkdown(id, exportPreset);
      setMarkdownPreview({ filename: exported.filename, content: exported.content });
      setStatusMessage('Markdown preview ready.');
    } catch {
      setErrorMessage('Unable to preview Markdown.');
    } finally {
      setBusy(false);
    }
  };

  const handleConsistencyReport = async () => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const [nextReport, nextIssueStates] = await Promise.all([
        fetchConsistencyReport(id),
        fetchConsistencyIssues(id),
      ]);
      setReport(nextReport);
      setIssueStates(nextIssueStates);
      setIssueNotes(Object.fromEntries(
        [
          ...nextReport.issues
            .filter((issue) => issue.issue_id)
            .map((issue) => [issue.issue_id as string, issue.note ?? '']),
          ...nextIssueStates.map((issue) => [issue.id, issue.note ?? '']),
        ],
      ));
      setStatusMessage('Consistency report ready.');
    } catch {
      setErrorMessage('Unable to run consistency report.');
    } finally {
      setBusy(false);
    }
  };

  const handleIssueUpdate = async (
    issue: ConsistencyReport['issues'][number],
    payload: { status?: ConsistencyIssueStatus; note?: string | null },
  ) => {
    if (!id || !issue.issue_id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const updated = await updateConsistencyIssue(id, issue.issue_id, payload);
      setReport((current) => current ? {
        ...current,
        issues: current.issues
          .map((item) => item.issue_id === updated.id ? {
            ...item,
            status: updated.status,
            note: updated.note,
            first_seen: updated.first_seen,
            last_seen: updated.last_seen,
          } : item)
          .filter((item) => item.status !== 'ignored' && item.status !== 'resolved'),
      } : current);
      setIssueStates((current) => current.map((item) => item.id === updated.id ? updated : item));
      setIssueNotes((current) => ({ ...current, [updated.id]: updated.note ?? '' }));
      setStatusMessage(payload.note !== undefined ? 'Issue note saved.' : 'Issue updated.');
    } catch {
      setErrorMessage('Unable to update issue.');
    } finally {
      setBusy(false);
    }
  };

  const handleIssueStateUpdate = async (
    issue: ConsistencyIssueState,
    payload: { status?: ConsistencyIssueStatus; note?: string | null },
  ) => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const updated = await updateConsistencyIssue(id, issue.id, payload);
      setIssueStates((current) => current.map((item) => item.id === updated.id ? updated : item));
      setIssueNotes((current) => ({ ...current, [updated.id]: updated.note ?? '' }));
      if (updated.status === 'open' || updated.status === 'reopened') {
        setReport(await fetchConsistencyReport(id));
      }
      setStatusMessage(payload.note !== undefined ? 'Issue note saved.' : 'Issue reopened.');
    } catch {
      setErrorMessage('Unable to update issue.');
    } finally {
      setBusy(false);
    }
  };

  const handleSuggestionApply = async (
    suggestion: GenerationSuggestion,
    mode: 'create_entity' | 'append_to_entity' | 'replace_entity' | 'discard' | 'create_relationship' | 'create_timeline_event' | 'create_lore_note',
  ) => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const result = await applySuggestion(id, suggestion.id, {
        mode,
        entity_id: mode === 'create_entity' || mode === 'discard' ? undefined : selectedEntityId ?? undefined,
        name: generatedName.trim() || suggestion.suggested_name || 'Generated Lore',
        entity_type: generatedType || suggestion.suggested_type || 'Concept',
      });
      await Promise.all([refreshEntities(), refreshReviewData(), fetchLoreNotes(id).then(setLoreNotes).catch(() => [])]);
      if (result.entity?.id) setSelectedEntityId(result.entity.id);
      setStatusMessage(mode === 'discard' ? 'Suggestion discarded.' : 'Suggestion applied to canon.');
    } catch {
      setErrorMessage('Unable to apply suggestion.');
    } finally {
      setBusy(false);
    }
  };

  const handleTimelineSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !timelineForm.title.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createTimelineEvent(id, {
        title: timelineForm.title.trim(),
        event_order: timelineForm.event_order,
        description: timelineForm.description,
        participants: selectedEntityId ? [selectedEntityId] : [],
        causes: timelineForm.causes || null,
        consequences: timelineForm.consequences || null,
        date_label: timelineForm.date_label || null,
        era_label: timelineForm.era_label || null,
        depends_on: timelineForm.depends_on ? [timelineForm.depends_on] : [],
      });
      setTimelineForm({
        title: '',
        event_order: timelineForm.event_order + 1,
        description: '',
        causes: '',
        consequences: '',
        date_label: '',
        era_label: timelineForm.era_label,
        depends_on: '',
      });
      setTimelineEvents(await fetchTimelineEvents(id));
      setStatusMessage('Timeline event created.');
    } catch {
      setErrorMessage('Unable to create timeline event.');
    } finally {
      setBusy(false);
    }
  };

  const handlePassageCheck = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !passageText.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      setPassageReport(await checkPassage(id, passageText));
      setStatusMessage('Passage check complete.');
    } catch {
      setErrorMessage('Unable to check passage.');
    } finally {
      setBusy(false);
    }
  };

  const handleRestoreRevision = async (revisionId: string) => {
    if (!id) return;
    setBusy(true);
    setErrorMessage('');
    try {
      const restored = await restoreRevision(id, revisionId);
      await refreshEntities();
      setSelectedEntityId(restored.id);
      setStatusMessage('Revision restored.');
    } catch {
      setErrorMessage('Unable to restore revision.');
    } finally {
      setBusy(false);
    }
  };

  const downloadMarkdown = (filename: string, content: string) => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    setStatusMessage('Markdown exported.');
  };

  const handleIssueSelect = (issue: ConsistencyReport['issues'][number]) => {
    setActiveView('canon');
    if (issue.entity_id) {
      selectEntity(issue.entity_id);
      return;
    }
    if (issue.relationship_id) {
      const relationship = relationships.find((item) => item.id === issue.relationship_id);
      if (relationship) {
        selectEntity(relationship.source_entity_id);
      }
      setSelectedRelationshipId(issue.relationship_id);
    }
  };

  const handleResetGraph = () => {
    setGraphPositions({});
    setGraphLayoutMode('manual');
    setGraphResetKey((current) => current + 1);
    if (id) {
      window.localStorage.removeItem(`world-graph-positions:${id}`);
    }
  };

  const handleCreateEntityFromGraph = () => {
    setActiveView('canon');
    selectEntity(null);
  };

  const handleSaveGraphView = async () => {
    if (!id || !graphViewName.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createGraphView(id, {
        name: graphViewName.trim(),
        layout_mode: graphLayoutMode,
        filters: { entity_type: graphTypeFilter },
        camera: { x: 0, y: 0, zoom: 1 },
        node_positions: graphPositions,
      });
      setGraphViews(await fetchGraphViews(id));
      setGraphViewName('');
      setStatusMessage('Graph view saved.');
    } catch {
      setErrorMessage('Unable to save graph view.');
    } finally {
      setBusy(false);
    }
  };

  const applyGraphView = (view: GraphView) => {
    setGraphLayoutMode(view.layout_mode);
    setGraphTypeFilter(typeof view.filters.entity_type === 'string' ? view.filters.entity_type : 'All');
    setGraphPositions(view.node_positions ?? {});
    setGraphResetKey((current) => current + 1);
  };

  const handleCreatePlanningBoard = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !planningForm.boardName.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createPlanningBoard(id, {
        name: planningForm.boardName.trim(),
        board_type: planningForm.boardType,
      });
      setPlanningBoards(await fetchPlanningBoards(id));
      setPlanningForm((current) => ({ ...current, boardName: '' }));
      setStatusMessage('Planning board created.');
    } catch {
      setErrorMessage('Unable to create planning board.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreatePlanningCard = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !planningBoards[0] || !planningForm.cardTitle.trim()) return;
    setBusy(true);
    setErrorMessage('');
    try {
      await createPlanningCard(id, planningBoards[0].id, {
        title: planningForm.cardTitle.trim(),
        description: selectedEntity ? `Linked to ${selectedEntity.name}` : '',
        lane: planningForm.cardLane,
        position: planningBoards[0].cards.length + 1,
        entity_links: selectedEntityId ? [selectedEntityId] : [],
        relationship_links: selectedRelationshipId ? [selectedRelationshipId] : [],
        timeline_event_links: [],
      });
      setPlanningBoards(await fetchPlanningBoards(id));
      setPlanningForm((current) => ({ ...current, cardTitle: '' }));
      setStatusMessage('Planning card linked to canon.');
    } catch {
      setErrorMessage('Unable to create planning card.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateCampaignSession = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !campaignForm.sessionTitle.trim()) return;
    setBusy(true);
    try {
      const session = await createCampaignSession(id, {
        session_number: campaignForm.sessionNumber,
        title: campaignForm.sessionTitle.trim(),
        played_date: null,
        in_world_date: null,
        recap: campaignForm.recap,
        player_actions: '',
        consequences: '',
        linked_entity_ids: selectedEntityId ? [selectedEntityId] : [],
        linked_relationship_ids: selectedRelationshipId ? [selectedRelationshipId] : [],
        linked_timeline_event_ids: [],
      });
      setCampaignSessions(await fetchCampaignSessions(id));
      setCampaignForm((current) => ({
        ...current,
        sessionTitle: '',
        sessionNumber: session.session_number + 1,
        recap: '',
      }));
      setStatusMessage('Campaign session added.');
    } catch {
      setErrorMessage('Unable to create campaign session.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateLoreNote = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !campaignForm.noteTitle.trim()) return;
    setBusy(true);
    try {
      await createLoreNote(id, {
        title: campaignForm.noteTitle.trim(),
        body: campaignForm.noteBody,
        subject_type: selectedEntityId ? 'entity' : 'world',
        subject_id: selectedEntityId,
        visibility: campaignForm.noteVisibility,
        truth_state: 'unknown',
        reveal_condition: null,
        handout_text: campaignForm.noteVisibility === 'dm_only' ? null : campaignForm.noteBody,
      });
      setLoreNotes(await fetchLoreNotes(id));
      setCampaignForm((current) => ({ ...current, noteTitle: '', noteBody: '' }));
      setStatusMessage('Lore note added.');
    } catch {
      setErrorMessage('Unable to create lore note.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateFactionClock = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !campaignForm.clockTitle.trim()) return;
    setBusy(true);
    try {
      await createFactionClock(id, {
        title: campaignForm.clockTitle.trim(),
        linked_entity_id: selectedEntityId,
        segments: campaignForm.clockSegments,
        filled_segments: campaignForm.clockFilled,
        stakes: campaignForm.clockStakes,
        status: 'active',
        linked_session_ids: [],
        linked_entity_ids: selectedEntityId ? [selectedEntityId] : [],
        linked_relationship_ids: [],
        linked_timeline_event_ids: [],
      });
      setFactionClocks(await fetchFactionClocks(id));
      setCampaignForm((current) => ({ ...current, clockTitle: '', clockFilled: 0, clockStakes: '' }));
      setStatusMessage('Faction clock added.');
    } catch {
      setErrorMessage('Unable to create faction clock.');
    } finally {
      setBusy(false);
    }
  };

  const handleCampaignImpactReview = async (sessionId: string) => {
    if (!id) return;
    setBusy(true);
    try {
      const suggestion = await createCampaignImpactReview(id, sessionId);
      setSuggestions(await fetchSuggestions(id));
      setStatusMessage(`Impact review queued: ${suggestion.suggested_name ?? 'campaign suggestion'}.`);
    } catch {
      setErrorMessage('Unable to create impact review.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="loading-state" role="status">Loading world workspace...</div>;
  }

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
        <Link to="/worlds" className="back-link">
          <ArrowLeft size={20} />
          <span>Back to Worlds</span>
        </Link>
      </div>

      <div className="world-header">
        <div className="title-section">
          <h1>{world.title}</h1>
          <div className="tags">
            {world.tone && <span className="badge badge-primary">{world.tone}</span>}
          <span className="badge">{entities.length} entities</span>
          <span className={`badge ${health?.llm.enabled ? 'badge-good' : 'badge-muted'}`}>
            <Activity size={13} />
            {health ? `LLM ${health.llm.enabled ? 'ready' : 'stub'}` : 'Backend unknown'}
          </span>
        </div>
      </div>
      <div className="meta-section">
          <div className="meta-item">
            <Clock size={16} />
            <span>Created {new Date(world.created_at).toLocaleDateString()}</span>
          </div>
          <Link to={`/wiki/${world.id}`} className="btn btn-primary">
            <BookOpen size={16} />
            Wiki
          </Link>
          <button className="btn btn-secondary" onClick={handleConsistencyReport} disabled={busy}>
            <ClipboardCheck size={16} />
            Report
          </button>
          <button className="btn btn-secondary" onClick={handlePreviewExport} disabled={busy}>
            <FileText size={16} />
            Preview
          </button>
          <select
            className="form-input compact-select"
            aria-label="Export preset"
            value={exportPreset}
            onChange={(event) => setExportPreset(event.target.value as typeof exportPreset)}
          >
            {EXPORT_PRESETS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <button className="btn btn-secondary" onClick={handleExport} disabled={busy}>
            <Download size={16} />
            Export
          </button>
          <div className="danger-actions" aria-label="Danger actions">
          <button className="btn btn-danger" onClick={handleDeleteWorld} disabled={busy} type="button">
            <Trash2 size={16} />
            Delete World
          </button>
          </div>
        </div>
      </div>

      {(statusMessage || errorMessage) && (
        <div
          className={`workspace-alert ${errorMessage ? 'error' : 'success'}`}
          role={errorMessage ? 'alert' : 'status'}
          aria-live={errorMessage ? 'assertive' : 'polite'}
        >
          {errorMessage || statusMessage}
        </div>
      )}

      {(report || markdownPreview) && (
        <div className="demo-review-grid">
          {report && (
            <section className="glass content-section">
              <div className="section-header">
                <ClipboardCheck className="text-primary" />
                <h2>Consistency Report</h2>
                <span className="report-score">{report.score}</span>
              </div>
              <p className="text-secondary">{report.summary}</p>
              <div className="issue-list">
                {report.issues.length === 0 ? (
                  <p className="text-muted">No issues found.</p>
                ) : report.issues.map((issue) => (
                  <div
                    key={issue.issue_id ?? `${issue.code}-${issue.entity_id ?? issue.relationship_id ?? issue.message}`}
                    className={`issue-item ${issue.severity}`}
                  >
                    <button
                      className="issue-content"
                      type="button"
                      onClick={() => handleIssueSelect(issue)}
                    >
                      <span className="issue-severity">{issue.severity}</span>
                      <span className="issue-body">
                        <span className="issue-code">{issue.code.replaceAll('_', ' ')}</span>
                        {issue.message}
                        {issue.status && <span className="issue-status">{issue.status}</span>}
                      </span>
                    </button>
                    {issue.issue_id && (
                      <div className="issue-controls">
                        <button
                          className="icon-button"
                          type="button"
                          title="Ignore issue"
                          aria-label={`Ignore issue: ${issue.message}`}
                          disabled={busy}
                          onClick={() => handleIssueUpdate(issue, { status: 'ignored' })}
                        >
                          <EyeOff size={16} />
                        </button>
                        <button
                          className="icon-button"
                          type="button"
                          title="Resolve issue"
                          aria-label={`Resolve issue: ${issue.message}`}
                          disabled={busy}
                          onClick={() => handleIssueUpdate(issue, { status: 'resolved' })}
                        >
                          <Check size={16} />
                        </button>
                        {issue.status === 'reopened' && (
                          <button
                            className="icon-button"
                            type="button"
                            title="Mark open"
                            aria-label={`Mark issue open: ${issue.message}`}
                            disabled={busy}
                            onClick={() => handleIssueUpdate(issue, { status: 'open' })}
                          >
                            <RefreshCcw size={16} />
                          </button>
                        )}
                        <input
                          className="issue-note-input"
                          aria-label={`Note for issue: ${issue.message}`}
                          value={issueNotes[issue.issue_id] ?? issue.note ?? ''}
                          onChange={(event) => setIssueNotes((current) => ({
                            ...current,
                            [issue.issue_id as string]: event.target.value,
                          }))}
                          placeholder="Note"
                        />
                        <button
                          className="icon-button"
                          type="button"
                          title="Save note"
                          aria-label={`Save note for issue: ${issue.message}`}
                          disabled={busy}
                          onClick={() => handleIssueUpdate(issue, {
                            note: issueNotes[issue.issue_id ?? ''] ?? '',
                          })}
                        >
                          <Save size={16} />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {archivedIssueStates.length > 0 && (
                <div className="issue-archive">
                  <h3>Managed Issues</h3>
                  {archivedIssueStates.map((issue) => (
                    <div key={issue.id} className={`issue-item ${issue.severity}`}>
                      <div className="issue-content">
                        <span className="issue-severity">{issue.severity}</span>
                        <span className="issue-body">
                          <span className="issue-code">{issue.code.replaceAll('_', ' ')}</span>
                          {issue.message}
                          <span className="issue-status">{issue.status}</span>
                        </span>
                      </div>
                      <div className="issue-controls">
                        <button
                          className="icon-button"
                          type="button"
                          title="Reopen issue"
                          aria-label={`Reopen issue: ${issue.message}`}
                          disabled={busy}
                          onClick={() => handleIssueStateUpdate(issue, { status: 'open' })}
                        >
                          <RefreshCcw size={16} />
                        </button>
                        <input
                          className="issue-note-input"
                          aria-label={`Note for managed issue: ${issue.message}`}
                          value={issueNotes[issue.id] ?? issue.note ?? ''}
                          onChange={(event) => setIssueNotes((current) => ({
                            ...current,
                            [issue.id]: event.target.value,
                          }))}
                          placeholder="Note"
                        />
                        <button
                          className="icon-button"
                          type="button"
                          title="Save note"
                          aria-label={`Save note for managed issue: ${issue.message}`}
                          disabled={busy}
                          onClick={() => handleIssueStateUpdate(issue, {
                            note: issueNotes[issue.id] ?? '',
                          })}
                        >
                          <Save size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
          {markdownPreview && (
            <section className="glass content-section">
              <div className="section-header">
                <FileText className="text-primary" />
                <h2>Markdown Preview</h2>
                <button
                  className="btn btn-secondary compact-button"
                  type="button"
                  onClick={() => downloadMarkdown(markdownPreview.filename, markdownPreview.content)}
                >
                  <Download size={16} />
                  Download
                </button>
              </div>
              <p className="text-secondary">{markdownPreview.filename}</p>
              <pre className="markdown-preview">{markdownPreview.content}</pre>
            </section>
          )}
        </div>
      )}

      {pendingSuggestions.length > 0 && (
        <section className="glass content-section">
          <div className="section-header">
            <Sparkles className="text-primary" />
            <h2>Canon Inbox</h2>
            <span className="review-badge">{pendingSuggestions.length} pending</span>
          </div>
          <div className="suggestion-list">
            {pendingSuggestions.map((suggestion) => (
              <article className="suggestion-item" key={suggestion.id}>
                <div>
                  <strong>{suggestion.suggested_name || 'Generated lore'}</strong>
                  <p className="text-muted">{suggestion.instruction}</p>
                  <div className="suggestion-badges">
                    <span>{(suggestion.candidate_kind ?? 'entity').replace('_', ' ')}</span>
                    {suggestion.source_type && <span>{suggestion.source_type}</span>}
                  </div>
                  <pre className="lore-content compact-lore">{suggestion.content}</pre>
                </div>
                <div className="form-actions">
                  {(suggestion.candidate_kind === null || suggestion.candidate_kind === 'entity') && (
                    <>
                      <button className="btn btn-secondary" type="button" onClick={() => handleSuggestionApply(suggestion, 'append_to_entity')} disabled={!selectedEntity || busy}>
                        Append
                      </button>
                      <button className="btn btn-secondary" type="button" onClick={() => handleSuggestionApply(suggestion, 'create_entity')} disabled={busy}>
                        Accept New
                      </button>
                    </>
                  )}
                  {suggestion.candidate_kind === 'relationship' && (
                    <button className="btn btn-secondary" type="button" onClick={() => handleSuggestionApply(suggestion, 'create_relationship')} disabled={busy}>
                      Add Relation
                    </button>
                  )}
                  {suggestion.candidate_kind === 'timeline_event' && (
                    <button className="btn btn-secondary" type="button" onClick={() => handleSuggestionApply(suggestion, 'create_timeline_event')} disabled={busy}>
                      Add Event
                    </button>
                  )}
                  {suggestion.candidate_kind === 'lore_note' && (
                    <button className="btn btn-secondary" type="button" onClick={() => handleSuggestionApply(suggestion, 'create_lore_note')} disabled={busy}>
                      Add Note
                    </button>
                  )}
                  <button className="btn btn-danger" type="button" onClick={() => handleSuggestionApply(suggestion, 'discard')} disabled={busy}>
                    Discard
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      <div className="workspace-grid">
        <aside className="entity-browser glass" aria-label="World bible entity browser">
          <div className="panel-title">
            <BookOpen size={18} />
            <h2>World Bible</h2>
            <button
              className="icon-button"
              type="button"
              onClick={() => selectEntity(null)}
              title="New entity"
              aria-label="Create new entity"
            >
              <Plus size={18} />
            </button>
          </div>
          <label className="entity-search">
            <Search size={16} />
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search this world"
              type="search"
            />
          </label>
          {entities.length === 0 ? (
            <p className="text-muted">No saved entities yet.</p>
          ) : searchResult.query && searchResult.filteredEntities.length === 0 ? (
            <p className="text-muted">No matches in this world.</p>
          ) : (
            groupedEntities.map(({ group, items }) => (
              items.length > 0 && (
                <div className="entity-group" key={group}>
                  <h3>{group}</h3>
                  {items.map((entity) => (
                    <button
                      className={[
                        'entity-list-item',
                        selectedEntityId === entity.id ? 'active' : '',
                        searchResult.matchingEntityIds.has(entity.id) ? 'search-match' : '',
                      ].filter(Boolean).join(' ')}
                      key={entity.id}
                      onClick={() => selectEntity(entity.id)}
                      type="button"
                    >
                      <span>{entity.name}</span>
                      <small>{entity.entity_type}</small>
                    </button>
                  ))}
                </div>
              )
            ))
          )}
        </aside>

        <div className="editor-stack">
          <div className="workspace-tabs glass" role="tablist" aria-label="Workspace views">
            <button
              className={activeView === 'canon' ? 'active' : ''}
              onClick={() => setActiveView('canon')}
              type="button"
              role="tab"
              aria-selected={activeView === 'canon'}
              aria-controls="canon-panel"
              id="canon-tab"
            >
              <Pencil size={16} />
              Canon
            </button>
            <button
              className={activeView === 'drafts' ? 'active' : ''}
              onClick={() => setActiveView('drafts')}
              type="button"
              role="tab"
              aria-selected={activeView === 'drafts'}
              aria-controls="drafts-panel"
              id="drafts-tab"
            >
              <FileText size={16} />
              Drafts
            </button>
            <button
              className={activeView === 'timeline' ? 'active' : ''}
              onClick={() => setActiveView('timeline')}
              type="button"
              role="tab"
              aria-selected={activeView === 'timeline'}
              aria-controls="timeline-panel"
              id="timeline-tab"
            >
              <Clock size={16} />
              Timeline
            </button>
            <button
              className={activeView === 'planning' ? 'active' : ''}
              onClick={() => setActiveView('planning')}
              type="button"
              role="tab"
              aria-selected={activeView === 'planning'}
              aria-controls="planning-panel"
              id="planning-tab"
            >
              <ClipboardCheck size={16} />
              Planning
            </button>
            <button
              className={activeView === 'graph' ? 'active' : ''}
              onClick={() => setActiveView('graph')}
              type="button"
              role="tab"
              aria-selected={activeView === 'graph'}
              aria-controls="graph-panel"
              id="graph-tab"
            >
              <Network size={16} />
              Graph
            </button>
            <button
              className={activeView === 'campaign' ? 'active' : ''}
              onClick={() => setActiveView('campaign')}
              type="button"
              role="tab"
              aria-selected={activeView === 'campaign'}
              aria-controls="campaign-panel"
              id="campaign-tab"
            >
              <Flag size={16} />
              Campaign
            </button>
          </div>

          {activeView === 'drafts' ? (
            <>
              <section className="glass content-section" id="drafts-panel" role="tabpanel" aria-labelledby="drafts-tab">
                <div className="section-header">
                  <FileText className="text-primary" />
                  <h2>Drafts</h2>
                  <button className="icon-button" type="button" title="New draft" aria-label="Create new draft" onClick={() => {
                    setSelectedDraftId(null);
                    setDraftForm({ title: '', body: '' });
                    setDraftSelection('');
                  }}>
                    <Plus size={16} />
                  </button>
                </div>
                <div className="draft-workspace">
                  <div className="draft-list" aria-label="Saved drafts">
                    {drafts.length === 0 ? (
                      <p className="text-muted">No saved drafts yet.</p>
                    ) : drafts.map((draft) => (
                      <button
                        className={selectedDraftId === draft.id ? 'draft-list-item active' : 'draft-list-item'}
                        key={draft.id}
                        type="button"
                        onClick={() => handleDraftSelect(draft.id)}
                      >
                        <span>{draft.title}</span>
                        <small>{draft.status}</small>
                      </button>
                    ))}
                  </div>
                  <form className="draft-editor" onSubmit={handleDraftSave}>
                    <label className="field-label">
                      <span>Draft title</span>
                      <input
                        className="form-input"
                        value={draftForm.title}
                        onChange={(event) => setDraftForm({ ...draftForm, title: event.target.value })}
                        placeholder="Draft title"
                        required
                      />
                    </label>
                    <label className="field-label">
                      <span>Draft body</span>
                      <textarea
                        className="form-input"
                        value={draftForm.body}
                        onChange={(event) => {
                          setDraftForm({ ...draftForm, body: event.target.value });
                          setDraftSelection('');
                        }}
                        onSelect={handleDraftTextSelect}
                        placeholder="Write or paste a scene draft, save it, then select an excerpt to extract"
                        rows={8}
                      />
                    </label>
                    <label className="field-label">
                      <span>Extraction focus</span>
                      <input
                        className="form-input"
                        value={draftInstruction}
                        onChange={(event) => setDraftInstruction(event.target.value)}
                        placeholder="Optional instruction"
                      />
                    </label>
                    <div className="form-actions">
                      <button className="btn btn-primary" type="submit" disabled={busy}>
                        <Save size={16} />
                        Save Draft
                      </button>
                      <button className="btn btn-secondary" type="button" onClick={handleDraftCheck} disabled={!selectedDraft || busy}>
                        <ClipboardCheck size={16} />
                        Check
                      </button>
                      <button className="btn btn-secondary" type="button" onClick={handleDraftExtract} disabled={!selectedDraft || !draftSelection || busy}>
                        <Sparkles size={16} />
                        Extract
                      </button>
                    </div>
                  </form>
                </div>
              </section>

            </>
          ) : activeView === 'canon' ? (
            <>
              <section className="glass content-section" id="canon-panel" role="tabpanel" aria-labelledby="canon-tab">
                <div className="section-header">
                  <BookOpen className="text-secondary" />
                  <h2>{selectedEntity ? 'Entity Detail' : 'New Entity'}</h2>
                  {entityFormDirty && <span className="dirty-indicator">Unsaved</span>}
                </div>
                <form onSubmit={handleEntitySubmit} className="entity-form">
                  <div className="form-row">
                    <label className="field-label">
                      <span>Entity name</span>
                      <input
                        value={entityForm.name}
                        onChange={(event) => setEntityForm({ ...entityForm, name: event.target.value })}
                        placeholder="Name"
                        className="form-input"
                        required
                      />
                    </label>
                    <label className="field-label">
                      <span>Entity type</span>
                      <select
                        value={entityForm.entity_type}
                        onChange={(event) => setEntityForm({ ...entityForm, entity_type: event.target.value })}
                        className="form-input"
                      >
                        {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                      </select>
                    </label>
                  </div>
                  <label className="field-label">
                    <span>Description</span>
                    <textarea
                      value={entityForm.description}
                      onChange={(event) => setEntityForm({ ...entityForm, description: event.target.value })}
                      placeholder="Description"
                      rows={9}
                      className="form-input"
                    />
                  </label>
                  <div className="template-grid">
                    {templateFields.map((field) => (
                      <label key={field}>
                        <span>{field.replaceAll('_', ' ')}</span>
                        <input
                          value={entityForm.structured_fields?.[field] ?? ''}
                          onChange={(event) => setEntityForm({
                            ...entityForm,
                            structured_fields: {
                              ...(entityForm.structured_fields ?? {}),
                              [field]: event.target.value,
                            },
                          })}
                          className="form-input"
                        />
                      </label>
                    ))}
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="btn btn-primary" disabled={busy}>
                      <Save size={16} />
                      {selectedEntity ? 'Save Entity' : 'Create Entity'}
                    </button>
                    {selectedEntity && (
                      <>
                        <button type="button" className="btn btn-secondary" onClick={handleDuplicateEntity} disabled={busy}>
                          <Plus size={16} />
                          Duplicate
                        </button>
                        <button type="button" className="btn btn-danger" onClick={handleDeleteEntity} disabled={busy}>
                          <Trash2 size={16} />
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </form>
              </section>

              <section className="glass content-section relationship-section">
                <div className="section-header">
                  <Link2 className="text-primary" />
                  <h2>Relationships</h2>
                </div>
                <form onSubmit={handleRelationshipSubmit} className="relationship-form">
                  <label className="field-label">
                    <span>Source</span>
                    <select
                      value={relationshipForm.source_entity_id}
                      onChange={(event) => setRelationshipForm({ ...relationshipForm, source_entity_id: event.target.value })}
                      className="form-input"
                      required
                    >
                      <option value="">Source</option>
                      {entities.map((entity) => <option key={entity.id} value={entity.id}>{entity.name}</option>)}
                    </select>
                  </label>
                  <label className="field-label">
                    <span>Relation type</span>
                    <input
                      value={relationshipForm.relation_type}
                      onChange={(event) => setRelationshipForm({ ...relationshipForm, relation_type: event.target.value })}
                      placeholder="Protects, rivals, funds"
                      className="form-input"
                      required
                    />
                  </label>
                  <label className="field-label">
                    <span>Target</span>
                    <select
                      value={relationshipForm.target_entity_id}
                      onChange={(event) => setRelationshipForm({ ...relationshipForm, target_entity_id: event.target.value })}
                      className="form-input"
                      required
                    >
                      <option value="">Target</option>
                      {entities.map((entity) => <option key={entity.id} value={entity.id}>{entity.name}</option>)}
                    </select>
                  </label>
                  <label className="field-label">
                    <span>Notes</span>
                    <input
                      value={relationshipForm.notes}
                      onChange={(event) => setRelationshipForm({ ...relationshipForm, notes: event.target.value })}
                      placeholder="Optional notes"
                      className="form-input"
                    />
                  </label>
                  <label className="field-label">
                    <span>Category</span>
                    <select
                      value={relationshipForm.category}
                      onChange={(event) => setRelationshipForm({ ...relationshipForm, category: event.target.value })}
                      className="form-input"
                    >
                      <option value="">Category</option>
                      <option>Alliance</option>
                      <option>Conflict</option>
                      <option>Kinship</option>
                      <option>Trade</option>
                      <option>History</option>
                    </select>
                  </label>
                  <label className="field-label">
                    <span>Strength</span>
                    <input
                      value={relationshipForm.strength}
                      onChange={(event) => setRelationshipForm({ ...relationshipForm, strength: Number(event.target.value) })}
                      className="form-input"
                      min={1}
                      max={5}
                      type="number"
                    />
                  </label>
                  <button type="submit" className="btn btn-primary" disabled={busy || entities.length < 2}>
                    <Plus size={16} />
                    Add
                  </button>
                </form>
                <div className="relationship-list">
                  <div className="context-row">
                    <span>{selectedEntity ? `Showing relationships connected to ${selectedContextLabel}` : 'Showing all relationships'}</span>
                    {selectedEntity && (
                      <label className="checkbox-row">
                        <input checked={showAllRelationships} onChange={(event) => setShowAllRelationships(event.target.checked)} type="checkbox" />
                        <span>Show all</span>
                      </label>
                    )}
                  </div>
                  {selectedRelationship && (
                    <p className="text-secondary">
                      Selected: {selectedRelationship.source_entity_name} {selectedRelationship.relation_type} {selectedRelationship.target_entity_name}
                    </p>
                  )}
                  {relationships.length === 0 ? (
                    <p className="text-muted">No relationships yet.</p>
                  ) : visibleRelationships.length === 0 ? (
                    <p className="text-muted">No relationships are connected to {selectedContextLabel}.</p>
                  ) : (
                    visibleRelationships.map((relationship) => (
                      <article
                        className={[
                          'relationship-item',
                          selectedRelationshipId === relationship.id ? 'selected' : '',
                          searchResult.matchingRelationshipIds.has(relationship.id) ? 'search-match' : '',
                        ].filter(Boolean).join(' ')}
                        key={relationship.id}
                      >
                        <div>
                          <strong>{relationship.source_entity_name}</strong>
                          <span> {relationship.relation_type} </span>
                          <strong>{relationship.target_entity_name}</strong>
                          {relationship.notes && <p>{relationship.notes}</p>}
                          {(relationship.category || relationship.strength || relationship.history) && (
                            <small>
                              {[relationship.category, relationship.strength ? `${relationship.strength}/5` : null, relationship.history].filter(Boolean).join(' · ')}
                            </small>
                          )}
                        </div>
                        <button
                          className="icon-button"
                          type="button"
                          aria-label={`Select relationship: ${relationship.source_entity_name} ${relationship.relation_type} ${relationship.target_entity_name}`}
                          aria-pressed={selectedRelationshipId === relationship.id}
                          onClick={() => setSelectedRelationshipId(relationship.id)}
                        >
                          <Link2 size={16} />
                        </button>
                        <button
                          className="icon-button danger"
                          onClick={async (event) => {
                            event.stopPropagation();
                            if (!id) return;
                            setErrorMessage('');
                            try {
                              await deleteRelationship(id, relationship.id);
                              setRelationships(await fetchRelationships(id));
                              if (selectedRelationshipId === relationship.id) {
                                setSelectedRelationshipId(null);
                              }
                              setStatusMessage('Relationship deleted.');
                            } catch {
                              setErrorMessage('Unable to delete relationship.');
                            }
                          }}
                          type="button"
                          title="Delete relationship"
                          aria-label={`Delete relationship: ${relationship.source_entity_name} ${relationship.relation_type} ${relationship.target_entity_name}`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </article>
                    ))
                  )}
                </div>
              </section>

            </>
          ) : activeView === 'timeline' ? (
            <>
              <section className="glass content-section" id="timeline-panel" role="tabpanel" aria-labelledby="timeline-tab">
                <div className="section-header">
                  <Clock className="text-primary" />
                  <h2>Timeline</h2>
                </div>
                <form onSubmit={handleTimelineSubmit} className="timeline-form">
                  <label className="field-label">
                    <span>Event title</span>
                    <input
                      value={timelineForm.title}
                      onChange={(event) => setTimelineForm({ ...timelineForm, title: event.target.value })}
                      placeholder="Event title"
                      className="form-input"
                    />
                  </label>
                  <label className="field-label">
                    <span>Order</span>
                    <input
                      value={timelineForm.event_order}
                      onChange={(event) => setTimelineForm({ ...timelineForm, event_order: Number(event.target.value) })}
                      type="number"
                      className="form-input"
                      min={1}
                    />
                  </label>
                  <label className="field-label full-width">
                    <span>Description</span>
                    <textarea
                      value={timelineForm.description}
                      onChange={(event) => setTimelineForm({ ...timelineForm, description: event.target.value })}
                      placeholder="Event description"
                      rows={3}
                      className="form-input"
                    />
                  </label>
                  <div className="form-row compact">
                    <label className="field-label">
                      <span>Causes</span>
                      <input
                        value={timelineForm.causes}
                        onChange={(event) => setTimelineForm({ ...timelineForm, causes: event.target.value })}
                        placeholder="Causes"
                        className="form-input"
                      />
                    </label>
                    <label className="field-label">
                      <span>Consequences</span>
                      <input
                        value={timelineForm.consequences}
                        onChange={(event) => setTimelineForm({ ...timelineForm, consequences: event.target.value })}
                        placeholder="Consequences"
                        className="form-input"
                      />
                    </label>
                  </div>
                  <div className="form-row compact">
                    <label className="field-label">
                      <span>Era</span>
                      <input
                        value={timelineForm.era_label}
                        onChange={(event) => setTimelineForm({ ...timelineForm, era_label: event.target.value })}
                        placeholder="Era"
                        className="form-input"
                      />
                    </label>
                    <label className="field-label">
                      <span>Date label</span>
                      <input
                        value={timelineForm.date_label}
                        onChange={(event) => setTimelineForm({ ...timelineForm, date_label: event.target.value })}
                        placeholder="Date label"
                        className="form-input"
                      />
                    </label>
                  </div>
                  <label className="field-label full-width">
                    <span>Dependency</span>
                    <select
                      value={timelineForm.depends_on}
                      onChange={(event) => setTimelineForm({ ...timelineForm, depends_on: event.target.value })}
                      className="form-input"
                    >
                      <option value="">No dependency</option>
                      {timelineEvents.map((event) => (
                        <option key={event.id} value={event.id}>{event.event_order}. {event.title}</option>
                      ))}
                    </select>
                  </label>
                  <button className="btn btn-primary" type="submit" disabled={busy}>
                    <Plus size={16} />
                    Add Event
                  </button>
                </form>
                <div className="context-row">
                  <span>{selectedEntity ? `Showing events linked to ${selectedContextLabel}` : 'Showing all events'}</span>
                  {selectedEntity && (
                    <label className="checkbox-row">
                      <input checked={showAllTimeline} onChange={(event) => setShowAllTimeline(event.target.checked)} type="checkbox" />
                      <span>Show all</span>
                    </label>
                  )}
                </div>
                <div className="timeline-track">
                  {timelineEvents.length === 0 ? (
                    <p className="text-muted">No timeline events yet.</p>
                  ) : visibleTimelineEvents.length === 0 ? (
                    <p className="text-muted">No timeline events are linked to {selectedContextLabel}.</p>
                  ) : visibleTimelineEvents.map((event) => (
                    <article className="timeline-item" key={event.id}>
                      <span>{event.event_order}</span>
                      <div>
                        <strong>{event.title}</strong>
                        {(event.era_label || event.date_label) && (
                          <em>{[event.era_label, event.date_label].filter(Boolean).join(' / ')}</em>
                        )}
                        {event.description && <p>{event.description}</p>}
                        {(event.causes || event.consequences) && (
                          <small>{[event.causes && `Cause: ${event.causes}`, event.consequences && `Consequence: ${event.consequences}`].filter(Boolean).join(' · ')}</small>
                        )}
                        {event.depends_on.length > 0 && (
                          <small>Depends on {event.depends_on.length} prior event{event.depends_on.length === 1 ? '' : 's'}</small>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            </>
          ) : activeView === 'planning' ? (
            <>
              <section className="glass content-section" id="planning-panel" role="tabpanel" aria-labelledby="planning-tab">
                <div className="section-header">
                  <ClipboardCheck className="text-primary" />
                  <h2>Planning Board</h2>
                </div>
                {planningBoards.length === 0 ? (
                  <form className="planning-form" onSubmit={handleCreatePlanningBoard}>
                    <label className="field-label">
                      <span>Board name</span>
                      <input
                        value={planningForm.boardName}
                        onChange={(event) => setPlanningForm({ ...planningForm, boardName: event.target.value })}
                        placeholder="Board name"
                        className="form-input"
                      />
                    </label>
                    <label className="field-label">
                      <span>Board type</span>
                      <select
                        value={planningForm.boardType}
                        onChange={(event) => setPlanningForm({ ...planningForm, boardType: event.target.value as PlanningBoard['board_type'] })}
                        className="form-input"
                      >
                        <option value="plot_thread">Plot thread</option>
                        <option value="arc">Arc</option>
                        <option value="chapter">Chapter</option>
                        <option value="scene">Scene</option>
                        <option value="custom">Custom</option>
                      </select>
                    </label>
                    <button className="btn btn-primary" type="submit" disabled={busy}>
                      <Plus size={16} />
                      Create Board
                    </button>
                  </form>
                ) : (
                  <>
                    <form className="planning-form" onSubmit={handleCreatePlanningCard}>
                      <label className="field-label">
                        <span>Card title</span>
                        <input
                          value={planningForm.cardTitle}
                          onChange={(event) => setPlanningForm({ ...planningForm, cardTitle: event.target.value })}
                          placeholder="Scene or thread card"
                          className="form-input"
                        />
                      </label>
                      <label className="field-label">
                        <span>Lane</span>
                        <input
                          value={planningForm.cardLane}
                          onChange={(event) => setPlanningForm({ ...planningForm, cardLane: event.target.value })}
                          placeholder="Lane"
                          className="form-input"
                        />
                      </label>
                      <button className="btn btn-primary" type="submit" disabled={busy}>
                        <Plus size={16} />
                        Link Card
                      </button>
                    </form>
                    <div className="planning-board-strip">
                      {planningBoards[0].cards.map((card) => (
                        <article className="planning-card" key={card.id}>
                          <small>{card.lane}</small>
                          <strong>{card.title}</strong>
                          <span>{card.entity_links.length + card.relationship_links.length + card.timeline_event_links.length} canon links</span>
                        </article>
                      ))}
                    </div>
                  </>
                )}
              </section>

              {selectedEntity && revisions.length > 0 && (
                <section className="glass content-section">
                  <div className="section-header">
                    <FileText className="text-secondary" />
                    <h2>Revision History</h2>
                  </div>
                  <div className="revision-list">
                    {revisions.slice(0, 5).map((revision) => (
                      <button className="revision-item" type="button" key={revision.id} onClick={() => handleRestoreRevision(revision.id)}>
                        <span>{new Date(revision.created_at).toLocaleString()}</span>
                        <small>{revision.source} {revision.field_name}</small>
                      </button>
                    ))}
                  </div>
                </section>
              )}
            </>
          ) : activeView === 'campaign' ? (
            <>
              <section className="glass content-section" id="campaign-panel" role="tabpanel" aria-labelledby="campaign-tab">
                <div className="section-header">
                  <Flag className="text-primary" />
                  <h2>Campaign Sessions</h2>
                </div>
                <form className="planning-form" onSubmit={handleCreateCampaignSession}>
                  <label className="field-label">
                    <span>Session number</span>
                    <input
                      className="form-input"
                      min={1}
                      type="number"
                      value={campaignForm.sessionNumber}
                      onChange={(event) => setCampaignForm({ ...campaignForm, sessionNumber: Number(event.target.value) })}
                    />
                  </label>
                  <label className="field-label">
                    <span>Session title</span>
                    <input
                      className="form-input"
                      value={campaignForm.sessionTitle}
                      onChange={(event) => setCampaignForm({ ...campaignForm, sessionTitle: event.target.value })}
                      placeholder="Session title"
                    />
                  </label>
                  <button className="btn btn-primary" type="submit" disabled={busy}>
                    <Plus size={16} />
                    Add Session
                  </button>
                  <label className="field-label full-width">
                    <span>Recap and consequences</span>
                    <textarea
                      className="form-input"
                      value={campaignForm.recap}
                      onChange={(event) => setCampaignForm({ ...campaignForm, recap: event.target.value })}
                      placeholder="Recap and consequences"
                      rows={3}
                    />
                  </label>
                </form>
                <div className="planning-board-strip">
                  {campaignSessions.length === 0 ? (
                    <p className="text-muted">No campaign sessions yet.</p>
                  ) : campaignSessions.map((session) => (
                    <article className="planning-card" key={session.id}>
                      <small>Session {session.session_number}</small>
                      <strong>{session.title}</strong>
                      {session.recap && <span>{session.recap}</span>}
                      <button className="btn btn-secondary compact-button" type="button" disabled={busy} onClick={() => handleCampaignImpactReview(session.id)}>
                        Review Impact
                      </button>
                    </article>
                  ))}
                </div>
              </section>

              <section className="glass content-section">
                <div className="section-header">
                  <BookOpen className="text-secondary" />
                  <h2>Lore Notes</h2>
                </div>
                <form className="planning-form" onSubmit={handleCreateLoreNote}>
                  <label className="field-label">
                    <span>Note title</span>
                    <input
                      className="form-input"
                      value={campaignForm.noteTitle}
                      onChange={(event) => setCampaignForm({ ...campaignForm, noteTitle: event.target.value })}
                      placeholder={selectedEntity ? `Note for ${selectedEntity.name}` : 'World note'}
                    />
                  </label>
                  <label className="field-label">
                    <span>Visibility</span>
                    <select
                      className="form-input"
                      value={campaignForm.noteVisibility}
                      onChange={(event) => setCampaignForm({ ...campaignForm, noteVisibility: event.target.value as LoreNote['visibility'] })}
                    >
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
                    <textarea
                      className="form-input"
                      value={campaignForm.noteBody}
                      onChange={(event) => setCampaignForm({ ...campaignForm, noteBody: event.target.value })}
                      placeholder="Secret, rumor, reveal condition, or handout text"
                      rows={3}
                    />
                  </label>
                </form>
                <div className="suggestion-list">
                  {loreNotes.slice(0, 8).map((note) => (
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
                <form className="planning-form" onSubmit={handleCreateFactionClock}>
                  <label className="field-label">
                    <span>Clock title</span>
                    <input
                      className="form-input"
                      value={campaignForm.clockTitle}
                      onChange={(event) => setCampaignForm({ ...campaignForm, clockTitle: event.target.value })}
                      placeholder="Clock title"
                    />
                  </label>
                  <label className="field-label">
                    <span>Segments</span>
                    <input
                      className="form-input"
                      min={1}
                      max={20}
                      type="number"
                      value={campaignForm.clockSegments}
                      onChange={(event) => setCampaignForm({ ...campaignForm, clockSegments: Number(event.target.value) })}
                    />
                  </label>
                  <label className="field-label">
                    <span>Filled</span>
                    <input
                      className="form-input"
                      min={0}
                      max={campaignForm.clockSegments}
                      type="number"
                      value={campaignForm.clockFilled}
                      onChange={(event) => setCampaignForm({ ...campaignForm, clockFilled: Number(event.target.value) })}
                    />
                  </label>
                  <button className="btn btn-primary" type="submit" disabled={busy}>
                    <Plus size={16} />
                    Add Clock
                  </button>
                  <label className="field-label full-width">
                    <span>Stakes</span>
                    <input
                      className="form-input"
                      value={campaignForm.clockStakes}
                      onChange={(event) => setCampaignForm({ ...campaignForm, clockStakes: event.target.value })}
                      placeholder="Stakes if the clock fills"
                    />
                  </label>
                </form>
                <div className="planning-board-strip">
                  {factionClocks.map((clock) => (
                    <article className="planning-card" key={clock.id}>
                      <small>{clock.status}</small>
                      <strong>{clock.title}</strong>
                      <span>{clock.filled_segments}/{clock.segments} segments</span>
                      {clock.stakes && <span>{clock.stakes}</span>}
                    </article>
                  ))}
                </div>
              </section>
            </>
          ) : (
            <section className="glass content-section graph-section" id="graph-panel" role="tabpanel" aria-labelledby="graph-tab">
              <div className="section-header graph-header">
                <div>
                  <Network className="text-primary" />
                  <h2>World Graph</h2>
                </div>
                {searchResult.query && (
                  <span className="graph-search-summary">
                    {searchResult.highlightedEntityIds.size} nodes, {searchResult.highlightedRelationshipIds.size} edges
                  </span>
                )}
                <div className="graph-tools">
                  <select
                    className="form-input"
                    aria-label="Graph layout mode"
                    value={graphLayoutMode}
                    onChange={(event) => {
                      setGraphLayoutMode(event.target.value as GraphLayoutMode);
                      setGraphResetKey((current) => current + 1);
                    }}
                    title="Graph layout mode"
                  >
                    {GRAPH_LAYOUTS.map((layout) => (
                      <option key={layout.value} value={layout.value}>{layout.label}</option>
                    ))}
                  </select>
                  <select
                    className="form-input"
                    aria-label="Filter graph by entity type"
                    value={graphTypeFilter}
                    onChange={(event) => setGraphTypeFilter(event.target.value)}
                    title="Filter graph by entity type"
                  >
                    <option>All</option>
                    {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                  </select>
                  <button className="icon-button" type="button" onClick={handleResetGraph} title="Reset layout" aria-label="Reset graph layout">
                    <RefreshCcw size={16} />
                  </button>
                </div>
              </div>
              <div className="saved-views-row">
                <label className="field-label saved-view-label">
                  <span>View name</span>
                  <input
                    value={graphViewName}
                    onChange={(event) => setGraphViewName(event.target.value)}
                    placeholder="Named view"
                    className="form-input"
                  />
                </label>
                <button className="btn btn-secondary compact-button" type="button" onClick={handleSaveGraphView} disabled={busy || !graphViewName.trim()}>
                  <Save size={16} />
                  Save View
                </button>
                {graphViews.map((view) => (
                  <button className="preset-button compact-view-button" key={view.id} type="button" onClick={() => applyGraphView(view)}>
                    {view.name}
                  </button>
                ))}
              </div>
              <div className="graph-legend" aria-label="Relationship color legend">
                <span><i className="legend-swatch alliance" />Alliance</span>
                <span><i className="legend-swatch conflict" />Conflict</span>
                <span><i className="legend-swatch neutral" />Neutral</span>
                <span><i className="legend-swatch selected" />Selected</span>
              </div>
              <div className="graph-canvas">
                <Suspense fallback={<div className="loading-state" role="status">Loading graph...</div>}>
                  <WorldGraphView
                    nodes={graphData.nodes}
                    edges={graphData.edges}
                    onSelectEntity={selectEntity}
                    onSelectRelationship={setSelectedRelationshipId}
                    onPositionsChange={setGraphPositions}
                    onCreateEntity={handleCreateEntityFromGraph}
                    resetKey={graphResetKey}
                  />
                </Suspense>
              </div>
              <section className="graph-summary" aria-labelledby="graph-summary-heading">
                <h3 id="graph-summary-heading">Accessible graph summary</h3>
                <p className="text-secondary">
                  Showing {graphEntities.length} {graphTypeFilter === 'All' ? 'entities' : graphTypeFilter.toLowerCase() + ' entities'} and {graphRelationships.length} relationships in {GRAPH_LAYOUTS.find((layout) => layout.value === graphLayoutMode)?.label ?? graphLayoutMode} layout.
                </p>
                <div className="graph-summary-grid">
                  <div>
                    <h4>Entities</h4>
                    {graphEntities.length === 0 ? (
                      <p className="text-muted">No entities match this filter.</p>
                    ) : (
                      <ul className="graph-summary-list">
                        {graphEntities.map((entity) => (
                          <li key={entity.id}>
                            <button
                              className="wiki-text-link"
                              type="button"
                              aria-current={selectedEntityId === entity.id ? 'true' : undefined}
                              onClick={() => selectEntity(entity.id)}
                            >
                              {entity.name}
                            </button>
                            <span>{displayType(entity.entity_type)}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div>
                    <h4>Relationships</h4>
                    {graphRelationshipRows.length === 0 ? (
                      <p className="text-muted">No visible relationships.</p>
                    ) : (
                      <ul className="graph-summary-list">
                        {graphRelationshipRows.map((relationship) => (
                          <li key={relationship.id}>
                            <button
                              className="wiki-text-link"
                              type="button"
                              aria-current={selectedRelationshipId === relationship.id ? 'true' : undefined}
                              onClick={() => setSelectedRelationshipId(relationship.id)}
                            >
                              {relationship.sourceName} {relationship.relation_type} {relationship.targetName}
                            </button>
                            {(relationship.category || relationship.stance) && (
                              <span>{[relationship.category, relationship.stance].filter(Boolean).join(', ')}</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </section>
            </section>
          )}
        </div>

        <aside className="generator-stack" aria-label="Generation and review tools">
          <section className="glass agent-section">
            <div className="agent-header">
              <Bot className="agent-icon" size={24} />
              <h3>Generator</h3>
            </div>
            <div className="preset-row">
              {PROMPTS.map((prompt) => (
                <button
                  key={prompt.label}
                  className="preset-button"
                  type="button"
                  onClick={() => setAgenticInstruction(prompt.value)}
                >
                  {prompt.label}
                </button>
              ))}
            </div>
            <form onSubmit={handleAgenticGen} className="agent-form">
              <label className="field-label">
                <span>Generation prompt</span>
                <textarea
                  value={agenticInstruction}
                  onChange={(event) => {
                    setAgenticInstruction(event.target.value);
                    setConfirmReplaceGenerated(false);
                  }}
                  placeholder="Generation prompt"
                  rows={5}
                  className="form-input"
                  required
                />
              </label>
              <label className="checkbox-row">
                <input
                  checked={saveGenerated}
                  onChange={(event) => setSaveGenerated(event.target.checked)}
                  type="checkbox"
                />
                <span>Save as entity</span>
              </label>
              {saveGenerated && (
                <div className="form-row compact">
                  <label className="field-label">
                    <span>Entity name</span>
                    <input
                      value={generatedName}
                      onChange={(event) => setGeneratedName(event.target.value)}
                      placeholder="Entity name"
                      className="form-input"
                    />
                  </label>
                  <label className="field-label">
                    <span>Entity type</span>
                    <select
                      value={generatedType}
                      onChange={(event) => setGeneratedType(event.target.value)}
                      className="form-input"
                    >
                      {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                    </select>
                  </label>
                </div>
              )}
              <button type="submit" className="btn btn-primary" disabled={generating || !agenticInstruction.trim()}>
                <Sparkles size={16} />
                {generating ? 'Generating...' : 'Generate'}
              </button>
            </form>
          </section>

          {agenticResult && (
            <section className="glass content-section result-section page-enter">
              <div className="section-header">
                <Sparkles className="text-primary" />
                <h2>Generated Lore</h2>
                <span className="review-badge">Ready for review</span>
              </div>
              <pre className="lore-content">{agenticResult.content}</pre>
              {!saveGenerated && (
                <div className="form-row compact">
                  <label className="field-label">
                    <span>New entity name</span>
                    <input
                      value={generatedName}
                      onChange={(event) => setGeneratedName(event.target.value)}
                      placeholder="Entity name"
                      className="form-input"
                    />
                  </label>
                  <label className="field-label">
                    <span>New entity type</span>
                    <select
                      value={generatedType}
                      onChange={(event) => setGeneratedType(event.target.value)}
                      className="form-input"
                    >
                      {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                    </select>
                  </label>
                </div>
              )}
              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleApplyGenerated('append')}
                  disabled={!selectedEntity || busy}
                >
                  Append
                </button>
                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={() => handleApplyGenerated('replace')}
                  disabled={!selectedEntity || busy}
                >
                  {confirmReplaceGenerated ? 'Confirm Replace' : 'Replace'}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleSaveGeneratedAsEntity}
                  disabled={!generatedName.trim() || busy}
                >
                  Save as New
                </button>
              </div>
            </section>
          )}

          <section className="glass agent-section">
            <div className="agent-header">
              <ClipboardCheck className="agent-icon" size={22} />
              <h3>Passage Check</h3>
            </div>
            <form onSubmit={handlePassageCheck} className="agent-form">
              <label className="field-label">
                <span>Passage text</span>
                <textarea
                  value={passageText}
                  onChange={(event) => setPassageText(event.target.value)}
                  placeholder="Paste a scene excerpt"
                  rows={5}
                  className="form-input"
                />
              </label>
              <button type="submit" className="btn btn-secondary" disabled={busy || !passageText.trim()}>
                <ClipboardCheck size={16} />
                Check
              </button>
            </form>
            {passageReport && (
              <div className="issue-list">
                <p className="text-secondary">{passageReport.summary}</p>
                {passageReport.issues.map((issue) => (
                  <button
                    className={`issue-item ${issue.severity}`}
                    key={`${issue.code}-${issue.entity_id ?? issue.message}`}
                    type="button"
                    onClick={() => issue.entity_id && selectEntity(issue.entity_id)}
                  >
                    <span className="issue-severity">{issue.severity}</span>
                    <span className="issue-body">{issue.message}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
};

export default WorldDetail;
