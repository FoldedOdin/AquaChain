import React from 'react';
import { render, screen } from '@testing-library/react';
import HeroSection from '../HeroSection';

// Mock the child components to avoid complex animation testing
jest.mock('../AnimatedLogo', () => {
  return function MockAnimatedLogo() {
    return <div data-testid="animated-logo">AquaChain Logo</div>;
  };
});

jest.mock('../TypewriterText', () => {
  return function MockTypewriterText({ text }: { text: string }) {
    return <div data-testid="typewriter-text">{text}</div>;
  };
});

jest.mock('../UnderwaterBackground', () => {
  return function MockUnderwaterBackground() {
    return <div data-testid="underwater-background">Background</div>;
  };
});

describe('HeroSection', () => {
  const mockOnGetStartedClick = jest.fn();
  const mockOnViewDashboardsClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render hero section with correct content', () => {
    render(
      <HeroSection
        onGetStartedClick={mockOnGetStartedClick}
        onViewDashboardsClick={mockOnViewDashboardsClick}
      />
    );

    // Check for main components
    expect(screen.getByTestId('animated-logo')).toBeInTheDocument();
    expect(screen.getByTestId('typewriter-text')).toBeInTheDocument();
    expect(screen.getByTestId('underwater-background')).toBeInTheDocument();

    // Check for call-to-action buttons
    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /view demo/i })).toBeInTheDocument();

    // Check for trust indicators
    expect(screen.getByText('99.8%')).toBeInTheDocument();
    expect(screen.getByText('System Uptime')).toBeInTheDocument();
    expect(screen.getByText('<30s')).toBeInTheDocument();
    expect(screen.getByText('Alert Response')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('Tamper-Evident')).toBeInTheDocument();
  });

  it('should have proper semantic HTML structure', () => {
    render(
      <HeroSection
        onGetStartedClick={mockOnGetStartedClick}
        onViewDashboardsClick={mockOnViewDashboardsClick}
      />
    );

    // Check for semantic elements
    const heroSection = screen.getByRole('banner');
    expect(heroSection).toHaveAttribute('aria-label', 'AquaChain Hero Section');
    expect(heroSection).toHaveAttribute('id', 'hero');
  });

  it('should call callback functions when buttons are clicked', () => {
    render(
      <HeroSection
        onGetStartedClick={mockOnGetStartedClick}
        onViewDashboardsClick={mockOnViewDashboardsClick}
      />
    );

    const getStartedButton = screen.getByRole('button', { name: /get started/i });
    const viewDemoButton = screen.getByRole('button', { name: /view demo/i });

    getStartedButton.click();
    expect(mockOnGetStartedClick).toHaveBeenCalledTimes(1);

    viewDemoButton.click();
    expect(mockOnViewDashboardsClick).toHaveBeenCalledTimes(1);
  });
});