# Worldwright Frontend

React, TypeScript, and Vite client for the world wiki reader and canon tools.

## Local Commands

- `npm run dev` starts the Vite dev server.
- `npm run lint` runs ESLint.
- `npm run build` runs TypeScript project checks and creates a production build.
- `npm run test:a11y` runs the Playwright accessibility smoke tests.
- `npm run check` runs lint, build, and accessibility checks.

## API Layout

`src/lib/api.ts` is the compatibility barrel used by existing pages. New API code should live in:

- `src/lib/apiClient.ts` for Axios setup and auth-token handling.
- `src/lib/apiTypes.ts` for shared response and payload types.
- `src/lib/api/*.ts` for domain-specific REST calls.

The default API base URL is `http://localhost:8000/api/v1`. Set `VITE_API_BASE_URL` when pointing the frontend at a different backend.

## Route Notes

The primary world destination is `src/pages/WorldWiki.tsx` at `/wiki/:worldId`.
Dashboards, recent links, world cards, and post-create/demo flows should open
that route by default.

The editable workbench remains `src/pages/WorldDetail.tsx` at `/worlds/:id`.
Keep links to it explicit and secondary with labels such as Workbench or Edit
Canon. Extracted helpers and stable workbench constants live under
`src/pages/worldDetail/`.

The dedicated DM workflow is `src/pages/WorldDm.tsx` at `/worlds/:id/dm` and
shares suggestion application helpers with the workbench.
