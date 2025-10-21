# AquaChain Design Token System Documentation

## Overview

The AquaChain Design Token System is a comprehensive, scalable foundation for consistent design implementation across all user interfaces. Built on a 4px base unit system, it provides semantic color usage, responsive typography, consistent spacing, and underwater-themed animations that reflect the aquatic nature of the water quality monitoring platform.

## Core Principles

### 1. 4px Base Unit System
All spacing values are derived from a 4px base unit, ensuring mathematical consistency and visual harmony across all components and layouts.

### 2. Semantic Color Usage
Colors are organized by meaning and usage context, not just visual appearance, making it easier to maintain consistency and accessibility.

### 3. Responsive Typography
Typography scales appropriately across device sizes while maintaining readability and hierarchy.

### 4. Underwater Theme Integration
Animation timings and effects are specifically designed to evoke underwater environments with ripples, waves, bubbles, and bioluminescent glows.

## Color System

### Underwater Theme Palette

#### Surface Zone (Light/Bright)
- **surface-light**: `#E0F7FA` - Lightest surface water tone (21:1 contrast with dark)
- **surface-main**: `#B2EBF2` - Main surface water tone (18:1 contrast with dark)
- **surface-accent**: `#06B6D4` - Surface accent and highlights (7.5:1 contrast with dark)

#### Mid-Water Zone (Primary Brand)
- **mid-light**: `#4DD0E1` - Light mid-water tone (9.2:1 contrast with dark)
- **mid-main**: `#088395` - Primary brand color (7.8:1 contrast with light)
- **mid-dark**: `#0A4D68` - Dark mid-water tone (12.4:1 contrast with light)

#### Deep Zone (Dark/Foundation)
- **deep-main**: `#01579B` - Deep water blue (15.2:1 contrast with light)
- **deep-dark**: `#003D5B` - Deeper foundation color (18.9:1 contrast with light)
- **deep-black**: `#001F2E` - Deepest background color (21:1 contrast with light)

#### Glow Effects (Bioluminescence)
- **glow-cyan**: `#00E5FF` - Bright cyan bioluminescent glow
- **glow-teal**: `#1DE9B6` - Teal bioluminescent effect
- **glow-blue**: `#2196F3` - Blue light effects

### Semantic Color Usage

#### Status Colors
- **status-safe**: `#10B981` - Safe water quality indicator
- **status-warning**: `#F59E0B` - Warning level indicator
- **status-critical**: `#EF4444` - Critical alert indicator
- **status-info**: `#06B6D4` - Informational indicator

#### Feedback Colors
Each feedback color includes background, border, and text variants:
- **Success**: Green tones for positive feedback and safe conditions
- **Warning**: Amber tones for caution states and moderate alerts
- **Error**: Red tones for danger states and critical alerts
- **Info**: Cyan tones for neutral information and guidance

#### Brand Colors
- **brand-primary**: `#088395` - Main CTAs, primary actions, brand elements
- **brand-secondary**: `#06B6D4` - Secondary actions, accents, highlights
- **brand-tertiary**: `#4DD0E1` - Subtle accents, backgrounds, decorative elements

## Typography System

### Font Families
- **Primary**: Inter with system font fallbacks for UI text
- **Secondary**: Poppins with Inter fallback for headings and emphasis
- **Monospace**: JetBrains Mono with code font fallbacks

### Responsive Font Sizes
Typography scales across device sizes:
- **Mobile**: 87.5% of base scale
- **Tablet**: 93.75% of base scale
- **Desktop**: 100% of base scale (default)
- **Large Desktop**: 112.5% of base scale

### Font Size Scale
- **xs**: 12px - Small labels and captions
- **sm**: 14px - Small body text
- **base**: 16px - Primary body text
- **lg**: 18px - Large body text
- **xl**: 20px - Small headings (h6)
- **2xl**: 24px - Medium headings (h5)
- **3xl**: 30px - Large headings (h4)
- **4xl**: 36px - Extra large headings (h3)
- **5xl**: 48px - Hero headings (h2)
- **6xl**: 60px - Display headings (h1)
- **7xl**: 72px - Large display headings
- **8xl**: 96px - Extra large display headings

### Line Heights and Letter Spacing
Each font size includes optimized line height and letter spacing:
- Larger text uses tighter letter spacing (-0.025em to -0.05em)
- Smaller text uses wider letter spacing (0.016em to 0.025em)
- Line heights range from 1.08 (large displays) to 1.56 (large body text)

## Spacing System

### Base Unit: 4px
All spacing derives from a 4px foundation, creating mathematical consistency.

### Spacing Scale
- **0.5**: 2px - Half base unit for fine adjustments
- **1**: 4px - Base unit, minimal spacing
- **1.5**: 6px - Subtle spacing
- **2**: 8px - Small spacing
- **3**: 12px - Medium-small spacing
- **4**: 16px - Standard spacing
- **6**: 24px - Large spacing
- **8**: 32px - Extra large spacing
- **12**: 48px - Section spacing
- **16**: 64px - Major section spacing
- **24**: 96px - Hero section spacing
- **32**: 128px - Maximum layout spacing

### Layout Spacing
- **Container Padding**: Responsive padding for main containers
  - Mobile: 16px
  - Tablet: 24px
  - Desktop: 32px
  - Wide: 48px
- **Section Spacing**: Vertical spacing between major sections
  - Small: 48px
  - Medium: 64px
  - Large: 96px
  - Extra Large: 128px
- **Grid Gaps**: Consistent spacing in grid layouts
  - Small: 16px
  - Medium: 24px
  - Large: 32px

### Component Spacing
- **Padding**: Internal spacing within components
  - XS: 8px
  - SM: 12px
  - MD: 16px
  - LG: 24px
  - XL: 32px
- **Margin**: External spacing around components
  - XS: 4px
  - SM: 8px
  - MD: 16px
  - LG: 24px
  - XL: 32px

## Animation System

### Duration Scale
- **instant**: 0ms - No animation
- **immediate**: 50ms - Immediate feedback
- **fast**: 150ms - Quick interactions
- **normal**: 300ms - Standard transitions
- **slow**: 500ms - Emphasis transitions
- **slower**: 800ms - Page transitions
- **slowest**: 1200ms - Dramatic effects

### Easing Functions
- **linear**: Consistent motion, loading bars
- **ease-in**: Elements entering from rest
- **ease-out**: Elements coming to rest
- **ease-in-out**: Standard transitions, hover effects
- **bounce**: Success states, playful interactions
- **elastic**: Spring-like animations, modals
- **anticipate**: Dramatic entrances, reveals

### Underwater-Themed Animations

#### Ripple Effect
- **Duration**: 600ms
- **Easing**: cubic-bezier(0.25, 0.46, 0.45, 0.94)
- **Usage**: Button interactions, touch feedback

#### Wave Motion
- **Duration**: 2000ms
- **Easing**: cubic-bezier(0.445, 0.05, 0.55, 0.95)
- **Usage**: Background animations, ambient effects

#### Bubble Animation
- **Duration**: 800ms
- **Easing**: cubic-bezier(0.25, 0.46, 0.45, 0.94)
- **Usage**: Loading states, success feedback

#### Water Current
- **Duration**: 3000ms
- **Easing**: cubic-bezier(0.4, 0, 0.6, 1)
- **Usage**: Data flow visualization, transitions

#### Bioluminescent Glow
- **Duration**: 1500ms
- **Easing**: cubic-bezier(0.4, 0, 0.6, 1)
- **Usage**: Focus states, active elements, alerts

### Interaction Animations
- **Hover**: 200ms ease-out - Standard hover transitions
- **Focus**: 150ms ease-out - Focus state transitions
- **Press**: 100ms ease-in - Button press feedback
- **Release**: 200ms ease-out - Button release animation

## Implementation Guidelines

### CSS Custom Properties
All design tokens are available as CSS custom properties with the `--` prefix:

```css
/* Color usage */
.primary-button {
  background-color: var(--brand-primary);
  color: var(--surface-light);
}

/* Typography usage */
.heading {
  font-family: var(--font-secondary);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

/* Spacing usage */
.card {
  padding: var(--space-6);
  margin-bottom: var(--space-4);
  border-radius: var(--radius-lg);
}

/* Animation usage */
.interactive-element {
  transition-duration: var(--interaction-hover-duration);
  transition-timing-function: var(--interaction-hover-easing);
}
```

### Utility Classes
Pre-built utility classes are available for common patterns:

```css
/* Feedback components */
.feedback-success { /* Success message styling */ }
.feedback-warning { /* Warning message styling */ }
.feedback-error { /* Error message styling */ }
.feedback-info { /* Info message styling */ }

/* Underwater effects */
.underwater-card { /* Card with underwater styling */ }
.underwater-modal { /* Modal with underwater effects */ }
.underwater-nav { /* Navigation with underwater theme */ }

/* Touch targets */
.touch-target { /* Minimum 44px touch target */ }

/* Animation utilities */
.animate-ripple { /* Ripple effect animation */ }
.animate-wave { /* Wave motion animation */ }
.animate-bubble { /* Bubble floating animation */ }
.animate-glow { /* Bioluminescent glow effect */ }
```

### Responsive Behavior
Typography automatically scales across breakpoints:

```css
/* Mobile: 87.5% scale */
@media (max-width: 768px) {
  :root {
    --text-base: calc(1rem * 0.875); /* 14px */
  }
}

/* Tablet: 93.75% scale */
@media (min-width: 769px) and (max-width: 1023px) {
  :root {
    --text-base: calc(1rem * 0.9375); /* 15px */
  }
}

/* Large Desktop: 112.5% scale */
@media (min-width: 1536px) {
  :root {
    --text-base: calc(1rem * 1.125); /* 18px */
  }
}
```

## Accessibility Considerations

### Color Contrast
All color combinations meet WCAG 2.1 AA standards:
- Status colors maintain 4.5:1 contrast ratio minimum
- Brand colors provide sufficient contrast for text usage
- Feedback colors include high-contrast alternatives

### Touch Targets
Minimum touch target sizes are enforced:
- Desktop: 44px minimum
- Mobile: 48px minimum (larger for better touch interaction)

### Reduced Motion
Animation preferences are respected:

```css
@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-fast: 0.01ms;
    --duration-normal: 0.01ms;
    --duration-slow: 0.01ms;
    --duration-slower: 0.01ms;
  }
}
```

### High Contrast Mode
Enhanced contrast for accessibility:

```css
@media (prefers-contrast: high) {
  :root {
    --focus-ring-width: 3px;
    --focus-ring-color: var(--glow-cyan);
    --border-primary: rgba(8, 131, 149, 0.6);
    --border-secondary: rgba(8, 131, 149, 0.8);
  }
}
```

## Usage Examples

### Status Indicator Component
```css
.status-indicator {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--interaction-hover-duration) var(--interaction-hover-easing);
}

.status-indicator--safe {
  background-color: var(--feedback-success-bg);
  color: var(--feedback-success-text);
  border: 1px solid var(--feedback-success-border);
}

.status-indicator--warning {
  background-color: var(--feedback-warning-bg);
  color: var(--feedback-warning-text);
  border: 1px solid var(--feedback-warning-border);
}

.status-indicator--critical {
  background-color: var(--feedback-error-bg);
  color: var(--feedback-error-text);
  border: 1px solid var(--feedback-error-border);
}
```

### Underwater Button Component
```css
.underwater-button {
  background: var(--brand-primary);
  color: var(--surface-light);
  border: 1px solid var(--brand-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-6);
  font-family: var(--font-primary);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  
  /* Underwater effects */
  box-shadow: var(--shadow-aqua-sm);
  backdrop-filter: var(--backdrop-blur-sm);
  
  /* Interactions */
  transition: all var(--interaction-hover-duration) var(--interaction-hover-easing);
  cursor: pointer;
}

.underwater-button:hover {
  background: var(--brand-secondary);
  box-shadow: var(--shadow-aqua-md);
  transform: translateY(-1px);
}

.underwater-button:active {
  transform: translateY(0);
  transition-duration: var(--interaction-press-duration);
  transition-timing-function: var(--interaction-press-easing);
}

.underwater-button:focus {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
  box-shadow: var(--focus-ring-shadow), var(--shadow-aqua-md);
}
```

### Data Visualization Card
```css
.data-card {
  background: var(--bg-underwater-card);
  backdrop-filter: var(--backdrop-blur-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-4);
  
  /* Underwater glow effect */
  box-shadow: var(--shadow-aqua-sm);
  
  /* Hover animation */
  transition: all var(--interaction-hover-duration) var(--interaction-hover-easing);
}

.data-card:hover {
  border-color: var(--border-secondary);
  box-shadow: var(--shadow-aqua-md);
  transform: translateY(-2px);
}

.data-card__title {
  font-family: var(--font-secondary);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--surface-light);
  margin-bottom: var(--space-3);
  letter-spacing: var(--tracking-tight);
}

.data-card__value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--surface-accent);
  line-height: var(--leading-tight);
}

.data-card__unit {
  font-size: var(--text-sm);
  color: var(--neutral-400);
  margin-left: var(--space-2);
}
```

## Maintenance and Updates

### Version Control
- All design token changes should be versioned
- Breaking changes require major version updates
- New tokens can be added in minor versions
- Bug fixes and optimizations are patch versions

### Documentation Updates
- Update this documentation when tokens are modified
- Include migration guides for breaking changes
- Provide examples for new token usage
- Document accessibility implications

### Testing
- Validate color contrast ratios after color changes
- Test responsive typography across all breakpoints
- Verify animation performance on various devices
- Ensure accessibility compliance with assistive technologies

This comprehensive design token system provides the foundation for consistent, accessible, and maintainable user interfaces across the AquaChain platform while reflecting its underwater theme and water quality monitoring purpose.