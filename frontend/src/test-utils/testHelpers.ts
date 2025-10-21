/**
 * Test utilities and helpers
 */

import { jest } from '@jest/globals';

// Mock props for LandingPage component
export const mockLandingPageProps = {
  onViewDashboardsClick: jest.fn(),
};

// Mock userEvent setup for older versions
export const mockUserEvent = {
  setup: () => ({
    click: jest.fn(),
    type: jest.fn(),
    keyboard: jest.fn(),
    tab: jest.fn(),
  }),
};

// Environment variable helper for tests
export const setTestEnv = (env: string) => {
  const originalEnv = process.env.NODE_ENV;
  Object.defineProperty(process.env, 'NODE_ENV', {
    value: env,
    writable: true,
    configurable: true,
  });
  return () => {
    Object.defineProperty(process.env, 'NODE_ENV', {
      value: originalEnv,
      writable: true,
      configurable: true,
    });
  };
};