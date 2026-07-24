# Zielit — Marketing Website

A static, single-page marketing site for Zielit (email, phone, DM marketing, privacy assessment, AI enablement). No build step — plain HTML/CSS/JS, ready for GitHub Pages.

## Files
- `index.html` — all page content and sections
- `styles.css` — design system (colors, type, layout, animation)
- `script.js` — nav behavior, scroll reveal, contact form
- `assets/logo.png` — original raster logo (used as the apple-touch-icon)
- `assets/logo-mark.svg` — icon-only mark (mosaic + crosshair), used as the favicon
- `assets/logo-full-light.svg` — full logo lockup, white wordmark for dark backgrounds (nav, footer)
- `assets/logo-full-dark.svg` — full logo lockup, ink wordmark for light backgrounds (e.g. email signatures, printed use)

## Design system
- **Type:** Libre Franklin (display/headings) + Source Sans 3 (body) + IBM Plex Mono (labels, tags, eyebrows)
- **Color:** exact brand hexes lifted from the logo — coral `#EF4D3B`, indigo `#4D479A` — plus a void/ink pairing for dark sections. All defined as CSS variables at the top of `styles.css`.
- **Sections:** Hero → Capabilities (6, incl. AI Governance) → Process → AI Governance detail → Industries → Why Zielit → Perspectives → Careers → Contact.

## Deploy on GitHub Pages
1. Push these files to the root of your repo (`Jimit124/Zielit`), on the `main` branch.
2. In the repo: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, branch `main`, folder `/ (root)`.
3. Save. Your site will be live at `https://jimit124.github.io/Zielit/` within a couple of minutes.

## Using your zielit.com domain
1. Add a file named `CNAME` (no extension) to the repo root containing exactly:
   ```
   zielit.com
   ```
2. At your domain registrar, point DNS at GitHub Pages:
   - `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME` record for `www` → `jimit124.github.io`
3. Back in **Settings → Pages**, enter `zielit.com` as the custom domain and enable **Enforce HTTPS** once it's verified.

## Editing content
- Company email and service copy live directly in `index.html` — search for the section by its `id` (`#services`, `#contact`, `#careers`, etc.).
- Colors and fonts are all CSS variables at the top of `styles.css` under `:root`.
- The contact form submits to [FormSubmit.co](https://formsubmit.co/), a free form-backend service — no server code needed, and it delivers straight to `info@zielit.com`.
  - **One-time activation:** the very first time the form is submitted (by anyone, including your own test), FormSubmit sends a confirmation email to `info@zielit.com` asking you to activate the endpoint. Until that link is clicked, submissions won't be delivered. Check spam/junk in Zoho if it doesn't show up in the inbox within a few minutes.
  - After activation, every submission arrives as a formatted email. If the request ever fails (e.g. FormSubmit is unreachable), the form falls back to opening the visitor's own email client instead, so a message is never silently lost.
  - To route to a different inbox later, change the address in the form's `action` URL in `index.html` (search for `formsubmit.co`) — that also re-triggers the one-time activation step for the new address.

## Notes
- All graphics (the hero network animation, icons) are hand-built SVG/CSS — no stock photography was used, so there's nothing to license or swap out later. Real product/team photos can be dropped into `assets/` and referenced from `index.html` whenever you're ready.
- Social links in the footer are placeholders (`href="#"`) — add your real profile URLs when ready.
