# ASCENT Nexus 3.0 Crystal Wire

**Codename:** Crystal Wire
**Date:** 2026-08-13 (3.0.1 parse-law 2026-09-18)
**Ship:** Nexus / architecture card v3.0.1
**Codec:** ascent-wire 2.1.0 (in-tree parse-law: 4-byte surrogate + agent-fence hard-faults; SPEC 1.0.0-rc1)

## Intent

Raise the public Wire Lab to the Grok Build 4.6 premium bar without remapping the wire. Keep teal/cyan parse-law identity, manifesto voice, and Hello Universe. Add product chrome a lab can live in.

## Surface

Hybrid marketing + lab dashboard.

Skills applied: premium-web-design, premium-design-tokens, premium-typography, fontshare-priority, premium-layout-systems, premium-ui-surfaces, premium-ui-motion, premium-marketing-site-ux, premium-saas-dashboard-ux, premium-ui-a11y, premium-ui-performance, fleet-visitor-counter, site-upgrade-seo-aeo-cf, first-pass-ship, utf8-hygiene.

## What changed

| Area | Change |
|------|--------|
| Tokens | Semantic OKLCH, space scale, motion ladder, glass/grain surfaces |
| Type | Self-hosted Clash Display + Satoshi (no Google Fonts) |
| Nav | Brand island, X follow, Ctrl+K, 6 primary links, mobile drawer |
| Hero | One primary CTA + one secondary; quieter tour/GitHub/SPEC |
| Lab | Command palette, focus mode, compact density, toasts |
| Mission | HUD + timeline for captain-log / mixed streams |
| A11y | 44px targets, skip links, reduced motion, reduced transparency |
| Fleet | hits.jonbailey.xyz `data-site="ascent"` + CSP allow |
| SEO | llms / sitemap / FAQ + schema / OG ?v=3.0.1 |

## 3.0.1 parse-law

Decoders MUST hard-fault 4-byte residual UTF-16 surrogates (`F1 A5 AC A0` = U+D800) and nested/truncated agent fences (`9A`/`9B` inside args, truncated `C1 1B`). No new lead. Cont freeze `0xA0-0xBF` unchanged. Wire Lab gallery: Encoding guard, 4-byte surrogate, Agent fence fault.

## Preserve

- Parse law and frozen Cont 0xA0-0xBF packing
- SkyPulse honesty (usable session bandwidth, not RF Mbps)
- Sacred meter labeled sim
- MIT, @suddenlyjon, Hello Universe, SPEC try-this
