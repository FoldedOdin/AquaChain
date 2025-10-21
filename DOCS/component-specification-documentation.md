# AquaChain Component Specification Documentation

## Overview

This document provides comprehensive specifications for all UI components in the AquaChain system. Each component is documented with its current implementation status, design specifications, interaction states, responsive behavior, accessibility requirements, and implementation guidelines.

## Component Categories

### 1. Form Components
### 2. Navigation Components  
### 3. Data Display Components
### 4. Feedback Components
### 5. Layout Components
### 6. Interactive Components

---

## 1. Form Components

### 1.1 FloatingInput

**Current Implementation Status**: ✅ Fully Implemented
**Location**: `frontend/src/components/shared/auth-modal/FloatingInput.jsx`

#### Component Specification

**Purpose**: Floating label input field with aqua-themed styling and validation states

**Visual Design**:
- Base padding: `16px` (top/bottom) `16px` (left/right)
- Border radius: `8px`
- Minimum height: `48px` for touch accessibility
- Font size: `16px` (prevents zoom on iOS)

**Interaction States**:

| State | Border Color | Background | Label Position | Shadow |
|-------|-------------|------------|----------------|---------|
| Default | `#D1D5DB` | `white` | Inline | Base shadow |
| Focus | `#06B6D4` | `white` | Floating (-24px) | Cyan glow |
| Error | `#EF4444` | `white` | Floating | Red glow |
| Success | `#10B981` | `white` | Floating | Green indicator |
| Disabled | `#D1D5DB` | `#F9FAFB` | Static | None |

**Responsive Behavior**:
- Mobile: Font size locked to 16px to prevent zoom
- Touch targets: Minimum 48px height
- Label scaling: 0.875x when floating

**Accessibility Requirements**:
- ARIA attributes: `aria-invalid`, `aria-describedby`
- Required indicator: Visual asterisk with semantic markup
- Error association: Proper `id` and `aria-describedby` linking
- Keyboard navigation: Full tab order support

**Animation Specifications**:
- Label float duration: `300ms`
- Easing: `back.out(1.7)` for label, `power2.out` for focus
- GPU acceleration: `force3D: true` for all transforms
- Performance optimization: `will-change` management

**Implementation Guidelines**:
```jsx
<FloatingInput
  type="email"
  name="email"
  value={value}
  onChange={handleChange}
  label="Email Address"
  error={errors.email}
  required
  autoComplete="email"
  showValidation={true}
  isValid={isEmailValid}
/>
```

**Code Example**:
```css
.floating-input {
  position: relative;
  width: 100%;
}

.floating-input input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--neutral-300);
  border-radius: 8px;
  font-size: 16px;
  min-height: 48px;
  transition: all 300ms ease;
}

.floating-input input:focus {
  border-color: var(--surface-accent);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

.floating-input label {
  position: absolute;
  left: 16px;
  top: 12px;
  transition: all 300ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
  pointer-events: none;
}

.floating-input.has-value label,
.floating-input.is-focused label {
  transform: translateY(-24px) scale(0.875);
  color: var(--surface-accent);
}
```

### 1.2 Button Components

**Current Implementation Status**: ✅ Implemented (Multiple variants)
**Location**: Various components (LoginForm, SignupForm, etc.)

#### Primary Button Specification

**Visual Design**:
- Background: `linear-gradient(135deg, #088395, #06B6D4)`
- Padding: `12px 24px`
- Border radius: `8px`
- Font weight: `600` (semibold)
- Minimum height: `48px`

**Interaction States**:

| State | Transform | Shadow | Background |
|-------|-----------|---------|------------|
| Default | `scale(1)` | Cyan glow (medium) | Primary gradient |
| Hover | `translateY(-2px)` | Cyan glow (large) | Enhanced gradient |
| Active | `scale(0.98)` | Cyan glow (small) | Darker gradient |
| Loading | `scale(1)` | Cyan glow (medium) | Muted gradient |
| Disabled | `scale(1)` | None | Gray |

**Animation Specifications**:
- Hover transition: `200ms ease-out`
- Press animation: `100ms ease-in`
- Ripple effect: `600ms power2.out`
- Loading spinner: Dual-ring with reverse rotation

**Responsive Behavior**:
- Mobile: Increased padding (`16px 24px`)
- Touch targets: Minimum 48px height maintained
- Text scaling: Responsive font sizes

**Accessibility Requirements**:
- Focus ring: 2px solid cyan with 2px offset
- Loading state: `aria-describedby` for status
- Disabled state: `aria-disabled="true"`
- High contrast: Enhanced outline in high contrast mode

**Implementation Guidelines**:
```jsx
<button
  className="btn-primary"
  onClick={handleClick}
  disabled={isLoading}
  aria-describedby={isLoading ? "loading-status" : undefined}
>
  {isLoading ? (
    <>
      <LoadingSpinner size="small" />
      <span id="loading-status">Processing...</span>
    </>
  ) : (
    'Submit'
  )}
</button>
```

#### Secondary Button Specification

**Visual Design**:
- Background: `transparent`
- Border: `2px solid #06B6D4`
- Color: `#06B6D4`
- Same padding and sizing as primary

**Interaction States**:
- Hover: Background `rgba(6, 182, 212, 0.1)` with glow
- Active: Background `rgba(6, 182, 212, 0.2)`
- Focus: Same focus ring as primary

### 1.3 TabNavigation

**Current Implementation Status**: ✅ Fully Implemented
**Location**: `frontend/src/components/shared/auth-modal/TabNavigation.jsx`

#### Component Specification

**Purpose**: Animated tab switching with aqua theme and accessibility support

**Visual Design**:
- Container: Rounded background with padding
- Indicator: Animated white background that slides
- Tabs: Equal width with centered text

**Animation Specifications**:
- Indicator movement: `400ms power2.out`
- Tab glow effect: `300ms power2.out`
- Ripple on click: `600ms power2.out`

**Accessibility Requirements**:
- ARIA roles: `tablist`, `tab`, `tabpanel`
- Keyboard navigation: Arrow keys, Enter, Space
- Focus management: Proper tab index handling
- Screen reader: Proper announcements

**Responsive Behavior**:
- Mobile: Adjusted padding and font sizes
- Touch targets: 44px minimum height

---

## 2. Navigation Components

### 2.1 TopNavigation

**Current Implementation Status**: ✅ Fully Implemented
**Location**: `frontend/src/components/navigation/TopNavigation.jsx`

#### Component Specification

**Purpose**: Fixed top navigation with role-based menu items and user actions

**Visual Design**:
- Height: `70px` fixed
- Background: `rgba(15, 23, 42, 0.95)` with backdrop blur
- Border: Bottom border with aqua accent

**Layout Structure**:
1. **Brand Section**: Logo + AquaChain text
2. **Navigation Links**: Role-based menu items
3. **Search Bar**: Expandable search input
4. **Actions**: Notifications + User menu

**Interaction States**:

| Element | Default | Hover | Active |
|---------|---------|-------|--------|
| Nav Links | Gray text | Aqua color + glow | Aqua background |
| Brand | Gradient text | Enhanced glow | - |
| User Avatar | Aqua gradient | Background highlight | - |
| Search | Semi-transparent | Enhanced background | Focus ring |

**Animation Specifications**:
- Link hover: Shimmer effect (`500ms ease`)
- Dropdown enter: Scale + fade (`200ms ease-out`)
- Brand pulse: Water drop glow (`2s infinite`)

**Responsive Behavior**:
- Desktop: Full navigation visible
- Tablet: Condensed search, icon-only links
- Mobile: Hidden (replaced by mobile navigation)

**Accessibility Requirements**:
- Landmark: `<nav>` with `aria-label`
- Dropdown menus: Proper ARIA states
- Keyboard navigation: Tab order and escape handling
- Screen reader: Menu state announcements

**Implementation Guidelines**:
```jsx
<nav className="top-navigation" aria-label="Main navigation">
  <div className="nav-container">
    <div className="nav-brand">
      <Link to="/" className="brand-link">
        <div className="brand-icon">
          <div className="water-drop"></div>
        </div>
        <span className="brand-text">AquaChain</span>
      </Link>
    </div>
    
    <div className="nav-links">
      {navigationItems.map(item => (
        <Link
          key={item.path}
          to={item.path}
          className={`nav-link ${isActive ? 'active' : ''}`}
          aria-current={isActive ? 'page' : undefined}
        >
          <Icon size={18} />
          <span>{item.label}</span>
        </Link>
      ))}
    </div>
    
    {/* Search and Actions */}
  </div>
</nav>
```

### 2.2 BreadcrumbNavigation

**Current Implementation Status**: ✅ Fully Implemented
**Location**: `frontend/src/components/navigation/BreadcrumbNavigation.jsx`

#### Component Specification

**Purpose**: Hierarchical navigation with underwater theming

**Visual Design**:
- Sticky positioning below top nav
- Background: Semi-transparent with blur
- Separators: Aqua-themed chevrons

**Animation Specifications**:
- Item entrance: `300ms ease-out` slide-in
- Hover shimmer: `400ms ease` sweep effect
- Current item glow: `2s infinite` pulse

**Accessibility Requirements**:
- Landmark: `<nav aria-label="Breadcrumb">`
- List structure: Proper `<ol>` with `<li>`
- Current page: `aria-current="page"`

### 2.3 MobileNavigation

**Current Implementation Status**: ✅ Implemented
**Location**: `frontend/src/components/navigation/MobileNavigation.jsx`

#### Component Specification

**Purpose**: Mobile-optimized navigation with bottom placement

**Visual Design**:
- Position: Fixed bottom
- Background: Semi-transparent with blur
- Icons: Large touch-friendly targets

**Responsive Behavior**:
- Visible: Mobile and tablet only
- Hidden: Desktop breakpoints
- Safe area: iOS safe area insets

---

## 3. Data Display Components

### 3.1 StatusIndicator

**Current Implementation Status**: ✅ Fully Implemented
**Location**: `frontend/src/components/consumer/StatusIndicator.jsx`

#### Component Specification

**Purpose**: Large visual indicator for water quality status with clear feedback

**Visual Design**:
- Large card format with gradient backgrounds
- Status-specific color schemes
- Prominent icons and typography

**Status Variants**:

| Status | Background | Icon | Border | Actions |
|--------|------------|------|--------|---------|
| Safe | Green gradient | ✓ | Green | Quality details |
| Warning | Yellow gradient | ⚠️ | Yellow | Recommended actions |
| Critical | Red gradient | 🚨 | Red | Immediate actions |
| Loading | Gray gradient | ⏳ | Gray | Loading state |

**Animation Specifications**:
- Status transitions: `300ms ease-in-out`
- Pulse effect: `2s infinite` for active states
- Hover scale: `1.02` transform
- Loading overlay: Backdrop blur with spinner

**Responsive Behavior**:
- Mobile: Adjusted padding and font sizes
- Tablet: Optimized layout for medium screens
- Desktop: Full-size display with hover effects

**Accessibility Requirements**:
- Status announcements: `aria-live="polite"`
- Color independence: Icons and text convey status
- High contrast: Enhanced visibility modes
- Screen reader: Descriptive status text

**Implementation Guidelines**:
```jsx
<StatusIndicator
  status={{
    wqi: 85,
    category: 'excellent',
    trend: 'improving',
    lastUpdated: new Date()
  }}
  isLoading={false}
/>
```

### 3.2 LoadingSpinner

**Current Implementation Status**: ✅ Fully Implemented
**Location**: `frontend/src/components/shared/LoadingSpinner.jsx`

#### Component Specification

**Purpose**: Aquatic-themed loading indicator with multiple sizes

**Visual Design**:
- Concentric ripple rings
- Central pulsing dot
- Bubble effects around spinner
- Caustic light shimmer

**Size Variants**:
- Small: `24px` (w-6 h-6)
- Medium: `48px` (w-12 h-12)
- Large: `64px` (w-16 h-16)

**Animation Specifications**:
- Ripple expansion: `2s infinite ease-out`
- Center pulse: `2s infinite ease-in-out`
- Bubble float: `4s infinite ease-in-out`
- Caustic shimmer: `3s infinite ease-in-out`

**Accessibility Requirements**:
- Reduced motion: Static state with opacity
- Screen reader: Loading message
- ARIA: `role="status"` with `aria-label`

---

## 4. Feedback Components

### 4.1 Modal Components

**Current Implementation Status**: ✅ Implemented (AuthModal)
**Location**: `frontend/src/components/shared/auth-modal/`

#### ModalContainer Specification

**Purpose**: Base modal container with backdrop and positioning

**Visual Design**:
- Backdrop: Semi-transparent with blur
- Container: Centered with responsive sizing
- Background: Dark aqua with border glow

**Animation Specifications**:
- Backdrop fade: `200ms ease-out`
- Modal scale: `300ms cubic-bezier(0.175, 0.885, 0.32, 1.275)`
- Exit animation: `200ms ease-in`

**Accessibility Requirements**:
- Focus trap: Keyboard navigation contained
- Escape key: Close modal functionality
- ARIA: `role="dialog"` with proper labeling
- Focus management: Return focus on close

#### ModalOverlay Specification

**Visual Design**:
- Background: `rgba(0, 0, 0, 0.5)` with backdrop blur
- Z-index: `1000` (modal layer)
- Click outside: Close modal behavior

### 4.2 Alert/Notification Components

**Current Implementation Status**: ⚙️ Partially Implemented
**Location**: Various components (inline alerts)

#### Component Specification

**Purpose**: System feedback for user actions and status updates

**Variant Types**:
- Success: Green theme with checkmark
- Warning: Yellow theme with warning icon
- Error: Red theme with error icon
- Info: Blue theme with info icon

**Visual Design**:
- Padding: `12px 16px`
- Border radius: `8px`
- Border: Left accent border (4px)
- Background: Semi-transparent color overlay

**Animation Specifications**:
- Enter: Slide down + fade (`300ms ease-out`)
- Exit: Slide up + fade (`200ms ease-in`)
- Auto-dismiss: 5 second timer for non-critical alerts

---

## 5. Layout Components

### 5.1 Container Components

**Current Implementation Status**: ✅ Implemented (Various)
**Location**: Multiple layout components

#### Responsive Container Specification

**Purpose**: Consistent content width and padding across breakpoints

**Breakpoint Behavior**:
- Mobile: `100%` width, `16px` padding
- Tablet: `768px` max-width, `24px` padding
- Desktop: `1024px` max-width, `32px` padding
- Wide: `1280px` max-width, `48px` padding

**Implementation Guidelines**:
```css
.container {
  width: 100%;
  margin: 0 auto;
  padding: 0 1rem;
}

@media (min-width: 640px) {
  .container {
    max-width: 640px;
    padding: 0 1.5rem;
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
    padding: 0 2rem;
  }
}
```

### 5.2 Card Components

**Current Implementation Status**: ✅ Implemented (Various)
**Location**: Dashboard and display components

#### Base Card Specification

**Visual Design**:
- Background: `rgba(15, 23, 42, 0.8)` with backdrop blur
- Border: `1px solid rgba(8, 131, 149, 0.2)`
- Border radius: `16px`
- Padding: `24px`

**Interaction States**:
- Hover: `translateY(-5px)` with enhanced shadow
- Focus: Aqua focus ring
- Active: Slight scale reduction

**Animation Specifications**:
- Hover transition: `300ms ease-out`
- Shimmer effect: `500ms ease` sweep on hover

---

## 6. Interactive Components

### 6.1 Dropdown Components

**Current Implementation Status**: ✅ Implemented (Navigation dropdowns)
**Location**: `frontend/src/components/navigation/TopNavigation.jsx`

#### Dropdown Menu Specification

**Purpose**: Contextual menus for user actions and navigation

**Visual Design**:
- Background: `rgba(15, 23, 42, 0.95)` with backdrop blur
- Border: Aqua accent with glow shadow
- Border radius: `12px`
- Min width: `280px`

**Animation Specifications**:
- Enter: Scale + fade (`200ms ease-out`)
- Exit: Scale + fade (`150ms ease-in`)
- Item hover: Background highlight

**Accessibility Requirements**:
- ARIA: `role="menu"` with `menuitem` children
- Keyboard: Arrow navigation, Enter/Space selection
- Focus management: Proper focus handling
- Escape: Close dropdown

### 6.2 Search Components

**Current Implementation Status**: ✅ Implemented (TopNavigation)
**Location**: `frontend/src/components/navigation/TopNavigation.jsx`

#### Search Input Specification

**Purpose**: Global search functionality with aqua theming

**Visual Design**:
- Background: Semi-transparent dark
- Border: Aqua accent on focus
- Icon: Left-aligned search icon
- Placeholder: Contextual search hints

**Interaction States**:
- Focus: Enhanced background + glow
- Typing: Real-time search suggestions
- Results: Dropdown with highlighted matches

---

## Implementation Standards

### Code Quality Requirements

1. **TypeScript**: All new components must use TypeScript
2. **PropTypes**: Runtime type checking for JavaScript components
3. **Accessibility**: WCAG 2.1 AA compliance mandatory
4. **Performance**: Lazy loading and code splitting
5. **Testing**: Unit tests for all interactive components

### Design Token Usage

All components must use design tokens from the token system:

```jsx
// Good
const Button = styled.button`
  padding: var(--space-3) var(--space-6);
  background: var(--brand-primary);
  color: var(--neutral-100);
  border-radius: var(--radius-md);
`;

// Avoid
const Button = styled.button`
  padding: 12px 24px;
  background: #088395;
  color: #F1F5F9;
  border-radius: 6px;
`;
```

### Animation Guidelines

1. **Performance**: Use `transform` and `opacity` for animations
2. **Easing**: Use design system easing functions
3. **Duration**: Follow duration scale (150ms, 300ms, 500ms)
4. **Reduced Motion**: Respect `prefers-reduced-motion`
5. **GPU Acceleration**: Use `will-change` appropriately

### Responsive Design Principles

1. **Mobile First**: Design for mobile, enhance for desktop
2. **Touch Targets**: Minimum 44px for interactive elements
3. **Breakpoints**: Use system breakpoints consistently
4. **Content Priority**: Show most important content first
5. **Performance**: Optimize for mobile networks

### Accessibility Checklist

- [ ] Keyboard navigation works for all interactive elements
- [ ] Focus indicators are visible and meet contrast requirements
- [ ] Screen readers can access all content and functionality
- [ ] Color is not the only way to convey information
- [ ] Text meets contrast ratio requirements (4.5:1 for normal, 3:1 for large)
- [ ] Interactive elements have appropriate ARIA labels
- [ ] Form fields have associated labels
- [ ] Error messages are properly associated with form fields
- [ ] Loading states are announced to screen readers
- [ ] Modal dialogs trap focus and return focus on close

## Testing Requirements

### Unit Testing
- Component rendering
- Props handling
- Event handling
- State management
- Error boundaries

### Integration Testing
- Component interactions
- Form submissions
- Navigation flows
- API integrations
- User workflows

### Accessibility Testing
- Automated testing with axe-core
- Manual keyboard navigation
- Screen reader testing
- Color contrast validation
- Focus management verification

### Visual Regression Testing
- Component screenshots
- Responsive layouts
- Animation states
- Theme variations
- Browser compatibility

## Maintenance Guidelines

### Version Control
- Semantic versioning for component library
- Changelog for all component updates
- Migration guides for breaking changes
- Deprecation notices with timelines

### Documentation Updates
- Update specifications when components change
- Maintain code examples and usage guidelines
- Document known issues and workarounds
- Keep accessibility requirements current

### Performance Monitoring
- Bundle size tracking
- Runtime performance metrics
- Animation performance profiling
- Memory usage monitoring
- User experience metrics

This component specification documentation serves as the definitive guide for implementing, maintaining, and extending AquaChain's UI component library while ensuring consistency, accessibility, and performance across all user interfaces.