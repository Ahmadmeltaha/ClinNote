# App map

Written by the loop from the app's files after each passing feature: what is already built. Read it before any file.

## Pages
- / → Home (app/page.tsx)

## Data and where it is kept
- None found.

## Shared
- None.

## Theme
None found.

## Files
- src/components/kit/alert.tsx (imported by 0): AlertKind, Alert
- src/components/kit/badge.tsx (imported by 0): Badge
- src/components/kit/button.tsx (imported by 0): ButtonKind, Button, ButtonRow
- src/components/kit/card.tsx (imported by 0): Card
- src/components/kit/dialog.tsx (imported by 0): Dialog
- src/components/kit/empty-state.tsx (imported by 0): EmptyState
- src/components/kit/field.tsx (imported by 0): Field
- src/components/kit/header.tsx (imported by 0): HeaderLink, SiteHeader
- src/components/kit/list.tsx (imported by 0): List, ListItem
- src/components/kit/nav-bar.tsx (imported by 0): NavBar
- src/components/kit/page-title.tsx (imported by 0): PageTitle
- src/components/kit/status-message.tsx (imported by 0): StatusMessage
- src/components/kit/table.tsx (imported by 0): Column, Table
- src/components/kit/theme-color.ts (imported by 0): themeColor, themeColorRgb, watchTheme

## Conventions
- Use the starter kit's parts in src/components/kit before writing your own: AlertKind, Alert, Badge, ButtonKind, Button, ButtonRow, Card, Dialog, EmptyState, Field, HeaderLink, SiteHeader, List, ListItem, NavBar, PageTitle, StatusMessage, Column, Table, themeColor, themeColorRgb, watchTheme.
- Dates in tests are relative to the clock, written {clock+Nd}, never a fixed date.
- Colours come only from the theme tokens above and their --color-on-* pairs, never a literal colour.

## Features
### OrchState Explainer Page
Requirements:
- When someone opens the page, a hero section is visible with a headline, a one-line description of OrchState, and a visual showing the idea-to-software flow.
- When someone scrolls down, a "What is OrchState" section is visible with a short paragraph and an icon or illustration.
- When someone continues scrolling, a "How it works" section is visible with 3 to 4 numbered steps, each with an icon and a short description (describe, approve, build, review).
- When someone scrolls further, a "Key features" section is visible showing 4 to 6 feature cards, each with a title, icon, and one-line description.
- When someone reaches the bottom, a closing section is visible with a summary line and a call-to-action button.
Added: app/page.tsx, src/components/kit/alert.tsx, src/components/kit/badge.tsx, src/components/kit/button.tsx, src/components/kit/card.tsx, src/components/kit/dialog.tsx, src/components/kit/empty-state.tsx, src/components/kit/field.tsx, src/components/kit/font-license.txt, src/components/kit/font.css, src/components/kit/header.tsx, src/components/kit/kit.css, src/components/kit/list.tsx, src/components/kit/nav-bar.tsx, src/components/kit/page-title.tsx, src/components/kit/status-message.tsx, src/components/kit/table.tsx, src/components/kit/theme-color.ts
Changed: none
