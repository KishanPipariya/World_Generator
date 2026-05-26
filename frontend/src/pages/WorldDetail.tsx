import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Activity,
  Bot,
  BookOpen,
  ClipboardCheck,
  Clock,
  Download,
  FileText,
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
  checkPassage,
  createTimelineEvent,
  createEntity,
  createGraphView,
  createPlanningBoard,
  createPlanningCard,
  createRelationship,
  deleteEntity,
  deleteWorld,
  deleteRelationship,
  exportMarkdown,
  fetchConsistencyReport,
  fetchEntities,
  fetchGraphViews,
  fetchHealth,
  fetchPlanningBoards,
  fetchRelationships,
  fetchRevisions,
  fetchSuggestions,
  fetchTimelineEvents,
  fetchWorld,
  generateAgentic,
  restoreRevision,
  updateEntity,
  type ConsistencyReport,
  type Entity,
  type GenerationSuggestion,
  type GraphLayoutMode,
  type GraphView,
  type HealthStatus,
  type PassageCheck,
  type PlanningBoard,
  type Relationship,
  type RevisionVersion,
  type TimelineEvent,
  type World,
} from '../lib/api';
import { buildWorldGraph, searchWorldGraph } from '../lib/worldGraph';
import './WorldDetail.css';
import WorldGraphView from './WorldGraphView';

const ENTITY_GROUPS = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
const ENTITY_TYPES = ['Character', 'Location', 'Faction', 'Concept', 'Event', 'Other'];
const EXPORT_PRESETS = [
  ['full_bible', 'Full Bible'],
  ['character_dossier', 'Characters'],
  ['faction_brief', 'Factions'],
  ['location_gazetteer', 'Locations'],
  ['timeline_only', 'Timeline'],
  ['obsidian', 'Obsidian'],
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
type WorkspaceView = 'editor' | 'graph';

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
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [graphViews, setGraphViews] = useState<GraphView[]>([]);
  const [planningBoards, setPlanningBoards] = useState<PlanningBoard[]>([]);
  const [revisions, setRevisions] = useState<RevisionVersion[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<WorkspaceView>('editor');
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
  const [passageText, setPassageText] = useState('');
  const [passageReport, setPassageReport] = useState<PassageCheck | null>(null);
  const [exportPreset, setExportPreset] = useState<(typeof EXPORT_PRESETS)[number][0]>('full_bible');
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

  const loadWorkspace = async (worldId: string) => {
    setErrorMessage('');
    const [worldData, entityData, relationshipData, suggestionData, timelineData, graphViewData, boardData, healthData] = await Promise.all([
      fetchWorld(worldId),
      fetchEntities(worldId),
      fetchRelationships(worldId),
      fetchSuggestions(worldId).catch(() => []),
      fetchTimelineEvents(worldId).catch(() => []),
      fetchGraphViews(worldId).catch(() => []),
      fetchPlanningBoards(worldId).catch(() => []),
      fetchHealth().catch(() => null),
    ]);
    setWorld(worldData);
    setEntities(entityData);
    setRelationships(relationshipData);
    setSuggestions(suggestionData);
    setTimelineEvents(timelineData);
    setGraphViews(graphViewData);
    setPlanningBoards(boardData);
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

  const selectEntity = (entityId: string | null) => {
    if (entityFormDirty && !window.confirm('Discard unsaved entity edits?')) return;
    setSelectedEntityId(entityId);
    setSelectedRelationshipId(null);
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
    if (!window.confirm(`Delete "${world.title}" and all of its entities and relationships?`)) return;
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
  };

  const handleApplyGenerated = async (mode: 'append' | 'replace') => {
    if (!id || !selectedEntity || !agenticResult) return;
    if (
      mode === 'replace'
      && !window.confirm(`Replace the full description for "${selectedEntity.name}" with the generated lore?`)
    ) return;
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
      setReport(await fetchConsistencyReport(id));
      setStatusMessage('Consistency report ready.');
    } catch {
      setErrorMessage('Unable to run consistency report.');
    } finally {
      setBusy(false);
    }
  };

  const handleSuggestionApply = async (
    suggestion: GenerationSuggestion,
    mode: 'create_entity' | 'append_to_entity' | 'replace_entity' | 'discard',
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
      await Promise.all([refreshEntities(), refreshReviewData()]);
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
    setActiveView('editor');
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

  if (loading) {
    return <div className="loading-state">Loading world workspace...</div>;
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

      <div className="world-header glass">
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
            value={exportPreset}
            onChange={(event) => setExportPreset(event.target.value as typeof exportPreset)}
            title="Export preset"
          >
            {EXPORT_PRESETS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <button className="btn btn-secondary" onClick={handleExport} disabled={busy}>
            <Download size={16} />
            Export
          </button>
          <button className="btn btn-danger" onClick={handleDeleteWorld} disabled={busy} type="button">
            <Trash2 size={16} />
            Delete
          </button>
        </div>
      </div>

      {(statusMessage || errorMessage) && (
        <div className={`workspace-alert ${errorMessage ? 'error' : 'success'}`}>
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
                  <button
                    key={`${issue.code}-${issue.entity_id ?? issue.relationship_id ?? issue.message}`}
                    className={`issue-item ${issue.severity}`}
                    type="button"
                    onClick={() => handleIssueSelect(issue)}
                  >
                    <span className="issue-severity">{issue.severity}</span>
                    <span className="issue-body">
                      <span className="issue-code">{issue.code.replaceAll('_', ' ')}</span>
                      {issue.message}
                    </span>
                  </button>
                ))}
              </div>
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
                  <pre className="lore-content compact-lore">{suggestion.content}</pre>
                </div>
                <div className="form-actions">
                  <button className="btn btn-secondary" type="button" onClick={() => handleSuggestionApply(suggestion, 'append_to_entity')} disabled={!selectedEntity || busy}>
                    Append
                  </button>
                  <button className="btn btn-secondary" type="button" onClick={() => handleSuggestionApply(suggestion, 'create_entity')} disabled={busy}>
                    Accept New
                  </button>
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
        <aside className="entity-browser glass">
          <div className="panel-title">
            <BookOpen size={18} />
            <h2>World Bible</h2>
            <button
              className="icon-button"
              type="button"
              onClick={() => selectEntity(null)}
              title="New entity"
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

        <main className="editor-stack">
          <div className="workspace-tabs glass">
            <button
              className={activeView === 'editor' ? 'active' : ''}
              onClick={() => setActiveView('editor')}
              type="button"
            >
              <Pencil size={16} />
              Editor
            </button>
            <button
              className={activeView === 'graph' ? 'active' : ''}
              onClick={() => setActiveView('graph')}
              type="button"
            >
              <Network size={16} />
              Graph
            </button>
          </div>

          {activeView === 'editor' ? (
            <>
              <section className="glass content-section">
                <div className="section-header">
                  <BookOpen className="text-secondary" />
                  <h2>{selectedEntity ? 'Entity Detail' : 'New Entity'}</h2>
                  {entityFormDirty && <span className="dirty-indicator">Unsaved</span>}
                </div>
                <form onSubmit={handleEntitySubmit} className="entity-form">
                  <div className="form-row">
                    <input
                      value={entityForm.name}
                      onChange={(event) => setEntityForm({ ...entityForm, name: event.target.value })}
                      placeholder="Name"
                      className="form-input"
                      required
                    />
                    <select
                      value={entityForm.entity_type}
                      onChange={(event) => setEntityForm({ ...entityForm, entity_type: event.target.value })}
                      className="form-input"
                    >
                      {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                    </select>
                  </div>
                  <textarea
                    value={entityForm.description}
                    onChange={(event) => setEntityForm({ ...entityForm, description: event.target.value })}
                    placeholder="Description"
                    rows={9}
                    className="form-input"
                  />
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
                  <select
                    value={relationshipForm.source_entity_id}
                    onChange={(event) => setRelationshipForm({ ...relationshipForm, source_entity_id: event.target.value })}
                    className="form-input"
                    required
                  >
                    <option value="">Source</option>
                    {entities.map((entity) => <option key={entity.id} value={entity.id}>{entity.name}</option>)}
                  </select>
                  <input
                    value={relationshipForm.relation_type}
                    onChange={(event) => setRelationshipForm({ ...relationshipForm, relation_type: event.target.value })}
                    placeholder="Relation"
                    className="form-input"
                    required
                  />
                  <select
                    value={relationshipForm.target_entity_id}
                    onChange={(event) => setRelationshipForm({ ...relationshipForm, target_entity_id: event.target.value })}
                    className="form-input"
                    required
                  >
                    <option value="">Target</option>
                    {entities.map((entity) => <option key={entity.id} value={entity.id}>{entity.name}</option>)}
                  </select>
                  <input
                    value={relationshipForm.notes}
                    onChange={(event) => setRelationshipForm({ ...relationshipForm, notes: event.target.value })}
                    placeholder="Notes"
                    className="form-input"
                  />
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
                  <input
                    value={relationshipForm.strength}
                    onChange={(event) => setRelationshipForm({ ...relationshipForm, strength: Number(event.target.value) })}
                    className="form-input"
                    min={1}
                    max={5}
                    type="number"
                    title="Strength"
                  />
                  <button type="submit" className="btn btn-primary" disabled={busy || entities.length < 2}>
                    <Plus size={16} />
                    Add
                  </button>
                </form>
                <div className="relationship-list">
                  {selectedRelationship && (
                    <p className="text-secondary">
                      Selected: {selectedRelationship.source_entity_name} {selectedRelationship.relation_type} {selectedRelationship.target_entity_name}
                    </p>
                  )}
                  {relationships.length === 0 ? (
                    <p className="text-muted">No relationships yet.</p>
                  ) : (
                    relationships.map((relationship) => (
                      <div
                        className={[
                          'relationship-item',
                          selectedRelationshipId === relationship.id ? 'selected' : '',
                          searchResult.matchingRelationshipIds.has(relationship.id) ? 'search-match' : '',
                        ].filter(Boolean).join(' ')}
                        key={relationship.id}
                        onClick={() => setSelectedRelationshipId(relationship.id)}
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
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </section>

              <section className="glass content-section">
                <div className="section-header">
                  <Clock className="text-primary" />
                  <h2>Timeline</h2>
                </div>
                <form onSubmit={handleTimelineSubmit} className="timeline-form">
                  <input
                    value={timelineForm.title}
                    onChange={(event) => setTimelineForm({ ...timelineForm, title: event.target.value })}
                    placeholder="Event title"
                    className="form-input"
                  />
                  <input
                    value={timelineForm.event_order}
                    onChange={(event) => setTimelineForm({ ...timelineForm, event_order: Number(event.target.value) })}
                    type="number"
                    className="form-input"
                    min={1}
                  />
                  <textarea
                    value={timelineForm.description}
                    onChange={(event) => setTimelineForm({ ...timelineForm, description: event.target.value })}
                    placeholder="Event description"
                    rows={3}
                    className="form-input"
                  />
                  <div className="form-row compact">
                    <input
                      value={timelineForm.causes}
                      onChange={(event) => setTimelineForm({ ...timelineForm, causes: event.target.value })}
                      placeholder="Causes"
                      className="form-input"
                    />
                    <input
                      value={timelineForm.consequences}
                      onChange={(event) => setTimelineForm({ ...timelineForm, consequences: event.target.value })}
                      placeholder="Consequences"
                      className="form-input"
                    />
                  </div>
                  <div className="form-row compact">
                    <input
                      value={timelineForm.era_label}
                      onChange={(event) => setTimelineForm({ ...timelineForm, era_label: event.target.value })}
                      placeholder="Era"
                      className="form-input"
                    />
                    <input
                      value={timelineForm.date_label}
                      onChange={(event) => setTimelineForm({ ...timelineForm, date_label: event.target.value })}
                      placeholder="Date label"
                      className="form-input"
                    />
                  </div>
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
                  <button className="btn btn-primary" type="submit" disabled={busy}>
                    <Plus size={16} />
                    Add Event
                  </button>
                </form>
                <div className="timeline-track">
                  {timelineEvents.length === 0 ? (
                    <p className="text-muted">No timeline events yet.</p>
                  ) : timelineEvents.map((event) => (
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

              <section className="glass content-section">
                <div className="section-header">
                  <ClipboardCheck className="text-primary" />
                  <h2>Planning Board</h2>
                </div>
                {planningBoards.length === 0 ? (
                  <form className="planning-form" onSubmit={handleCreatePlanningBoard}>
                    <input
                      value={planningForm.boardName}
                      onChange={(event) => setPlanningForm({ ...planningForm, boardName: event.target.value })}
                      placeholder="Board name"
                      className="form-input"
                    />
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
                    <button className="btn btn-primary" type="submit" disabled={busy}>
                      <Plus size={16} />
                      Create Board
                    </button>
                  </form>
                ) : (
                  <>
                    <form className="planning-form" onSubmit={handleCreatePlanningCard}>
                      <input
                        value={planningForm.cardTitle}
                        onChange={(event) => setPlanningForm({ ...planningForm, cardTitle: event.target.value })}
                        placeholder="Scene or thread card"
                        className="form-input"
                      />
                      <input
                        value={planningForm.cardLane}
                        onChange={(event) => setPlanningForm({ ...planningForm, cardLane: event.target.value })}
                        placeholder="Lane"
                        className="form-input"
                      />
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
          ) : (
            <section className="glass content-section graph-section">
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
                    value={graphTypeFilter}
                    onChange={(event) => setGraphTypeFilter(event.target.value)}
                    title="Filter graph by entity type"
                  >
                    <option>All</option>
                    {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                  </select>
                  <button className="icon-button" type="button" onClick={handleResetGraph} title="Reset layout">
                    <RefreshCcw size={16} />
                  </button>
                </div>
              </div>
              <div className="saved-views-row">
                <input
                  value={graphViewName}
                  onChange={(event) => setGraphViewName(event.target.value)}
                  placeholder="Named view"
                  className="form-input"
                />
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
              <div className="graph-canvas">
                <WorldGraphView
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                  onSelectEntity={selectEntity}
                  onSelectRelationship={setSelectedRelationshipId}
                  onPositionsChange={setGraphPositions}
                  resetKey={graphResetKey}
                />
              </div>
            </section>
          )}
        </main>

        <aside className="generator-stack">
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
              <textarea
                value={agenticInstruction}
                onChange={(event) => setAgenticInstruction(event.target.value)}
                placeholder="Generation prompt"
                rows={5}
                className="form-input"
                required
              />
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
                  <input
                    value={generatedName}
                    onChange={(event) => setGeneratedName(event.target.value)}
                    placeholder="Entity name"
                    className="form-input"
                  />
                  <select
                    value={generatedType}
                    onChange={(event) => setGeneratedType(event.target.value)}
                    className="form-input"
                  >
                    {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                  </select>
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
                  <input
                    value={generatedName}
                    onChange={(event) => setGeneratedName(event.target.value)}
                    placeholder="Entity name"
                    className="form-input"
                  />
                  <select
                    value={generatedType}
                    onChange={(event) => setGeneratedType(event.target.value)}
                    className="form-input"
                  >
                    {ENTITY_TYPES.map((type) => <option key={type}>{type}</option>)}
                  </select>
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
                  Replace
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
              <textarea
                value={passageText}
                onChange={(event) => setPassageText(event.target.value)}
                placeholder="Paste a scene excerpt"
                rows={5}
                className="form-input"
              />
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
