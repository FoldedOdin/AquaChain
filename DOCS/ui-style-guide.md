# AquaChain UI Style Guide

## Overview

This comprehensive UI Style Guide defines the visual design system for AquaChain, a cloud-native water quality monitoring platform. The design system is built around an underwater theme that creates an immersive, aquatic experience while maintaining professional functionality and accessibility standards.

## Design Philosophy

### Core Principles

1. **Aquatic Immersion**: Every interface element should evoke the feeling of being underwater, with flowing animations, ripple effects, and depth-based layering
2. **Clarity Through Depth**: Use visual depth and transparency to create clear information hierarchy
3. **Fluid Responsiveness**: All components should flow naturally across different screen sizes like water adapts to its container
4. **Accessible by Design**: Maintain WCAG 2.1 AA compliance while preserving the underwater aesthetic
5. **Performance First**: Animations and effects should enhance rather than hinder user experience

## Color System

### Primary Color Palette

The AquaChain color system is organized by underwater depth zones, creating a natural progression from surface to deep ocean.

#### Surface Zone (Light/Bright)

```css
--surface-light: #e0f7fa; /* Lightest surface water */
--surface-main: #b2ebf2; /* Main surface tone */
--surface-accent: #06b6d4; /* Surface accent/highlights */
```

#### Mid-Water Zone (Primary Brand)

```css
--mid-light: #4dd0e1; /* Light mid-water */
--mid-main: #088395; /* Primary brand color */
--mid-dark: #0a4d68; /* Dark mid-water */
```

#### Deep Zone (Dark/Foundation)

```css
--deep-main: #01579b; /* Deep water blue */
--deep-dark: #003d5b; /* Deeper foundation */
--deep-black: #001f2e; /* Deepest background */
```

#### Glow Effects (Bioluminescence)

```css
--glow-cyan: #00e5ff; /* Bright cyan glow */
--glow-teal: #1de9b6; /* Teal bioluminescence */
--glow-blue: #2196f3; /* Blue light effects */
```

### Semantic Colors

#### Status Colors (Water Quality)

```css
--status-safe: #10b981; /* Safe water quality */
--status-warning: #f59e0b; /* Warning levels */
--status-critical: #ef4444; /* Critical alerts */
--status-info: #06b6d4; /* Informational */
```

#### Neutral Colors

```css
--neutral-50: #f8fafc; /* Lightest neutral */
--neutral-100: #f1f5f9; /* Light text on dark */
--neutral-200: #e2e8f0; /* Light borders */
--neutral-300: #cbd5e1; /* Medium text */
--neutral-400: #94a3b8; /* Muted text */
--neutral-500: #64748b; /* Secondary text */
--neutral-600: #475569; /* Dark secondary */
--neutral-700: #334155; /* Dark text */
--neutral-800: #1e293b; /* Very dark */
--neutral-900: #0f172a; /* Darkest */
```

### Color Usage Guidelines

#### Background Hierarchy

- **Primary Background**: `--deep-black` for main application background
- **Card/Panel Background**: `rgba(15, 23, 42, 0.8)` with backdrop blur
- **Modal/Overlay Background**: `rgba(0, 31, 46, 0.9)` with backdrop blur
- **Hover States**: `rgba(8, 131, 149, 0.1)` for subtle interactions

#### Text Hierarchy

- **Primary Text**: `--neutral-100` for main content
- **Secondary Text**: `--neutral-300` for supporting content
- **Muted Text**: `--neutral-500` for less important information
- **Interactive Text**: `--surface-accent` for links and actions

#### Interactive Elements

- **Primary Actions**: `linear-gradient(135deg, #088395, #06B6D4)`
- **Secondary Actions**: Transparent with `--surface-accent` border
- **Hover States**: Add `--glow-cyan` shadow and slight scale transform
- **Active States**: Darker gradient with increased shadow

## Typography System

### Font Families

#### Primary Font Stack

```css
font-family:
  'Inter',
  -apple-system,
  BlinkMacSystemFont,
  'Segoe UI',
  'Roboto',
  sans-serif;
```

#### Monospace Font Stack

```css
font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', monospace;
```

### Font Scale

#### Headings

```css
--text-xs: 0.75rem; /* 12px - Small labels */
--text-sm: 0.875rem; /* 14px - Body small */
--text-base: 1rem; /* 16px - Body text */
--text-lg: 1.125rem; /* 18px - Large body */
--text-xl: 1.25rem; /* 20px - Small heading */
--text-2xl: 1.5rem; /* 24px - Medium heading */
--text-3xl: 1.875rem; /* 30px - Large heading */
--text-4xl: 2.25rem; /* 36px - XL heading */
--text-5xl: 3rem; /* 48px - Hero heading */
--text-6xl: 3.75rem; /* 60px - Display heading */
```

#### Font Weights

```css
--font-thin: 100;
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

#### Line Heights

```css
--leading-tight: 1.25; /* Headings */
--leading-snug: 1.375; /* Subheadings */
--leading-normal: 1.5; /* Body text */
--leading-relaxed: 1.625; /* Large body text */
--leading-loose: 2; /* Spacious text */
```

### Typography Usage

#### Heading Hierarchy

```css
/* Hero Title */
.hero-title {
  font-size: var(--text-6xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  background: linear-gradient(135deg, #e0f7fa 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Section Title */
.section-title {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  color: var(--neutral-100);
}

/* Card Title */
.card-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
  color: var(--neutral-100);
}

/* Body Text */
.body-text {
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--neutral-300);
}
```

## Spacing System

### Base Unit

The spacing system uses a 4px base unit for consistent rhythm and alignment.

```css
--space-px: 1px;
--space-0: 0;
--space-1: 0.25rem; /* 4px */
--space-2: 0.5rem; /* 8px */
--space-3: 0.75rem; /* 12px */
--space-4: 1rem; /* 16px */
--space-5: 1.25rem; /* 20px */
--space-6: 1.5rem; /* 24px */
--space-8: 2rem; /* 32px */
--space-10: 2.5rem; /* 40px */
--space-12: 3rem; /* 48px */
--space-16: 4rem; /* 64px */
--space-20: 5rem; /* 80px */
--space-24: 6rem; /* 96px */
--space-32: 8rem; /* 128px */
```

### Layout Spacing

#### Container Spacing

```css
--container-padding-mobile: var(--space-4); /* 16px */
--container-padding-tablet: var(--space-6); /* 24px */
--container-padding-desktop: var(--space-8); /* 32px */
```

#### Component Spacing

```css
--component-padding-sm: var(--space-3); /* 12px */
--component-padding-md: var(--space-4); /* 16px */
--component-padding-lg: var(--space-6); /* 24px */
--component-padding-xl: var(--space-8); /* 32px */
```

#### Grid Gaps

```css
--grid-gap-sm: var(--space-4); /* 16px */
--grid-gap-md: var(--space-6); /* 24px */
--grid-gap-lg: var(--space-8); /* 32px */
```

## Animation System

### Duration Scale

```css
--duration-fast: 150ms; /* Quick interactions */
--duration-normal: 300ms; /* Standard transitions */
--duration-slow: 500ms; /* Emphasis transitions */
--duration-slower: 800ms; /* Page transitions */
```

### Easing Functions

```css
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.36, 0.66, 0.04, 1);
```

### Underwater Effects

#### Ripple Animation

```css
@keyframes ripple-expand {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

.ripple-effect {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(6, 182, 212, 0.8);
  border-radius: 50%;
  animation: ripple-expand 1s ease-out forwards;
}
```

#### Wave Animation

```css
@keyframes wave-flow {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.wave-element {
  animation: wave-flow 3s ease-in-out infinite;
}
```

#### Bubble Float

```css
@keyframes bubble-rise {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-100vh) scale(0.3);
    opacity: 0;
  }
}

.bubble {
  animation: bubble-rise 12s ease-in-out infinite;
}
```

#### Caustic Light Effect

```css
@keyframes caustic-dance {
  0%,
  100% {
    transform: translateX(0) translateY(0) scale(1);
    opacity: 0.8;
  }
  25% {
    transform: translateX(15px) translateY(-10px) scale(1.1);
    opacity: 1;
  }
  50% {
    transform: translateX(-10px) translateY(15px) scale(0.9);
    opacity: 0.9;
  }
  75% {
    transform: translateX(-15px) translateY(-12px) scale(1.05);
    opacity: 1;
  }
}

.caustic-effect {
  animation: caustic-dance 25s ease-in-out infinite;
}
```

## Component Library Specifications

### Buttons

#### Primary Button

```css
.btn-primary {
  padding: var(--space-3) var(--space-6);
  background: linear-gradient(135deg, #088395, #06b6d4);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: var(--font-semibold);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
  box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
  position: relative;
  overflow: hidden;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(6, 182, 212, 0.5);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 10px rgba(6, 182, 212, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
```

#### Secondary Button

```css
.btn-secondary {
  padding: var(--space-3) var(--space-6);
  background: transparent;
  color: var(--surface-accent);
  border: 2px solid var(--surface-accent);
  border-radius: 0.5rem;
  font-weight: var(--font-semibold);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
}

.btn-secondary:hover {
  background: rgba(6, 182, 212, 0.1);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
}
```

#### Button Sizes

```css
.btn-sm {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
}

.btn-md {
  padding: var(--space-3) var(--space-6);
  font-size: var(--text-base);
}

.btn-lg {
  padding: var(--space-4) var(--space-8);
  font-size: var(--text-lg);
}
```

### Form Elements

#### Input Fields

```css
.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: rgba(15, 23, 42, 0.6);
  border: 2px solid rgba(8, 131, 149, 0.3);
  border-radius: 0.5rem;
  color: var(--neutral-100);
  font-size: var(--text-base);
  transition: all var(--duration-normal) var(--ease-out);
}

.form-input::placeholder {
  color: var(--neutral-500);
}

.form-input:focus {
  outline: none;
  border-color: var(--surface-accent);
  background: rgba(15, 23, 42, 0.8);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
}

.form-input:invalid {
  border-color: var(--status-critical);
}
```

#### Floating Labels

```css
.floating-label-group {
  position: relative;
}

.floating-label {
  position: absolute;
  top: var(--space-3);
  left: var(--space-4);
  color: var(--neutral-500);
  pointer-events: none;
  transition: all var(--duration-normal) var(--ease-out);
  background: linear-gradient(to bottom, transparent 50%, rgba(15, 23, 42, 0.95) 50%);
  padding: 0 var(--space-1);
}

.form-input:focus ~ .floating-label,
.form-input:valid ~ .floating-label {
  top: -0.5rem;
  left: var(--space-3);
  font-size: var(--text-sm);
  color: var(--surface-accent);
}
```

### Cards

#### Base Card

```css
.card {
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(8, 131, 149, 0.2);
  border-radius: 1rem;
  padding: var(--space-6);
  transition: all var(--duration-normal) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(6, 182, 212, 0.2);
  border-color: rgba(6, 182, 212, 0.4);
}
```

#### Card with Shimmer Effect

```css
.card-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left var(--duration-slow);
}

.card:hover .card-shimmer {
  left: 100%;
}
```

### Navigation

#### Top Navigation

```css
.top-navigation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 70px;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(8, 131, 149, 0.2);
  padding: 0 var(--space-4);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: 0.5rem;
  text-decoration: none;
  color: var(--neutral-300);
  font-weight: var(--font-medium);
  transition: all var(--duration-normal) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.nav-link::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(8, 131, 149, 0.2), transparent);
  transition: left var(--duration-slow) var(--ease-out);
}

.nav-link:hover::before {
  left: 100%;
}

.nav-link:hover {
  color: var(--surface-accent);
  background: rgba(8, 131, 149, 0.1);
  transform: translateY(-1px);
}

.nav-link.active {
  color: var(--surface-accent);
  background: rgba(8, 131, 149, 0.2);
  box-shadow: 0 0 10px rgba(8, 131, 149, 0.3);
}
```

### Loading States

#### Aqua Spinner

```css
.aqua-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-ripple {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid rgba(8, 131, 149, 0.6);
  border-radius: 50%;
  animation: ripple-animation 2s infinite ease-out;
}

.spinner-ripple:nth-child(2) {
  animation-delay: 0.5s;
}

.spinner-ripple:nth-child(3) {
  animation-delay: 1s;
}

.spinner-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 25%;
  height: 25%;
  background: linear-gradient(135deg, #0891b2, #0e7490);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: pulse-animation 2s infinite ease-in-out;
  box-shadow: 0 0 10px rgba(8, 131, 149, 0.5);
}

@keyframes ripple-animation {
  0% {
    transform: scale(0.1);
    opacity: 1;
    border-color: rgba(8, 131, 149, 0.8);
  }
  50% {
    opacity: 0.6;
    border-color: rgba(8, 131, 149, 0.4);
  }
  100% {
    transform: scale(1);
    opacity: 0;
    border-color: rgba(8, 131, 149, 0.1);
  }
}

@keyframes pulse-animation {
  0%,
  100% {
    transform: translate(-50%, -50%) scale(1);
    box-shadow: 0 0 10px rgba(8, 131, 149, 0.5);
  }
  50% {
    transform: translate(-50%, -50%) scale(1.2);
    box-shadow: 0 0 20px rgba(8, 131, 149, 0.8);
  }
}
```

### Modals and Overlays

#### Modal Base

```css
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: overlay-enter var(--duration-normal) var(--ease-out);
}

.modal-content {
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(8, 131, 149, 0.3);
  border-radius: 1.5rem;
  padding: var(--space-8);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 30px rgba(8, 131, 149, 0.2);
  animation: modal-enter var(--duration-normal) var(--ease-bounce);
}

@keyframes overlay-enter {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes modal-enter {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
```

## Responsive Design System

### Breakpoints

```css
--breakpoint-sm: 640px; /* Small devices */
--breakpoint-md: 768px; /* Medium devices */
--breakpoint-lg: 1024px; /* Large devices */
--breakpoint-xl: 1280px; /* Extra large devices */
--breakpoint-2xl: 1536px; /* 2X large devices */
```

### Responsive Utilities

```css
/* Mobile First Approach */
.container {
  width: 100%;
  padding: 0 var(--space-4);
}

@media (min-width: 640px) {
  .container {
    max-width: 640px;
    margin: 0 auto;
    padding: 0 var(--space-6);
  }
}

@media (min-width: 768px) {
  .container {
    max-width: 768px;
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
    padding: 0 var(--space-8);
  }
}

@media (min-width: 1280px) {
  .container {
    max-width: 1280px;
  }
}
```

### Touch-Friendly Interactions

```css
/* Minimum 44px touch targets */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Larger tap areas on mobile */
@media (max-width: 768px) {
  .btn {
    min-height: 48px;
    padding: var(--space-4) var(--space-6);
  }

  .nav-link {
    min-height: 48px;
    padding: var(--space-3) var(--space-4);
  }
}
```

## Accessibility Guidelines

### Color Contrast

All color combinations must meet WCAG 2.1 AA standards:

- Normal text: 4.5:1 contrast ratio minimum
- Large text (18pt+): 3:1 contrast ratio minimum
- Interactive elements: 3:1 contrast ratio minimum

### Focus States

```css
.focusable:focus {
  outline: 2px solid var(--surface-accent);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.2);
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .focusable:focus {
    outline: 3px solid var(--glow-cyan);
    outline-offset: 3px;
  }
}
```

### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  .underwater-effect {
    animation: none !important;
    opacity: 0.3;
  }
}
```

### Screen Reader Support

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

## Implementation Guidelines

### CSS Custom Properties Usage

Always use CSS custom properties for consistent theming:

```css
/* Good */
.component {
  color: var(--neutral-100);
  background: var(--deep-black);
  padding: var(--space-4);
}

/* Avoid */
.component {
  color: #f1f5f9;
  background: #001f2e;
  padding: 1rem;
}
```

### Component Composition

Build components using composition patterns:

```css
/* Base component */
.btn-base {
  padding: var(--space-3) var(--space-6);
  border: none;
  border-radius: 0.5rem;
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
}

/* Variant modifiers */
.btn-primary {
  background: linear-gradient(135deg, #088395, #06b6d4);
  color: white;
  box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
}

.btn-secondary {
  background: transparent;
  color: var(--surface-accent);
  border: 2px solid var(--surface-accent);
}
```

### Performance Considerations

#### Hardware Acceleration

Use `transform` and `opacity` for animations:

```css
/* Good - GPU accelerated */
.animated-element {
  transform: translateY(0);
  opacity: 1;
  transition:
    transform var(--duration-normal),
    opacity var(--duration-normal);
}

.animated-element:hover {
  transform: translateY(-2px);
}

/* Avoid - CPU intensive */
.animated-element:hover {
  top: -2px;
}
```

#### Will-Change Property

Use `will-change` for elements that will be animated:

```css
.will-animate {
  will-change: transform, opacity;
}

/* Remove after animation */
.animation-complete {
  will-change: auto;
}
```

## Quality Assurance

### Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Testing Checklist

- [ ] All colors meet WCAG 2.1 AA contrast requirements
- [ ] Components work with keyboard navigation
- [ ] Screen readers can access all content
- [ ] Animations respect `prefers-reduced-motion`
- [ ] Touch targets are minimum 44px
- [ ] Components work across all supported browsers
- [ ] Responsive behavior works on all breakpoints
- [ ] Performance budget maintained (< 100ms interaction response)

### Validation Tools

- WebAIM Contrast Checker
- axe-core accessibility testing
- Lighthouse accessibility audit
- Manual keyboard navigation testing
- Screen reader testing (NVDA, JAWS, VoiceOver)

## Maintenance and Updates

### Version Control

- Document all changes in this style guide
- Maintain backward compatibility when possible
- Provide migration guides for breaking changes
- Use semantic versioning for style guide releases

### Component Documentation

Each component should include:

- Visual examples of all states
- Code implementation examples
- Accessibility requirements
- Usage guidelines and best practices
- Do's and don'ts

This style guide serves as the single source of truth for AquaChain's visual design system, ensuring consistency, accessibility, and maintainability across all user interfaces.
