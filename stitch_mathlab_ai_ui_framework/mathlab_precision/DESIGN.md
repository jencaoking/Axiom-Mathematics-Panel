---
name: MathLab Precision
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#434655'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#4b41e1'
  on-secondary: '#ffffff'
  secondary-container: '#645efb'
  on-secondary-container: '#fffbff'
  tertiary: '#006058'
  on-tertiary: '#ffffff'
  tertiary-container: '#007b71'
  on-tertiary-container: '#b3fff3'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#e2dfff'
  secondary-fixed-dim: '#c3c0ff'
  on-secondary-fixed: '#0f0069'
  on-secondary-fixed-variant: '#3323cc'
  tertiary-fixed: '#89f5e7'
  tertiary-fixed-dim: '#6bd8cb'
  on-tertiary-fixed: '#00201d'
  on-tertiary-fixed-variant: '#005049'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-base:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  code:
    fontFamily: monospace
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  panel-gap: 1px
  container-padding: 12px
---

## Brand & Style

The design system is engineered for cognitive clarity and academic rigor. It draws heavily from the **Corporate / Modern** aesthetic, prioritizing a "tool-first" philosophy where the interface recedes to highlight the user's mathematical constructions. 

The style is defined by mathematical precision: every margin, stroke width, and alignment is governed by a strict geometric logic. It evokes the feeling of a high-end physical laboratory—clean, organized, and powerful. By blending minimalist layouts with functional depth (similar to modern IDEs), this design system ensures that complex AI-driven workflows feel manageable and sophisticated. The emotional goal is to instill confidence in the user, suggesting that the software is as accurate as the calculus it computes.

## Colors

The palette revolves around **Science Blue** (#2563EB) for primary actions and **Calculus Indigo** (#4F46E5) for brand accents and mathematical variables. This dual-primary approach distinguishes between interface interactions and educational content. 

The grayscale is expansive to support a "Tonal Layering" effect. In Light Mode, we use cool grays to prevent eye strain during long research sessions. Dark Mode shifts to a deep navy-charcoal base to minimize glow while maintaining high-contrast ratios for syntax highlighting in the Python console. Mathematical symbols and LaTeX text must always maintain a minimum contrast ratio of 7:1 against their respective backgrounds to ensure absolute readability.

## Typography

This design system utilizes **Inter** for all UI elements due to its exceptional legibility and neutral character. It is typeset on a tight scale to maximize the information density required for a desktop engineering application.

For the Python console and mathematical input fields, a system-standard **Monospace** font is utilized to ensure that character alignment in code blocks and matrix arrays is perfectly preserved. All labels for geometric tools use `label-caps` to distinguish them from user-generated content. Vertical rhythm is strictly enforced via a 4px baseline grid, ensuring that multi-line mathematical proofs remain orderly and scannable.

## Layout & Spacing

The layout follows a **Fixed Panel Grid** philosophy, mirroring professional IDEs. The screen is divided into four primary zones:
1.  **Toolbar (Top):** Fixed height (48px), horizontal layout.
2.  **Sidebar (Left/Right):** Collapsible, fixed width (280px) for property inspectors and layer trees.
3.  **Canvas (Center):** Fluid area that expands to fill all available space for geometric plotting.
4.  **Console (Bottom):** Resizable pane (default 200px height) for Python and AI output.

A "Ghost Border" approach is used for layout separation: instead of large gutters, panels are separated by 1px borders. Internal padding within panels follows a standard 12px (`3 units`) rule to balance density with breathability.

## Elevation & Depth

Hierarchy in this design system is primarily achieved through **Tonal Layers** rather than heavy shadows. 

The Canvas occupies the lowest elevation (Surface), appearing as a flat plane. Sidebars and toolbars sit at a slightly higher tonal value. Popovers, modals, and context menus use **Ambient Shadows**—soft, 12% opacity blurs with no offset—to indicate they are temporary overlays. A 1px internal "shine" (stroke) is applied to buttons in Light Mode to provide a subtle tactile feel without breaking the flat aesthetic. In Dark Mode, elevation is communicated through progressively lighter surface fills.

## Shapes

The shape language is conservative to maintain a professional, technical appearance. Most UI components (buttons, input fields, panels) utilize a **4px (0.25rem)** corner radius. 

Larger containers like cards or the main application window frame use an **8px (0.5rem)** radius. Geometric tool icons are contained within square bounding boxes to emphasize the grid-based nature of the software. Circular elements are reserved strictly for geometric "Points" on the canvas or status indicators, ensuring that the distinction between UI and mathematical data is clear.

## Components

### Buttons
Buttons are flat with a solid fill for primary actions and a 1px border for secondary actions. They use a horizontal padding of 16px and a height of 32px to maintain a compact, professional feel.

### Input Fields
Inputs use a "Focus Ring" in Science Blue. For mathematical expressions, the input field should expand vertically to accommodate fractions and exponents without clipping.

### Chips & Tags
Used for mathematical properties (e.g., `Parallel`, `Integer`). These are styled with a subtle background tint and no border, using `body-sm` typography for high density.

### Panels & Dividers
Panels use a header with a subtle background gray (#F1F5F9 in light mode) and 11px uppercase bold labels. Dividers are strictly 1px and use the defined border colors.

### Tool Icons
Icons must be 20x20px SVGs with a 1.5px stroke weight. They should be minimalist, representing geometric concepts (Points, Segments, Perpendicular lines) with mathematical accuracy.

### The Console
The Python console should feature a distinct background color (deeper than the main UI) to visually "set it apart" as a separate environment. Text should be syntax-highlighted using the tertiary (Teal) and secondary (Indigo) colors.