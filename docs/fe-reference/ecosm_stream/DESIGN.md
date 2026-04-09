# Design System Specification: The Ethereal Tech Ecosystem

## 1. Overview & Creative North Star
The North Star for this design system is **"The Digital Greenhouse."** 

We are moving away from the "industrial" feel of standard SaaS platforms toward a high-end, editorial experience that feels oxygenated, intentional, and premium. The system captures the intersection of high-technology and ecological responsibility. By utilizing a "breathing" layout—characterized by generous white space, intentional asymmetry, and tonal layering—we create an interface that feels less like a tool and more like a curated environment. 

We break the "template" look by avoiding rigid grid-locked boxes. Elements should feel like they are floating or "growing" within the space, using overlapping typography and staggered image placements to drive a sophisticated, non-linear narrative.

---

## 2. Colors: Tonal Depth & The "No-Line" Rule
The palette is built on the signature Cyan (#00B1A7), but its application must be surgical. We treat color as light and atmosphere rather than just decoration.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define sections. Boundaries must be established through background color shifts. Use `surface-container-low` (#f6f3f2) sections sitting on a `surface` (#fcf9f8) background to create invisible structure. 

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—stacked sheets of frosted glass or fine paper.
- **Base:** `surface` (#fcf9f8)
- **Nested Depth:** Place `surface-container-lowest` (#ffffff) cards on `surface-container-low` (#f6f3f2) backgrounds. This creates a soft "lift" that feels organic rather than mechanical.
- **Glass & Gradient:** For hero sections and primary CTAs, use a "Signature Texture." Instead of a flat #006a64, use a subtle linear gradient from `primary` (#006a64) to `primary_container` (#00b1a7).

### Color Tokens
- **Primary (Action):** `#006a64` (on_primary: `#ffffff`)
- **Primary Container (Vibrancy):** `#00b1a7` (on_primary_container: `#003d39`)
- **Secondary (Eco-Softness):** `#3f6566`
- **Surface (The Canvas):** `#fcf9f8`
- **Tertiary (Neutral Support):** `#56615c`

---

## 3. Typography: Editorial Authority
We utilize a dual-typeface system to balance technical precision with human warmth.

- **Display & Headlines (Be Vietnam Pro):** This is our "Editorial Voice." Use `display-lg` (3.5rem) with tight letter-spacing for high-impact statements. The sans-serif geometric nature of Be Vietnam Pro conveys the "Tech" in "Eco-Tech."
- **Body & Labels (Inter):** Inter is our "Utility Voice." It provides maximum legibility at smaller scales.
- **Hierarchy as Identity:** Use high contrast in scale. Pair a `display-md` headline with a `body-sm` caption to create a "Signature Editorial" look. Do not use medium-sized text for everything; embrace the extremes to guide the eye.

---

## 4. Elevation & Depth: The Layering Principle
We reject traditional drop shadows in favor of **Tonal Layering** and **Atmospheric Depth.**

- **The Layering Principle:** Depth is achieved by stacking surface tiers. To make a card stand out, don't add a shadow—change the container color from `surface-container` to `surface-container-lowest`.
- **Ambient Shadows:** If an element must float (e.g., a modal or floating action button), use a shadow with a blur radius of at least `32px` and an opacity of `4-6%`. Use a tint of `on_surface` (#1b1c1c) for the shadow color to ensure it looks like a natural occlusion of light.
- **Glassmorphism:** For top navigation bars or floating filters, use `surface_container_lowest` at 80% opacity with a `20px` backdrop-blur. This allows the signature cyan and teal accents of the background to "bleed through," making the UI feel integrated.
- **The Ghost Border Fallback:** If accessibility requires a stroke, use the `outline_variant` (#bbc9c7) at 15% opacity. Never use 100% opaque borders.

---

## 5. Components

### Buttons: The Tactile Interaction
- **Primary:** Gradient fill (`primary` to `primary_container`), `xl` (1.5rem) roundedness. No border.
- **Secondary:** `surface_container_high` fill with `primary` text. This feels more integrated than an outlined button.
- **Tertiary:** Text-only with a `primary` underline that expands on hover.

### Input Fields: Clean Slate
- **Style:** Use a `surface_container_highest` (#e5e2e1) background with a "Ghost Border" that transforms into a `primary` 2px bottom-only border upon focus.
- **Labels:** Use `label-md` in `on_surface_variant` (#3c4948) positioned above the field, never inside as placeholder text.

### Cards & Lists: Organic Separation
- **Forbidden:** Horizontal divider lines.
- **Method:** Separate list items using `16px` of vertical white space or by alternating background tones between `surface` and `surface_container_low`.
- **Rounding:** All cards must use `xl` (1.5rem) corner radius to reinforce the "soft/eco" brand profile.

### Chips: The Navigation Seed
- **Action Chips:** Use `secondary_container` (#bfe7e8) with `on_secondary_container` (#43696a) text. Use `full` (9999px) roundedness to create a pill shape that contrasts against the `xl` roundedness of cards.

---

## 6. Do’s and Don’ts

### Do:
- **Do** use asymmetric margins (e.g., 80px left, 120px right) for hero layouts to create a bespoke, premium feel.
- **Do** use `primary_fixed_dim` (#51dad0) for subtle background glows behind high-quality imagery.
- **Do** prioritize high-quality photography of nature and clean technology; the UI should act as a frame for this content.

### Don’t:
- **Don't** use pure black (#000000) for text. Use `on_surface` (#1b1c1c) to maintain a soft, high-end look.
- **Don't** use standard "Material Design" shadows. They are too heavy and break the "Digital Greenhouse" aesthetic.
- **Don't** use 1px dividers. If you feel the need to separate, use space. If space isn't enough, use a tonal shift.
- **Don't** crowd the interface. If a screen feels "busy," increase the padding by 50% across all containers.