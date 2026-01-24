# AquaChain Landing Page Hero Section

## Overview

This directory contains the implementation of the AquaChain Landing Page Hero Section with immersive underwater animations, as specified in task 3 of the implementation plan.

## Components

### HeroSection.tsx
Main hero section component that orchestrates all the hero elements:
- Full-viewport height layout with centered content
- Responsive typography and call-to-action buttons
- Trust indicators showing system metrics
- Proper semantic HTML structure and accessibility
- Integration with all animation components

### AnimatedLogo.tsx
Animated AquaChain logo component featuring:
- Floating droplet icon with pulsing and floating animations
- Responsive scaling for different screen sizes
- Proper alt text and accessibility attributes
- Reduced motion support for accessibility preferences
- Floating particles and glow effects

### TypewriterText.tsx
Typewriter effect component for the main tagline:
- Configurable typing speed and delay options
- Blinking cursor effect with smooth transitions
- Reduced motion support (shows full text immediately)
- Responsive text breaking for mobile devices
- Screen reader accessibility with hidden complete text

### UnderwaterBackground.tsx
Immersive underwater background animation system:
- Animated background layers with CSS gradients
- Physics-based floating bubble system (15 bubbles max)
- Water caustics animation with light ray effects
- 60fps performance optimization with requestAnimationFrame
- Reduced motion support (static background)
- GPU acceleration and object pooling for performance

## Features

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatibility
- Reduced motion preference support
- Proper ARIA labels and semantic HTML

### Performance
- Optimized for 60fps animations
- GPU acceleration with transform3d
- Object pooling for bubble effects
- Responsive bubble count (fewer on mobile)
- Lazy animation initialization

### Responsive Design
- Mobile-first approach
- Breakpoints: mobile (320px+), tablet (768px+), desktop (1024px+)
- Responsive typography scaling
- Touch-optimized interactions
- Adaptive animation complexity

## Animation Details

### Bubble System
- Maximum 15 bubbles on desktop, 8 on mobile
- Physics-based movement with drift and speed variation
- Automatic recycling when bubbles exit viewport
- Smooth opacity transitions

### Caustics Effect
- Multiple overlapping radial gradients
- Staggered animation timing for natural effect
- GPU-accelerated transforms

### Logo Animation
- Gentle floating motion (4s duration)
- Pulsing glow rings with different timing
- Floating particles around the logo
- SVG-based droplet with gradient fills

### Typewriter Effect
- Configurable typing speed (default 100ms per character)
- Natural line breaking for mobile
- Blinking cursor with 530ms interval
- Smooth transitions

## Usage

```tsx
import HeroSection from './components/LandingPage/HeroSection';

<HeroSection 
  onGetStartedClick={() => openAuthModal()}
  onViewDashboardsClick={() => navigateToDemo()}
/>
```

## Testing

The hero section includes comprehensive tests in `__tests__/HeroSection.test.tsx`:
- Component rendering and content verification
- Semantic HTML structure validation
- Button click functionality
- Accessibility compliance

## Requirements Fulfilled

This implementation fulfills the following requirements from the specification:
- **1.1**: Landing page displays hero section with animated visuals and tagline
- **1.2**: Clear value propositions and call-to-action buttons
- **5.3**: Proper semantic HTML structure for accessibility
- **6.1**: Immersive animations including floating bubbles and water caustics
- **6.2**: Interactive ripple effects and smooth animations
- **6.4**: 60fps animation performance on modern devices
- **12.2**: Consistent AquaChain branding and typography