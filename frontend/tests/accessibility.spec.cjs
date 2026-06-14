const { AxeBuilder } = require('@axe-core/playwright');
const { expect, test } = require('@playwright/test');

const createdAt = '2026-01-01T00:00:00.000Z';

const world = {
  id: 'demo-world',
  title: 'Ember Archipelago',
  tone: 'Mythic',
  era_notes: 'Island city-states are rebuilding after the Night of Falling Bells.',
  seed: 'ember',
  created_at: createdAt,
};

const createdWorld = {
  ...world,
  id: 'created-world',
  title: 'Created Test World',
  tone: 'Mystery',
  era_notes: 'Fresh canon for a new wiki.',
  seed: 'created',
};

const demoCreatedWorld = {
  ...world,
  id: 'demo-created-world',
  title: 'Demo Created World',
};

const user = {
  id: 'user-1',
  username: 'test-writer',
  email: 'writer@example.com',
  created_at: createdAt,
};

const entities = [
  {
    id: 'entity-1',
    world_id: world.id,
    name: 'Mara Vey',
    entity_type: 'Character',
    description: 'A lighthouse keeper tracking impossible tides.',
    structured_fields: { goal: 'Restore the beacon', secret: 'Knows the bell names' },
    created_at: createdAt,
  },
  {
    id: 'entity-2',
    world_id: world.id,
    name: 'Glass Harbor',
    entity_type: 'Location',
    description: 'A port built from storm-polished obsidian.',
    structured_fields: { hazards: 'Echo storms' },
    created_at: createdAt,
  },
];

const relationships = [
  {
    id: 'relationship-1',
    world_id: world.id,
    source_entity_id: 'entity-1',
    source_entity_name: 'Mara Vey',
    target_entity_id: 'entity-2',
    target_entity_name: 'Glass Harbor',
    relation_type: 'protects',
    notes: 'Mara keeps the harbor lantern lit.',
    category: 'Alliance',
    strength: 4,
    history: 'Bound after the storm year.',
    stance: 'alliance',
    color: null,
    display_priority: null,
    created_at: createdAt,
  },
];

const suggestions = [
  {
    id: 'suggestion-1',
    world_id: world.id,
    instruction: 'Generated test lore',
    content: 'Generated replacement lore for Mara.',
    suggested_name: 'Bell Cipher',
    suggested_type: 'Concept',
    status: 'pending',
    created_at: createdAt,
    candidate_kind: 'entity',
    source_type: 'generation',
    source_id: null,
    source_excerpt: null,
    payload: null,
  },
];

const consistencyIssues = [
  {
    id: 'issue-1',
    world_id: world.id,
    fingerprint: 'missing-description:entity-1',
    code: 'thin_lore',
    severity: 'warning',
    message: 'Mara Vey needs more canon detail.',
    target_type: 'entity',
    entity_id: 'entity-1',
    relationship_id: null,
    status: 'open',
    note: null,
    first_seen: createdAt,
    last_seen: createdAt,
    updated_at: createdAt,
  },
];

const timelineEvents = [
  {
    id: 'timeline-1',
    world_id: world.id,
    title: 'Night of Falling Bells',
    event_order: 1,
    description: 'Every shrine bell fell silent at once.',
    participants: ['entity-1', 'entity-2'],
    causes: 'A broken pact',
    consequences: 'The tides learned names',
    date_label: 'First Tide',
    era_label: 'Bellfall',
    depends_on: [],
    created_at: createdAt,
  },
];

async function mockApi(page) {
  let mockDrafts = [];
  let mockSuggestions = suggestions.map((suggestion) => ({ ...suggestion }));
  let mockWorlds = [world];

  const getWorldById = (worldId) => mockWorlds.find((item) => item.id === worldId)
    ?? (worldId === createdWorld.id ? createdWorld : null)
    ?? (worldId === demoCreatedWorld.id ? demoCreatedWorld : null);

  await page.route('http://localhost:8000/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');
    const method = route.request().method();

    if (path === '/auth/me') return route.fulfill({ json: user });
    if (path === '/worlds' && method === 'GET') return route.fulfill({ json: mockWorlds });
    if (path === '/worlds' && method === 'POST') {
      const body = route.request().postDataJSON();
      const newWorld = {
        ...createdWorld,
        title: body.title,
        tone: body.tone,
        era_notes: body.era_notes,
        seed: body.seed,
      };
      mockWorlds = [newWorld, ...mockWorlds.filter((item) => item.id !== newWorld.id)];
      return route.fulfill({ status: 201, json: newWorld });
    }
    if (path === '/worlds/demo' && method === 'POST') {
      mockWorlds = [demoCreatedWorld, ...mockWorlds.filter((item) => item.id !== demoCreatedWorld.id)];
      return route.fulfill({ status: 201, json: { world: demoCreatedWorld } });
    }

    const worldMatch = path.match(/^\/worlds\/([^/]+)$/);
    if (worldMatch && method === 'GET') {
      const requestedWorld = getWorldById(worldMatch[1]);
      return requestedWorld
        ? route.fulfill({ json: requestedWorld })
        : route.fulfill({ status: 404, json: { detail: 'World not found' } });
    }

    if (path.match(/^\/worlds\/[^/]+\/entities$/)) return route.fulfill({ json: { entities } });
    if (path.match(/^\/worlds\/[^/]+\/relationships$/)) return route.fulfill({ json: { relationships } });
    if (path.match(/^\/worlds\/[^/]+\/timeline$/)) return route.fulfill({ json: { events: timelineEvents } });
    if (path === `/worlds/${world.id}/suggestions`) return route.fulfill({ json: { suggestions: mockSuggestions } });
    if (path === `/worlds/${world.id}/consistency/issues`) return route.fulfill({ json: { issues: consistencyIssues } });
    if (path === `/worlds/${world.id}/graph-views`) return route.fulfill({ json: { views: [] } });
    if (path === `/worlds/${world.id}/planning-boards`) return route.fulfill({ json: { boards: [] } });
    if (path === `/worlds/${world.id}/campaign-sessions`) return route.fulfill({ json: { sessions: [] } });
    if (path === `/worlds/${world.id}/lore-notes`) return route.fulfill({ json: { notes: [] } });
    if (path === `/worlds/${world.id}/faction-clocks`) return route.fulfill({ json: { clocks: [] } });
    if (path === `/worlds/${world.id}/drafts` && method === 'GET') return route.fulfill({ json: { drafts: mockDrafts } });
    if (path === `/worlds/${world.id}/drafts` && method === 'POST') {
      const body = route.request().postDataJSON();
      const draft = {
        id: `draft-${mockDrafts.length + 1}`,
        world_id: world.id,
        title: body.title,
        body: body.body,
        status: body.status ?? 'draft',
        linked_entity_ids: body.linked_entity_ids ?? [],
        linked_relationship_ids: body.linked_relationship_ids ?? [],
        linked_timeline_event_ids: body.linked_timeline_event_ids ?? [],
        check_history: [],
        created_at: createdAt,
        updated_at: createdAt,
      };
      mockDrafts = [draft, ...mockDrafts];
      return route.fulfill({ status: 201, json: draft });
    }
    const draftMatch = path.match(new RegExp(`^/worlds/${world.id}/drafts/([^/]+)$`));
    if (draftMatch && method === 'PATCH') {
      const body = route.request().postDataJSON();
      const draftId = draftMatch[1];
      mockDrafts = mockDrafts.map((draft) => (
        draft.id === draftId ? { ...draft, ...body, updated_at: '2026-01-02T00:00:00.000Z' } : draft
      ));
      return route.fulfill({ json: mockDrafts.find((draft) => draft.id === draftId) });
    }
    if (draftMatch && method === 'DELETE') {
      const draftId = draftMatch[1];
      mockDrafts = mockDrafts.filter((draft) => draft.id !== draftId);
      return route.fulfill({ status: 204, body: '' });
    }
    const checkMatch = path.match(new RegExp(`^/worlds/${world.id}/drafts/([^/]+)/check$`));
    if (checkMatch && method === 'POST') {
      const draftId = checkMatch[1];
      const report = {
        world_id: world.id,
        summary: '1 draft issue found.',
        issues: [{ code: 'entity-reference', severity: 'warning', message: 'Mara needs a clearer canon anchor.', entity_id: 'entity-1' }],
      };
      mockDrafts = mockDrafts.map((draft) => (
        draft.id === draftId
          ? { ...draft, check_history: [...draft.check_history, { checked_at: '2026-01-03T00:00:00.000Z', summary: report.summary, issues: report.issues }] }
          : draft
      ));
      return route.fulfill({ json: report });
    }
    const previewMatch = path.match(new RegExp(`^/worlds/${world.id}/drafts/([^/]+)/extract/preview$`));
    if (previewMatch && method === 'POST') {
      const draftId = previewMatch[1];
      const body = route.request().postDataJSON();
      return route.fulfill({
        json: {
          world_id: world.id,
          draft_id: draftId,
          summary: '1 candidate found.',
          excerpt: body.excerpt,
          candidates: [{
            candidate_kind: 'entity',
            suggested_name: 'Harbor Bell Secret',
            suggested_type: 'Concept',
            content: 'Mara heard the bell under Glass Harbor.',
            payload: { name: 'Harbor Bell Secret' },
          }],
        },
      });
    }
    const queueMatch = path.match(new RegExp(`^/worlds/${world.id}/drafts/([^/]+)/extract/queue$`));
    if (queueMatch && method === 'POST') {
      const draftId = queueMatch[1];
      const body = route.request().postDataJSON();
      const candidate = body.candidates[0];
      const draftSuggestion = {
        id: 'suggestion-draft-1',
        world_id: world.id,
        instruction: body.instruction ?? 'Extract draft canon',
        content: candidate.content,
        suggested_name: candidate.suggested_name,
        suggested_type: candidate.suggested_type,
        status: 'pending',
        created_at: createdAt,
        candidate_kind: candidate.candidate_kind,
        source_type: 'draft',
        source_id: draftId,
        source_excerpt: body.excerpt,
        payload: candidate.payload,
      };
      mockSuggestions = [...mockSuggestions, draftSuggestion];
      return route.fulfill({ json: { world_id: world.id, draft_id: draftId, summary: '1 suggestion queued.', suggestions: [draftSuggestion] } });
    }
    if (path === '/health') return route.fulfill({ json: { status: 'ok', llm: { mode: 'stub', enabled: false } } });
    if (path === `/worlds/${world.id}/agentic-generate`) return route.fulfill({ json: { content: 'Generated replacement lore for Mara.' } });
    if (path === `/worlds/${world.id}/entities/entity-1`) return route.fulfill({ json: { ...entities[0], description: 'Generated replacement lore for Mara.' } });

    return route.fulfill({ status: 404, json: { detail: 'Not found in accessibility test mock' } });
  });
}

async function checkA11y(page) {
  await page.waitForTimeout(600);
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('worldwright_access_token', 'test-token');
  });
  await mockApi(page);
});

test('dashboard home route exposes recent worlds and quick links', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Continue exploring your canon' })).toBeVisible();
  await expect(page.getByRole('link', { name: /Ember Archipelago/ })).toHaveAttribute('href', `/wiki/${world.id}`);
  await expect(page.getByRole('link', { name: /World Management/ })).toBeVisible();
  await expect(page.getByRole('link', { name: /Latest Wiki/ })).toHaveAttribute('href', `/wiki/${world.id}`);
  await expect(page.getByRole('link', { name: /Workbench/ })).toHaveAttribute('href', `/worlds/${world.id}`);
});

test('world cards open the wiki by default and expose the workbench', async ({ page }) => {
  await page.goto('/worlds');
  await expect(page.getByRole('link', { name: world.title })).toHaveAttribute('href', `/wiki/${world.id}`);
  await expect(page.getByRole('link', { name: /Island city-states/ })).toHaveAttribute('href', `/wiki/${world.id}`);
  await expect(page.getByRole('link', { name: /Workbench/ })).toHaveAttribute('href', `/worlds/${world.id}`);

  await page.goto(`/wiki/${world.id}`);
  await expect(page.getByRole('link', { name: /Edit Canon/ })).toHaveAttribute('href', `/worlds/${world.id}`);
});

test('new and demo world flows land on the wiki', async ({ page }) => {
  await page.goto('/worlds/new');
  await page.getByRole('textbox', { name: /World Title/ }).fill(createdWorld.title);
  await page.getByRole('button', { name: 'Create World' }).click();
  await page.waitForURL(`**/wiki/${createdWorld.id}`);
  await expect(page.getByRole('heading', { name: createdWorld.title })).toBeVisible();

  await page.goto('/');
  await page.getByRole('button', { name: 'Demo World' }).click();
  await page.waitForURL(`**/wiki/${demoCreatedWorld.id}`);
  await expect(page.getByRole('heading', { name: demoCreatedWorld.title })).toBeVisible();
});

test('worlds search and tone filter empty state are usable', async ({ page }) => {
  await page.goto('/worlds');
  await page.getByRole('searchbox', { name: 'Search worlds' }).fill('no matching world');
  await expect(page.getByText('No worlds match these filters')).toBeVisible();
  await page.getByRole('button', { name: 'Clear Filters' }).click();
  await expect(page.getByRole('heading', { name: world.title })).toBeVisible();
});

test('core routes have no automated axe violations', async ({ page }) => {
  for (const route of ['/', '/worlds', '/worlds/new', `/worlds/${world.id}`, `/wiki/${world.id}`]) {
    await page.goto(route);
    await expect(page.getByRole('main')).toBeVisible();
    await checkA11y(page);
  }
});

test('keyboard users can reach skip link, tabs, and graph summary selection', async ({ page }) => {
  await page.goto(`/worlds/${world.id}`);
  await expect(page.getByRole('tab', { name: /Dashboard/ })).toBeVisible();
  await expect(page.getByRole('tab', { name: /Canon/ })).toBeVisible();

  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to main content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();

  await page.getByRole('tab', { name: /Graph/ }).click();
  await expect(page.getByRole('heading', { name: 'Accessible graph summary' })).toBeVisible();
  await page.getByRole('button', { name: 'Glass Harbor', exact: true }).click();
  await page.getByRole('tab', { name: /Canon/ }).click();
  await expect(page.getByRole('textbox', { name: 'Entity name' })).toHaveValue('Glass Harbor');
});

test('workspace modes support keyboard navigation and selected context filters', async ({ page }) => {
  await page.goto(`/worlds/${world.id}`);
  for (const tab of ['Dashboard', 'Canon', 'Drafts', 'Timeline', 'Planning', 'Graph']) {
    await page.getByRole('tab', { name: tab }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('tab', { name: tab })).toHaveAttribute('aria-selected', 'true');
  }
  await page.getByRole('tab', { name: 'Canon' }).click();
  await expect(page.getByText('Showing relationships connected to Mara Vey')).toBeVisible();
  await page.getByRole('checkbox', { name: 'Show all' }).check();
  await expect(page.getByText('Mara Vey protects Glass Harbor')).toBeVisible();
});

test('world bible entity clicks open the canon editor', async ({ page }) => {
  await page.goto(`/worlds/${world.id}`);
  await expect(page.getByRole('tab', { name: 'Dashboard' })).toHaveAttribute('aria-selected', 'true');

  await page
    .getByLabel('World bible entity browser')
    .getByRole('button', { name: /Glass Harbor/ })
    .click();

  await expect(page.getByRole('tab', { name: 'Canon' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('textbox', { name: 'Entity name' })).toHaveValue('Glass Harbor');
});

test('world dashboard links into review and writing workflows', async ({ page }) => {
  await page.goto(`/worlds/${world.id}`);
  await expect(page.getByRole('heading', { name: 'World Dashboard' })).toBeVisible();
  await expect(page.getByRole('button', { name: /Open issues/ })).toContainText('1');
  await expect(page.getByRole('button', { name: /Bell Cipher/ })).toBeVisible();
  await page.getByRole('button', { name: /Mara Vey needs more canon detail/ }).click();
  await expect(page.getByRole('tab', { name: 'Canon' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('textbox', { name: 'Entity name' })).toHaveValue('Mara Vey');
});

test('draft workspace supports linked canon, checks, extraction, and delete', async ({ page }) => {
  page.on('dialog', (dialog) => dialog.accept());
  await page.goto(`/worlds/${world.id}`);
  await page.getByRole('tab', { name: 'Drafts' }).click();
  const draftsPanel = page.locator('#drafts-panel');

  await page.getByRole('textbox', { name: 'Draft title' }).fill('Bell Harbor scene');
  await page.getByLabel('Status').selectOption('revising');
  await page.getByRole('textbox', { name: 'Draft body' }).fill('Mara heard the bell under Glass Harbor before dawn.');
  await page.getByLabel('Linked entities').selectOption(['entity-1']);
  await page.getByLabel('Linked relationships').selectOption(['relationship-1']);
  await page.getByLabel('Linked timeline').selectOption(['timeline-1']);
  await page.getByRole('button', { name: 'Save Draft' }).click();

  await expect(page.getByRole('button', { name: /Bell Harbor scene/ })).toBeVisible();
  await expect(page.getByLabel('Linked canon context')).toContainText('Mara Vey');
  await expect(page.getByLabel('Linked canon context')).toContainText('Night of Falling Bells');

  await draftsPanel.getByRole('button', { name: 'Check', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Draft Review' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Draft Review' }).locator('xpath=ancestor::section')).toContainText('Mara needs a clearer canon anchor.');
  await expect(page.getByRole('button', { name: /Bell Harbor scene/ })).toContainText('1 check');

  const draftBody = page.getByRole('textbox', { name: 'Draft body' });
  await draftBody.focus();
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await page.keyboard.press('ArrowLeft');
  for (let index = 0; index < 15; index += 1) {
    await page.keyboard.press('Shift+ArrowRight');
  }
  await expect(page.getByLabel('Selected excerpt preview')).toContainText('Mara heard the');
  await page.getByRole('textbox', { name: 'Extraction focus' }).fill('Pull new concepts');
  await draftsPanel.getByRole('button', { name: 'Preview Extraction' }).click();

  await expect(page.getByLabel('Extraction candidate review')).toContainText('Harbor Bell Secret');
  await expect(page.getByRole('heading', { name: 'Canon Inbox' }).locator('xpath=ancestor::section')).not.toContainText('Harbor Bell Secret');
  await page.getByLabel('Extraction candidate review').getByRole('textbox', { name: 'Name', exact: true }).fill('Edited Harbor Bell');
  await page.getByRole('button', { name: 'Queue All' }).click();

  await expect(page.getByRole('heading', { name: 'Draft Suggestions' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Draft Suggestions' }).locator('xpath=ancestor::section')).toContainText('Edited Harbor Bell');
  await expect(page.getByRole('heading', { name: 'Canon Inbox' }).locator('xpath=ancestor::section')).toContainText('draft');

  await draftsPanel.getByRole('button', { name: 'Delete' }).click();
  await expect(page.getByText('No saved drafts yet.')).toBeVisible();
});

test('generated lore replace requires explicit confirmation', async ({ page }) => {
  await page.goto(`/worlds/${world.id}`);
  await page.getByRole('textbox', { name: 'Generation prompt' }).fill('Replace Mara description');
  await page.getByRole('button', { name: 'Generate' }).click();
  await expect(page.getByLabel('Generation and review tools').getByText('Generated replacement lore for Mara.')).toBeVisible();
  await page.getByRole('button', { name: 'Replace' }).click();
  await expect(page.getByRole('button', { name: 'Confirm Replace' })).toBeVisible();
});

test('mobile workspace has no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto(`/worlds/${world.id}`);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
});
