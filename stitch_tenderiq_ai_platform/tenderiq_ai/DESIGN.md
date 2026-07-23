---
name: TenderIQ AI
colors:
  surface: '#fcf8fa'
  surface-dim: '#dcd9db'
  surface-bright: '#fcf8fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f5'
  surface-container: '#f0edef'
  surface-container-high: '#eae7e9'
  surface-container-highest: '#e4e2e4'
  on-surface: '#1b1b1d'
  on-surface-variant: '#45464d'
  inverse-surface: '#303032'
  inverse-on-surface: '#f3f0f2'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#5c5e68'
  on-secondary: '#ffffff'
  secondary-container: '#dedfeb'
  on-secondary-container: '#60626c'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#271901'
  on-tertiary-container: '#98805d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#e1e2ed'
  secondary-fixed-dim: '#c4c6d1'
  on-secondary-fixed: '#191b24'
  on-secondary-fixed-variant: '#444650'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#fcf8fa'
  on-background: '#1b1b1d'
  surface-variant: '#e4e2e4'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  container-max: 1440px
  gutter: 24px
---

## Brand & Style

The design system is built for a high-stakes enterprise environment where procurement intelligence meets cutting-edge AI. The brand personality is **authoritative, analytical, and forward-leaning**. It avoids the cluttered "dashboard" aesthetic in favor of a focused, "canvas" approach similar to modern developer tools and AI interfaces.

The design style is **Modern Minimalist with Glassmorphic accents**. It utilizes a "Slate & Ink" foundation—heavy on whitespace and precise geometry—while using luminous gradients and backdrop blurs specifically to denote AI-generated insights and automated reasoning. The goal is to evoke a sense of "calm intelligence," where the UI recedes to let critical data and AI recommendations take center stage.

## Colors

The palette is anchored by **Deep Navy (#0F172A)**, used for primary text and structural grounding to establish trust. The core interaction color is **AI Blue (#3B82F6)**, while **Insight Purple (#8B5CF6)** is reserved exclusively for AI-generated suggestions, tender scoring, and predictive analytics.

- **Primary & Secondary:** Deep Navy provides high-contrast readability; Blue and Purple provide the "energy" of the platform.
- **Neutrals:** A sophisticated range of Slates ($50 through $900) manages hierarchy without introducing visual noise.
- **Semantic:** Success, Warning, and Critical colors use a slightly desaturated "Pro" tone to remain visible but not jarring within the professional context.
- **Surface Strategy:** Backgrounds utilize a subtle cool-white (#F8FAFC) to reduce eye strain during long procurement review sessions.

## Typography

This design system utilizes **Inter** for its exceptional legibility in data-heavy environments. To create a "tech-forward" distinction for metadata and technical specs, **Geist** (a monospaced-adjacent sans) is used for labels and small data points.

Hierarchy is enforced through tight letter-spacing on larger headings to create a "premium editorial" feel. Body text maintains a generous line height (1.5x) to ensure complex tender documents remain readable. Use **Deep Navy** for all headings and **Slate 600** for secondary body text.

## Layout & Spacing

The layout follows an **8px linear grid system**. The structure is a **Fixed-Fluid hybrid**: sidebars and navigation are fixed, while the primary workspace (the "Canvas") expands to fill the viewport, capped at a 1440px max-width for readability.

- **Desktop:** 12-column grid, 24px gutters, 48px page margins.
- **Tablet:** 8-column grid, 16px gutters, 24px page margins.
- **Mobile:** 4-column grid, 16px gutters, 16px page margins.

Spacing should be utilized to "group" logic. For example, 8px between a label and input, but 24px between distinct form sections. This "chunking" method helps users process complex procurement data faster.

## Elevation & Depth

Depth is used sparingly and purposefully. The design system uses three primary elevation levels:

1.  **Flat (Level 0):** Used for the main background and structural layout dividers.
2.  **Raised (Level 1):** Subtle 1px borders (Slate 200) with a very soft shadow (0px 4px 12px rgba(15, 23, 42, 0.03)). Used for standard cards and table rows.
3.  **Overlay (Level 2):** Glassmorphic surfaces with a 12px backdrop blur and 60% opacity white fill. This is reserved for AI insights, popovers, and floating action bars to signify they exist "above" the static data.

Instead of heavy shadows, we use **inner borders** and **tonal shifts** to indicate interactivity.

## Shapes

The shape language is **Professional Rounded**. 
- **Standard Elements:** 8px (0.5rem) radius for buttons, input fields, and small cards.
- **Large Containers:** 16px (1rem) radius for main content areas and modals.
- **Tags/Chips:** Fully pill-shaped (100px) to distinguish them from interactive buttons.

This approach balances the "industrial" feel of procurement with the "modern" feel of an AI-first startup.

## Components

### Buttons
- **Primary:** Deep Navy background, white text. No gradient. 8px radius.
- **AI Action:** AI Blue background with a subtle "Insight Purple" inner glow.
- **Ghost:** No background, Slate 600 text, becomes Slate 100 on hover.

### Cards
Cards are the primary unit of the UI. They feature a white background, 1px border (#E2E8F0), and 12px rounded corners. For **AI Insights**, the card should feature a 2px left-border accent in Insight Purple and a very faint purple tint in the background.

### Data Tables
Tables should be "clean-room" style. No vertical lines. Horizontal lines should be #F1F5F9. Header text uses the **label-sm** style in Slate 500. Row hover state uses a subtle Blue 50 tint.

### Inputs & Selects
Strict 8px radius. 1px border in Slate 300. On focus, the border transitions to AI Blue with a 3px soft blue outer glow (0.2 opacity).

### AI Insight Chips
Interactive tokens that use the **Insight Purple** color at 10% opacity for the background and 100% opacity for the text, paired with a small sparkle icon.