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
  await page.route('http://localhost:8000/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');

    if (path === '/worlds') return route.fulfill({ json: [world] });
    if (path === `/worlds/${world.id}`) return route.fulfill({ json: world });
    if (path === `/worlds/${world.id}/entities`) return route.fulfill({ json: { entities } });
    if (path === `/worlds/${world.id}/relationships`) return route.fulfill({ json: { relationships } });
    if (path === `/worlds/${world.id}/timeline`) return route.fulfill({ json: { events: timelineEvents } });
    if (path === `/worlds/${world.id}/suggestions`) return route.fulfill({ json: { suggestions } });
    if (path === `/worlds/${world.id}/graph-views`) return route.fulfill({ json: { views: [] } });
    if (path === `/worlds/${world.id}/planning-boards`) return route.fulfill({ json: { boards: [] } });
    if (path === `/worlds/${world.id}/campaign-sessions`) return route.fulfill({ json: { sessions: [] } });
    if (path === `/worlds/${world.id}/lore-notes`) return route.fulfill({ json: { notes: [] } });
    if (path === `/worlds/${world.id}/faction-clocks`) return route.fulfill({ json: { clocks: [] } });
    if (path === `/worlds/${world.id}/drafts`) return route.fulfill({ json: { drafts: [] } });
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
  await mockApi(page);
});

test('dashboard home route exposes recent worlds and quick links', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Continue building your canon' })).toBeVisible();
  await expect(page.getByRole('link', { name: /Ember Archipelago/ })).toBeVisible();
  await expect(page.getByRole('link', { name: /World Management/ })).toBeVisible();
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
  for (const tab of ['Canon', 'Drafts', 'Timeline', 'Planning', 'Graph', 'Campaign']) {
    await page.getByRole('tab', { name: tab }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('tab', { name: tab })).toHaveAttribute('aria-selected', 'true');
  }
  await page.getByRole('tab', { name: 'Canon' }).click();
  await expect(page.getByText('Showing relationships connected to Mara Vey')).toBeVisible();
  await page.getByRole('checkbox', { name: 'Show all' }).check();
  await expect(page.getByText('Mara Vey protects Glass Harbor')).toBeVisible();
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
