---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when building web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
version: 1.1.0
---

# Frontend Design

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. This client has already rejected proposals that felt templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take one real aesthetic risk you can justify.

## Ground it in the subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. If there's any information in your memory about the human's preferences, context about what they're building, or designs you've made before – use that as a hint. The subject's own world, its materials, instruments, artifacts, and vernacular, is where distinctive choices come from. Build with the brief's real content and subject matter throughout.

## Design principles

For web designs, the hero is a thesis. Open with the most characteristic thing in the subject's world, in whatever form makes sense for it: a headline, an image, an animation, a live demo, an interactive moment. Be deliberate with your choice: a big number with a small label, supporting stats, and a gradient accent is the template answer, only use if that's truly the best option.

Typography carries the personality of the page. Pair the display and body faces deliberately, not the same families you would reach for on any other project, and set a clear type scale with intentional weights, widths, and spacing. Make the type treatment itself a memorable part of the design, not a neutral delivery vehicle for the content.

Structure is information. Structural devices, numbering, eyebrows, dividers, labels, should encode something true about the content, not decorate it. Many generic designs use numbered markers (01 / 02 / 03), but that's only appropriate if the content actually is a sequence - like a real process or a typed timeline where order carries information the reader needs. Question if choices like numbered markers actually make sense before incorporating them.

Leverage motion deliberately. Think about where and if animation can serve the subject: a page-load sequence, a scroll-triggered reveal, hover micro-interactions, ambient atmosphere. An orchestrated moment usually lands harder than scattered effects; choose what the direction calls for. However, sometimes less is more, and extra animation contributes to the feeling that the design is AI-generated.

Match complexity to the vision. Maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Elegance is executing the chosen vision well.

Consider written content carefully. Often a design brief may not contain real content, and it's up to you to come up with copy. Copy can make a design feel as templated as the design itself. See the below section on writing for more guidance.

## Process: brainstorm, explore, plan, critique, build, critique again

For calibration: AI-generated design right now clusters around three looks: (1) a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta accent; (2) a near-black background with a single bright acid-green or vermilion accent; (3) a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns. All three are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on one of these defaults. Just like a human designer who's hired, there's often a careful balance between doing what you're good at and taking each project as a chance to experiment and learn.

Work in two passes. First, brainstorm a short design plan based on the human's design brief: create a compact token system with color, type, layout, and signature. Color: describe the palette as 4–6 named hex values. Type: the typefaces for 2+ roles (a characterful display face that's used with restraint, a complementary body face, and a utility face for captions or data if needed). Layout: a layout concept, using one-sentence prose descriptions and ASCII wireframes to ideate and compare. Signature: the single unique element this page will be remembered by that embodies the brief in an appropriate way.

Then review that plan against the brief before building: if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why. Only after you've confirmed the relative uniqueness of your design plan should you start to write the code, following the revised plan exactly and deriving every color and type decision from it.

When writing the code, be careful of structuring your CSS selector specificities. It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like .section and a element-based selector like .cta). This can happen often with paddings/margins between sections.

Try to do a lot of this planning and iteration in your thinking, and only show ideas to the user when you have higher confidence it'll delight them.

## Restraint and self-critique

Spend your boldness in one place. Let the signature element be the one memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Not taking a risk can be a risk itself! Build to a quality floor without announcing it: responsive down to mobile, visible keyboard focus, reduced motion respected. Critique your own work as you build, taking screenshots if your environment supports it – a picture is worth 1000 tokens. Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory. Human creators have memory and always try to do something new, so if you have a space to quickly jot down notes about what you've tried, it can help you in future passes.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration. Bring the same intentionality to copy that you would bring to spacing and color. Before writing anything, ask what the design needs to say, and how it can best be said to help the person navigate the experience.

Write from the end user's side of the screen. Name things by what people control and recognize, never by how the system is built. A person manages notifications, not webhook config. Describe what something does in plain terms rather than selling it. Being specific is always better than being clever.

Use active voice as default. A control should say exactly what happens when it's used: "Save changes," not "Submit." An action keeps the same name through the whole flow, so the button that says "Publish" produces a toast that says "Published." The vocabulary of an interface is the signposting for someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to fix it, in the interface's voice rather than a person's. Errors don't apologize, and they are never vague about what happened. An empty screen is an invitation to act.

Keep the register conversational and tuned: plain verbs, sentence case, no filler, with tone matched to the brand and the audience. Let each element do exactly one job. A label labels, an example demonstrates, and nothing quietly does double duty.

## Reference-Driven Redesign (when user provides screenshots or site references)

When the user rejects the current design ("too generic", "太土") and provides screenshots or points to existing websites as the target aesthetic, follow this workflow:

1. **Extract concrete design tokens from the reference**: Don't just say "dark and purple." Identify exact hex values, font families, structural elements (filmstrip notches, noise overlay, status pills with pulse dots, monospace labels, aurora blobs), and interaction patterns (hover lifts, avatar pulse rings, cubic-bezier message animations).
2. **Clone reference repos from GitHub for code patterns**: Search GitHub for similar projects (e.g. "live2d web chat dark", "cyberpunk portfolio"). HTTPS may fail due to TLS/rate limits — fall back to SSH (`git@github.com:user/repo.git`). Read their CSS variables, component structure, and key layout files to understand how they achieve specific effects (glassmorphism, backdrop-filter, filmstrip edges via `::before/::after` with radial-gradient patterns, noise via inline SVG turbulence filter).
3. **Map reference elements to existing codebase**: Before rewriting, read ALL current files (HTML, CSS, JS) to understand the existing structure. Then do a cohesive rewrite — don't patch individual properties; rewrite the entire CSS with the new design system, update HTML structure for new elements, and adjust JS for any new UI components (message counters, avatars, status indicators).
4. **Key design elements that elevate "tacky" to "premium"**:
   - Near-black backgrounds (#07070a) instead of dark blue (#0a0a1a)
   - Refined accent colors (#a855f7 purple, #f59e0b amber) instead of saturated blue-purple
   - Monospace fonts for labels/status/metadata (JetBrains Mono, Fira Code)
   - Subtle noise texture overlay (inline SVG, opacity 0.02-0.03)
   - Dynamic aurora background blobs (blurred, drifting, low opacity)
   - Filmstrip/industrial edge details via CSS pseudo-elements
   - Status indicators with pulse animations (green/amber dots)
   - Restrained particles (fewer, smaller, lower opacity)
   - Glass panels with layered shadows, not flat backgrounds

## Anti-Patterns (Avoid These)
- **Inter / Roboto / system-ui as display font** — these are body fonts, not headlines
- **Purple-to-blue gradients on white** — the default "tech startup" look
- **Centered hero with rounded-lg cards** — the default "SaaS landing" look
- **Excessive box-shadow** — one subtle shadow is enough
- **border-radius: 9999px on everything** — pills are not a design system
- **Placeholder images from unsplash** — use real product imagery or abstract SVG
- **Lorem ipsum** — write real copy that reflects the actual product
- **PPT-style page (色块+纯文字，无真实图片)** — 这是最常见的AI生成落地页失败模式：整页只有色块+文字，没有真实图片/插图，看起来像演示文稿。必须贯穿使用真实产品/场景图片（Unsplash等），图文交替布局，大胆撞色区块配图片，不用纯色块填充内容区域

## Dynamic Effects for Dark Themes (cyberpunk/tech aesthetic)

When a user says the page "has no dynamic elements" or "feels static", add layered ambient effects. Dark backgrounds (#07070a) need **higher opacity than intuition suggests** — values that look right in CSS (0.04, 0.15) are often invisible in actual browser rendering.

### Effect toolkit (proven patterns)

| Effect | Technique | Starting opacity |
|--------|-----------|-----------------|
| Cyber grid | `linear-gradient` crosshatch, 50px cells, `gridMove` animation | 0.08 |
| Particles | Canvas, 80-90 particles, dual-color (purple+cyan), mouse repulsion+connection lines, radial gradient glow per particle | 0.3-0.5 alpha |
| Scan line | Fixed div, `linear-gradient` with cyan glow, `scanMove` keyframe top→bottom | 0.8 |
| CRT texture | `repeating-linear-gradient` horizontal lines, 2px gaps | 0.25 |
| Mouse glow | 400px radial div, `mix-blend-mode: screen`, follows cursor | 0.08 |
| HUD corners | `::before/::after` L-shaped borders, 4 corners | 0.5 |
| Glitch text | `::before/::after` with `clip-path: inset()`, staggered `glitchTop/glitchBottom` keyframes, 90% idle 10% glitch | — |
| Data streams | Random char strings, `setInterval` 200ms refresh, `dataFloat` animation | 0.12 |
| Pill sweep | `::before` gradient bar, `pillSweep` left→right | 0.25-0.35 |
| Background parallax | `mousemove` → `transform: translate()` on bg image, ±15px | — |

### Critical pitfall: opacity calibration

After implementing dynamic effects, **always screenshot and verify**. Run `browser_vision` or `vision_analyze` on the deployed page and ask specifically whether each effect is visible. If effects are invisible:
- Grid lines: increase from 0.04 → 0.08
- Scan line: increase opacity 0.6 → 0.8, box-shadow 0.15 → 0.25
- CRT: increase 0.15 → 0.25
- Pill sweep: increase gradient stops 0.15 → 0.25-0.35, shorten animation duration

The verify-adjust-redeploy loop is essential: deploy → screenshot → vision analysis → patch opacity → redeploy. One round of calibration is usually enough.

## Quality Checklist

Before delivering, verify:
- [ ] Color palette has 4–6 named hex values, not just "primary/secondary"
- [ ] Typography has at least 2 distinct faces (display + body)
- [ ] Layout has a clear visual hierarchy (what's the hero?)
- [ ] There's one signature element that makes this memorable
- [ ] No anti-patterns from the list above
- [ ] Copy is written from user's perspective, not system's
- [ ] **Page is NOT PPT-style: real images throughout, image+text alternating layouts, bold color blocks with photos, no pure solid-color sections filling content areas**
- [ ] **Dynamic effects verified via screenshot — not just assumed visible**
- [ ] Responsive down to mobile viewport
- [ ] Focus states visible for keyboard navigation
- [ ] Reduced motion respected (prefers-reduced-motion)
