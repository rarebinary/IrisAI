# IrisAI Design System

## Visual Theme

IrisAI is a restrained product interface. The default is a light macOS scene:
a player glances at a local tool and wants a fast, calm confirmation that the
session is healthy. Dark mode is an intentionally quiet black-and-white working
surface for low-light use, not a neon gaming theme.

## Color Strategy

Cool-tinted neutral surfaces carry the interface. Use one muted indigo accent
for selection and direct actions. Green means healthy or victory, red means
error or defeat, and amber means attention. Colors must use semantic CSS tokens
with light and dark values.

## Typography

Use the system UI stack: `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, and
`system-ui`. Compact labels are medium weight, section headings are semibold,
and numeric data uses tabular figures. ASCII art is limited to the terminal
dashboard.

## Layout

Use a practical application shell with a compact sidebar and utility header.
The dashboard has three regions: a status strip, a primary current-run panel,
and an activity region for matches and events. Use flat surfaces, 6-8px corner
radii, fine separators, and modest shadows. Avoid nested cards.

## Components

- Status pills contain both a label and a text state.
- Current Run groups operating facts rather than marketing metrics.
- Match rows are compact timelines with result words, not color-only tiles.
- Event rows use plain category labels: State, Action, Match, Warning, or Error.
- Debug detail is a separate inline tab, never the default dashboard view.
- The light/dark theme control persists locally.

## Motion

Use 160-220ms opacity and color transitions for interactions. Avoid decorative
page-load choreography and respect `prefers-reduced-motion`.

## Brand Mark

Use the IrisAI Runbook mark as a small, single-color route-and-page symbol next
to the product name. It supports orientation and is not a hero image. The
canonical repository asset is `images/irisai-runbook.svg`; keep derivatives
visually aligned with that mark.
