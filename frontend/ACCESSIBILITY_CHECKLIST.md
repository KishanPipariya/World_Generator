# Accessibility Acceptance Checklist

Use this checklist before shipping substantial UI changes.

- Keyboard only: reach skip link, primary navigation, wiki reader controls, world cards, explicit workbench links, forms, tabs, graph summary controls, and destructive actions without a pointer.
- Screen reader smoke test: confirm page title heading, landmarks, tabs, form labels, live status/error messages, selected wiki/entity states, and graph summary are announced clearly.
- Zoom and reflow: verify Home, Worlds, Create World, Wiki, Workbench, DM workflow, and graph views at 200% browser zoom and narrow mobile widths.
- Reduced motion: enable OS/browser reduced motion and confirm page transitions and hover movement are effectively disabled.
- High contrast: verify focus rings, selected states, badges, alerts, relationship stance labels, and disabled controls remain distinguishable without relying on color alone.
- Form recovery: submit invalid or failed forms and confirm required fields, errors, and retry controls are understandable.
- Graph fallback: confirm every visible node and relationship can be reviewed and selected through the Accessible graph summary.
