# Changelog

## Workshop revision 22

- Categories now group together regardless of letter case or extra spaces, so `02-Media-01` and `02-MEDIA-02` share one MEDIA group instead of showing the header twice. Order numbers work across the merged group.
- When more than 24 apps need an HTTP check, a note under the list now says how many were not checked. Before, those apps simply had no dot.
- No option or layout changes. Existing setups look the same unless they were affected by one of the two issues above.

## Workshop revision 21

Workshop listing only; no widget code changes.

- Listing description now includes setup steps, including where to create the API token (Management > Tools > AI & MCP > Authentication > Create API token).

## Workshop revision 20

- Added optional automatic category columns, so the layout adjusts as you resize the widget while keeping categories together. Auto uses browser-balanced, top-to-bottom flow, not masonry; large categories can leave whitespace.
- Manual columns and Save space are still available. Auto is off by default, so existing layouts do not change unless you turn it on.
- Removed the fixed-color ring around status dots so it does not stand out on transparent boards. Dot dimensions and placement are unchanged.
- Existing template limits still apply. The 37-app/61-container test setup passed the enforced runtime limits across 24 option combinations; the heaviest manual/fuzzy combination has limited operation headroom, as it did in revision 19. Fuzzy matching remains best kept off unless needed.

Automatic layout suggested by [@Lefky](https://github.com/Lefky) in [#1](https://github.com/Clarkar00/homarr-categorized-app-list/issues/1).

## Workshop revision 19

- App tiles are now standard Homarr cards instead of hardcoded colors, so they follow board opacity, theme and custom CSS.
- Added side and bottom padding so tiles no longer touch the widget edge.
- Each tile has a `data-catlist-tile` attribute for custom CSS hover effects (example in the README). The widget sandbox blocks hover styles, so there is no built-in animation.

Suggested by [@Lefky](https://github.com/Lefky) in [#1](https://github.com/Clarkar00/homarr-categorized-app-list/issues/1).

## Workshop revision 18

- New **Category columns** option: show categories side by side, up to 6 columns. Default is 1, so existing widgets look the same until you change it.
- New **Save space** option: with 2+ columns, each category goes into the shortest column so the widget stays short.
- Full app name shows on hover when a name gets cut off in a narrow column.
- Faster container matching, so it does less work per render. Same matching results as revision 17.
- Docker-unavailable note now shows once above the list instead of inside it.
- Option descriptions now explain that columns are a maximum and that fuzzy matching can hit Homarr's template limit on bigger setups.

Columns and save space were suggested by [@Lefky](https://github.com/Lefky) in [#1](https://github.com/Clarkar00/homarr-categorized-app-list/issues/1).

## Workshop revision 17

Imported the public Workshop source without changing the widget.

Workshop release note:

> Added a setup screenshot showing how to tag apps. No code changes.

This repository starts at revision 17. Earlier development history is not reconstructed here.
Future release tags should match the corresponding Workshop revision (`workshop-r18`, etc.).
