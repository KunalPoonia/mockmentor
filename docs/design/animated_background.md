---
name: Liquid Glass
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c4c7c8'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c6c6c7'
  primary: '#ffffff'
  on-primary: '#2f3131'
  primary-container: '#e2e2e2'
  on-primary-container: '#636565'
  inverse-primary: '#5d5f5f'
  secondary: '#c8c5cb'
  on-secondary: '#303034'
  secondary-container: '#47464b'
  on-secondary-container: '#b6b4b9'
  tertiary: '#ffffff'
  on-tertiary: '#303032'
  tertiary-container: '#e4e2e4'
  on-tertiary-container: '#656466'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c7'
  on-primary-fixed: '#1a1c1c'
  on-primary-fixed-variant: '#454747'
  secondary-fixed: '#e4e1e7'
  secondary-fixed-dim: '#c8c5cb'
  on-secondary-fixed: '#1b1b1f'
  on-secondary-fixed-variant: '#47464b'
  tertiary-fixed: '#e4e2e4'
  tertiary-fixed-dim: '#c8c6c8'
  on-tertiary-fixed: '#1b1b1d'
  on-tertiary-fixed-variant: '#474649'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  label-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding-desktop: 40px
  container-padding-mobile: 20px
  gutter: 24px
  safe-area: 32px
---

## Brand & Style
The design system for this AI mock interviewer is rooted in a "Liquid Glass" aesthetic, drawing heavy inspiration from modern, high-fidelity operating systems. The brand personality is serious, calm, and academic, aimed at professionals who seek a focused environment for high-stakes preparation.

The visual style is a refined mix of **Glassmorphism** and **Minimalism**. It simulates a dark, controlled studio environment where UI elements appear as physical slabs of smoked glass. The emotional response is one of quiet confidence and focused intensity. There is no gamification; instead, the system relies on physical metaphors—refraction, specular highlights, and continuous curves—to create a premium, tactile experience that feels authoritative and technologically advanced.

## Colors
The palette is centered on a "Dark Room" atmosphere. The foundation is a deep black (`#0A0A0A`), layered with charcoal grays to create depth. 

- **Primary Light Source:** A pure white (`#FFFFFF`) used exclusively for specular highlights, text, and active states. 
- **Glass Surfaces:** Neutral, smoked glass tones achieved through low-opacity grays rather than tints.
- **Accents:** Feedback is communicated through desaturated, soft-glowing tones. These are "burnt-in" colors that feel like they are emitting light from behind the smoked glass rather than being painted on top.

## Typography
The system uses **Inter** for its systematic, utilitarian precision. The typographic hierarchy is disciplined and spacious.

- **Headlines:** Use tighter letter-spacing and heavier weights to command authority.
- **Body Text:** Set with generous line height to ensure readability during long reading sessions or feedback reviews.
- **Labels:** Use a slightly heavier weight and increased tracking for clarity at small sizes, often paired with subtle secondary gray tones to maintain hierarchy.

## Layout & Spacing
The layout follows a **fluid grid** model with significant breathing room to maintain the "calm" brand pillar. Content is centered and grouped into logical "glass slabs."

- **Desktop:** A 12-column grid with wide gutters (24px) and significant outer margins (40px+) to create a floating effect.
- **Mobile:** A single-column flow with 20px side margins. 
- **Rhythm:** All spacing is a multiple of 8px. Use larger gaps (48px-64px) between major sections to emphasize the minimalist, focused nature of the interface.

## Elevation & Depth
Depth is created through high-fidelity glass simulation rather than traditional shadows.

- **Refraction:** All elevated containers must use `backdrop-filter: blur(20px)` and a background color of `rgba(42, 42, 46, 0.7)`.
- **Specular Highlights:** Use a 0.5px to 1px inset border on the top and left edges (`rgba(255, 255, 255, 0.15)`) to simulate a single off-center light source catching the "thickness" of the glass.
- **Shadows:** Use extremely diffused, large-radius black shadows (`blur: 40px`, `opacity: 40%`) to lift glass panels off the background without creating harsh edges.

## Shapes
The shape language is defined by **continuous curves** and high-radius corners. 

- **Containers:** Large slabs use a 32px corner radius to feel soft and intentional.
- **Interactive Elements:** Buttons and inputs use a full pill/capsule shape.
- **Inner Radii:** When nesting elements, ensure the inner radius is smaller than the outer radius (Inner = Outer - Padding) to maintain visual harmony.

## Components
- **Buttons:** Primary buttons are solid white with black text. Secondary buttons are "Glass Link" style: transparent with a subtle 1px border and blur. All buttons are capsule-shaped.
- **Cards:** Use the "Liquid Glass" treatment. No visible borders except for the top-weighted specular highlight. 
- **Input Fields:** Semi-transparent dark wells with a 1px bottom highlight. Focus states should trigger a soft white outer glow (5px blur).
- **Status Chips:** Small, pill-shaped indicators. Instead of solid fills, use a 10% opacity background of the status color with a 2px inner glow of the same color.
- **Lists:** Items are separated by subtle 0.5px lines with 10% white opacity. Active list items should "lift" using a slight increase in backdrop-blur and a subtle scale effect (1.02x).
- **Progress Indicators:** Use thin, continuous lines. The "filled" portion of a progress bar should have a slight white bloom effect to simulate light traveling through a glass fiber.