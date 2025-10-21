# Testing Guide for AquaChain Landing Page

This document outlines the testing framework and tools set up for the AquaChain Landing Page project.

## Testing Stack

### Core Testing Tools

- **Jest**: JavaScript testing framework with built-in assertion library
- **React Testing Library**: Testing utilities for React components
- **jest-axe**: Accessibility testing integration for Jest
- **@axe-core/react**: Runtime accessibility testing
- **web-vitals**: Performance monitoring and Core Web Vitals tracking

### Development Tools

- **Storybook**: Component development and documentation
- **@storybook/addon-a11y**: Accessibility testing in Storybook
- **@storybook/addon-docs**: Automated documentation generation
- **ESLint**: Code linting with accessibility rules
- **Prettier**: Code formatting

## Available Scripts

### Testing Scripts

```bash
# Run all tests in watch mode
npm test

# Run tests once with coverage report
npm run test:ci

# Run accessibility tests only
npm run test:a11y-dev

# Run performance tests only
npm run test:performance

# Generate coverage report
npm run test:coverage

# Build and run accessibility audit on built app
npm run test:a11y
```

### Storybook Scripts

```bash
# Start Storybook development server
npm run storybook

# Build Storybook for production
npm run build-storybook

# Run Storybook tests (if configured)
npm run storybook:test
```

## Testing Utilities

### Accessibility Testing

The project includes comprehensive accessibility testing utilities:

```typescript
import { testComponentAccessibility, testKeyboardNavigation } from '../utils/accessibility';

// Test component for accessibility violations
await testComponentAccessibility(container);

// Test keyboard navigation
testKeyboardNavigation(container);
```

### Performance Testing

Performance monitoring is integrated with web-vitals:

```typescript
import { performanceMonitor, usePerformanceMetrics } from '../utils/performance';

// Get current performance metrics
const metrics = performanceMonitor.getMetrics();

// Use in React components
const { metrics, score } = usePerformanceMetrics();
```

## Writing Tests

### Component Tests

```typescript
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { testComponentAccessibility } from '../utils/accessibility';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('should be accessible', async () => {
    const { container } = render(<MyComponent />);
    await testComponentAccessibility(container);
  });

  it('should handle user interactions', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    
    render(<MyComponent onClick={handleClick} />);
    
    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### Accessibility Tests

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('should have no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Performance Tests

```typescript
import { PerformanceMonitor } from '../utils/performance';

describe('Performance', () => {
  it('should meet performance thresholds', () => {
    const monitor = new PerformanceMonitor();
    expect(monitor.getRating('lcp', 2000)).toBe('good');
  });
});
```

## Storybook Integration

### Writing Stories

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { MyComponent } from './MyComponent';

const meta: Meta<typeof MyComponent> = {
  title: 'Components/MyComponent',
  component: MyComponent,
  parameters: {
    docs: {
      description: {
        component: 'A description of the component',
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    prop: 'value',
  },
};

export const AccessibilityTest: Story = {
  args: {
    prop: 'value',
  },
  parameters: {
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
        ],
      },
    },
  },
};
```

## Coverage Requirements

The project maintains the following coverage thresholds:

- **Branches**: 70%
- **Functions**: 70%
- **Lines**: 70%
- **Statements**: 70%

## Accessibility Standards

All components must meet:

- **WCAG 2.1 AA** compliance
- **Keyboard navigation** support
- **Screen reader** compatibility
- **Color contrast** requirements
- **Focus management** best practices

## Performance Standards

Components should meet Core Web Vitals thresholds:

- **LCP (Largest Contentful Paint)**: < 2.5s
- **FID (First Input Delay)**: < 100ms
- **CLS (Cumulative Layout Shift)**: < 0.1

## Best Practices

### Test Organization

- Group related tests in `describe` blocks
- Use descriptive test names that explain the expected behavior
- Follow the Arrange-Act-Assert pattern
- Keep tests focused and independent

### Accessibility Testing

- Test with keyboard navigation
- Verify ARIA labels and roles
- Check color contrast
- Test with screen readers (manual testing)
- Use semantic HTML elements

### Performance Testing

- Monitor Core Web Vitals
- Test on various network conditions
- Optimize images and assets
- Use lazy loading where appropriate
- Implement code splitting

### Mocking

- Mock external dependencies
- Use MSW for API mocking
- Mock heavy animations in tests
- Provide fallbacks for browser APIs

## Continuous Integration

The testing setup integrates with CI/CD pipelines:

1. **Unit Tests**: Run on every commit
2. **Accessibility Tests**: Run on pull requests
3. **Performance Tests**: Run on staging deployments
4. **Visual Regression**: Run with Storybook builds

## Troubleshooting

### Common Issues

1. **Tests timing out**: Increase timeout in Jest configuration
2. **Accessibility violations**: Check ARIA labels and semantic HTML
3. **Performance issues**: Use React DevTools Profiler
4. **Flaky tests**: Ensure proper cleanup and mocking

### Debug Commands

```bash
# Run tests with debug output
npm test -- --verbose

# Run specific test file
npm test -- MyComponent.test.tsx

# Run tests with coverage
npm test -- --coverage

# Debug accessibility issues
npm run test:a11y-dev -- --verbose
```

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [jest-axe Documentation](https://github.com/nickcolley/jest-axe)
- [Storybook Documentation](https://storybook.js.org/docs/react/get-started/introduction)
- [Web Vitals](https://web.dev/vitals/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)