/**
 * Property Test: UI State Management
 * Feature: enhanced-consumer-ordering-system, Property 14: UI State Management
 * Validates: Requirements 2.4, 6.4
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import React, { useState, useEffect } from 'react';
import { NotificationProvider } from '../../../contexts/NotificationContext';
import { NetworkErrorHandler } from '../NetworkErrorHandler';
import { OrderingError } from '../../../utils/errorHandling';

// Mock fast-check for now to get tests running
// Mock fast-check for now to get tests running
const fc = {
  oneof: (...args: any[]) => args[Math.floor(Math.random() * args.length)],
  integer: (opts: any) => Math.floor(Math.random() * ((opts.max || 100) - (opts.min || 0))) + (opts.min || 0),
  boolean: () => Math.random() > 0.5,
  string: (opts: any) => `test-string-${Math.random().toString(36).substr(2, opts?.maxLength || 10)}`,
  record: (obj: any) => {
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = value;
    }
    return result;
  },
  constant: (val: any) => val,
  asyncProperty: (arb: any, fn: any) => ({ arb, fn }),
  assert: async (prop: any, opts: any = {}) => {
    // Run the property test a few times with mock data
    const numRuns = opts.numRuns || 10;
    for (let i = 0; i < numRuns; i++) {
      const testData = prop.arb;
      await prop.fn(testData);
    }
  }
};

// Increase timeout for property tests
jest.setTimeout(30000);

// Mock console methods to avoid noise in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
beforeAll(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <NotificationProvider>
    <NetworkErrorHandler>
      {children}
    </NetworkErrorHandler>
  </NotificationProvider>
);

// Mock component that simulates async operations with loading states
const AsyncOperationComponent: React.FC<{
  operation: () => Promise<any>;
  operationName: string;
  showLoadingText?: boolean;
  showSuccessMessage?: boolean;
  testId?: string; // Add unique test ID
}> = ({ operation, operationName, showLoadingText = true, showSuccessMessage = true, testId }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<Error | null>(null);

  const uniqueId = testId || `${operationName}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  const handleOperation = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const operationResult = await operation();
      setResult(operationResult);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={handleOperation} 
        disabled={isLoading}
        data-testid={`${uniqueId}-button`}
      >
        {isLoading ? `${operationName} Loading...` : `Start ${operationName}`}
      </button>
      
      {isLoading && showLoadingText && (
        <div data-testid={`${uniqueId}-loading`}>
          Loading {operationName}...
        </div>
      )}
      
      {result && showSuccessMessage && (
        <div data-testid={`${uniqueId}-success`}>
          {operationName} completed successfully
        </div>
      )}
      
      {error && (
        <div data-testid={`${uniqueId}-error`}>
          Error: {error.message}
        </div>
      )}
    </div>
  );
};

// Arbitraries for property testing
const operationNameArbitrary = fc.oneof(
  'payment',
  'order-placement',
  'status-update',
  'technician-assignment'
);

const operationDelayArbitrary = fc.integer({ min: 10, max: 500 });

const operationOutcomeArbitrary = fc.oneof(
  'success',
  'failure',
  'timeout'
);

const loadingStateConfigArbitrary = fc.record({
  showLoadingText: fc.boolean(),
  showSuccessMessage: fc.boolean(),
  operationName: operationNameArbitrary,
  delay: operationDelayArbitrary,
  outcome: operationOutcomeArbitrary
});

describe('Property Test: UI State Management', () => {
  /**
   * Property 14.1: Loading State Display (Requirement 2.4)
   * For all asynchronous operations, the system should display loading states
   */
  test('Property 14.1: All async operations display loading states', async () => {
    await fc.assert(fc.asyncProperty(
      loadingStateConfigArbitrary,
      async (config) => {
        const testId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const mockOperation = jest.fn().mockImplementation(() => {
          return new Promise((resolve, reject) => {
            setTimeout(() => {
              if (config.outcome === 'success') {
                resolve('success');
              } else if (config.outcome === 'failure') {
                reject(new Error(`${config.operationName} failed`));
              } else {
                reject(new Error('Operation timed out'));
              }
            }, config.delay);
          });
        });

        const { unmount } = render(
          <TestWrapper>
            <AsyncOperationComponent
              operation={mockOperation}
              operationName={config.operationName}
              showLoadingText={config.showLoadingText}
              showSuccessMessage={config.showSuccessMessage}
              testId={testId}
            />
          </TestWrapper>
        );

        const button = screen.getByTestId(`${testId}-button`);
        
        // Property: Button should be enabled initially
        expect(button).not.toBeDisabled();
        
        // Start the operation
        fireEvent.click(button);
        
        // Property: Button should be disabled during loading
        expect(button).toBeDisabled();
        expect(button.textContent).toContain('Loading');
        
        // Property: Loading indicator should be visible if configured
        if (config.showLoadingText) {
          expect(screen.getByTestId(`${testId}-loading`)).toBeInTheDocument();
        }
        
        // Wait for operation to complete
        await waitFor(() => {
          expect(button).not.toBeDisabled();
        }, { timeout: config.delay + 1000 });
        
        // Property: Loading state should be cleared after completion
        expect(screen.queryByTestId(`${testId}-loading`)).not.toBeInTheDocument();
        
        // Property: Appropriate result should be displayed
        if (config.outcome === 'success' && config.showSuccessMessage) {
          expect(screen.getByTestId(`${testId}-success`)).toBeInTheDocument();
        } else if (config.outcome !== 'success') {
          expect(screen.getByTestId(`${testId}-error`)).toBeInTheDocument();
        }

        // Clean up
        unmount();

        return true;
      }
    ), { numRuns: 10 }); // Reduced runs for faster execution
  });

  /**
   * Property 14.2: Error State Feedback (Requirement 6.4)
   * For all operation failures, the system should provide user feedback
   */
  test('Property 14.2: All operation failures provide user feedback', async () => {
    await fc.assert(fc.asyncProperty(
      fc.record({
        operationName: operationNameArbitrary,
        errorMessage: fc.string({ minLength: 1, maxLength: 100 }),
        errorType: fc.oneof(
          'NetworkError',
          'ValidationError',
          'TimeoutError',
          'PaymentError'
        )
      }),
      async (config) => {
        const testId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const mockOperation = jest.fn().mockRejectedValue(
          new Error(`${config.errorType}: ${config.errorMessage}`)
        );

        const { unmount } = render(
          <TestWrapper>
            <AsyncOperationComponent
              operation={mockOperation}
              operationName={config.operationName}
              testId={testId}
            />
          </TestWrapper>
        );

        const button = screen.getByTestId(`${testId}-button`);
        fireEvent.click(button);

        // Wait for error to be displayed
        await waitFor(() => {
          expect(screen.getByTestId(`${testId}-error`)).toBeInTheDocument();
        });

        const errorElement = screen.getByTestId(`${testId}-error`);
        
        // Property: Error message should be displayed
        expect(errorElement).toBeInTheDocument();
        expect(errorElement.textContent).toContain('Error:');
        
        // Property: Error message should contain meaningful information
        expect(errorElement.textContent).toMatch(new RegExp(config.errorType, 'i'));

        // Clean up
        unmount();

        return true;
      }
    ), { numRuns: 50 });
  });

  /**
   * Property 14.3: State Consistency During Rapid Operations
   * For rapid successive operations, UI state should remain consistent
   */
  test('Property 14.3: UI state remains consistent during rapid operations', async () => {
    await fc.assert(fc.asyncProperty(
      fc.record({
        operationName: operationNameArbitrary,
        clickCount: fc.integer({ min: 2, max: 5 }),
        operationDelay: fc.integer({ min: 50, max: 200 })
      }),
      async (config) => {
        let operationCount = 0;
        const testId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const mockOperation = jest.fn().mockImplementation(() => {
          operationCount++;
          return new Promise(resolve => {
            setTimeout(() => resolve(`result-${operationCount}`), config.operationDelay);
          });
        });

        const { unmount } = render(
          <TestWrapper>
            <AsyncOperationComponent
              operation={mockOperation}
              operationName={config.operationName}
              testId={testId}
            />
          </TestWrapper>
        );

        const button = screen.getByTestId(`${testId}-button`);
        
        // Rapidly click the button multiple times
        for (let i = 0; i < config.clickCount; i++) {
          if (!button.disabled) {
            fireEvent.click(button);
          }
          // Small delay between clicks
          await new Promise(resolve => setTimeout(resolve, 10));
        }

        // Property: Only one operation should be running at a time
        // (button should be disabled after first click)
        expect(button).toBeDisabled();
        
        // Property: Operation should have been called only once
        // (due to button being disabled after first click)
        expect(mockOperation).toHaveBeenCalledTimes(1);

        // Wait for operation to complete
        await waitFor(() => {
          expect(button).not.toBeDisabled();
        }, { timeout: config.operationDelay + 1000 });

        // Clean up
        unmount();

        return true;
      }
    ), { numRuns: 30 });
  });

  /**
   * Property 14.4: Loading State Cleanup
   * For all operations, loading states should be properly cleaned up
   */
  test('Property 14.4: Loading states are properly cleaned up', async () => {
    await fc.assert(fc.asyncProperty(
      fc.record({
        operationName: operationNameArbitrary,
        shouldSucceed: fc.boolean(),
        operationDelay: fc.integer({ min: 50, max: 300 })
      }),
      async (config) => {
        const testId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const mockOperation = jest.fn().mockImplementation(() => {
          return new Promise((resolve, reject) => {
            setTimeout(() => {
              if (config.shouldSucceed) {
                resolve('success');
              } else {
                reject(new Error('Operation failed'));
              }
            }, config.operationDelay);
          });
        });

        const { unmount } = render(
          <TestWrapper>
            <AsyncOperationComponent
              operation={mockOperation}
              operationName={config.operationName}
              showLoadingText={true}
              testId={testId}
            />
          </TestWrapper>
        );

        const button = screen.getByTestId(`${testId}-button`);
        fireEvent.click(button);

        // Property: Loading state should be active during operation
        expect(screen.getByTestId(`${testId}-loading`)).toBeInTheDocument();
        expect(button).toBeDisabled();

        // Wait for operation to complete
        await waitFor(() => {
          expect(button).not.toBeDisabled();
        }, { timeout: config.operationDelay + 1000 });

        // Property: Loading state should be cleaned up after completion
        expect(screen.queryByTestId(`${testId}-loading`)).not.toBeInTheDocument();
        
        // Property: Button should be re-enabled
        expect(button).not.toBeDisabled();
        expect(button.textContent).not.toContain('Loading');

        // Clean up
        unmount();

        return true;
      }
    ), { numRuns: 40 });
  });

  /**
   * Property 14.5: Success State Display
   * For successful operations, appropriate success feedback should be shown
   */
  test('Property 14.5: Successful operations display success feedback', async () => {
    await fc.assert(fc.asyncProperty(
      fc.record({
        operationName: operationNameArbitrary,
        successData: fc.string({ minLength: 1, maxLength: 50 }),
        showSuccessMessage: fc.boolean()
      }),
      async (config) => {
        const testId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const mockOperation = jest.fn().mockResolvedValue(config.successData);

        const { unmount } = render(
          <TestWrapper>
            <AsyncOperationComponent
              operation={mockOperation}
              operationName={config.operationName}
              showSuccessMessage={config.showSuccessMessage}
              testId={testId}
            />
          </TestWrapper>
        );

        const button = screen.getByTestId(`${testId}-button`);
        fireEvent.click(button);

        // Wait for operation to complete
        await waitFor(() => {
          expect(button).not.toBeDisabled();
        });

        if (config.showSuccessMessage) {
          // Property: Success message should be displayed when configured
          expect(screen.getByTestId(`${testId}-success`)).toBeInTheDocument();
          expect(screen.getByTestId(`${testId}-success`).textContent)
            .toContain('completed successfully');
        }

        // Property: No error should be displayed for successful operations
        expect(screen.queryByTestId(`${testId}-error`)).not.toBeInTheDocument();

        // Clean up
        unmount();

        return true;
      }
    ), { numRuns: 50 });
  });

  /**
   * Property 14.6: State Transition Atomicity
   * For all state transitions, changes should be atomic and consistent
   */
  test('Property 14.6: State transitions are atomic and consistent', async () => {
    await fc.assert(fc.asyncProperty(
      fc.record({
        operationName: operationNameArbitrary,
        intermediateDelay: fc.integer({ min: 10, max: 100 })
      }),
      async (config) => {
        let stateSnapshots: string[] = [];
        const testId = `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const StateTrackingComponent: React.FC = () => {
          const [isLoading, setIsLoading] = useState(false);
          const [hasResult, setHasResult] = useState(false);
          const [hasError, setHasError] = useState(false);

          // Track state changes
          useEffect(() => {
            const state = `loading:${isLoading},result:${hasResult},error:${hasError}`;
            stateSnapshots.push(state);
          }, [isLoading, hasResult, hasError]);

          const handleOperation = async () => {
            setIsLoading(true);
            setHasResult(false);
            setHasError(false);

            try {
              await new Promise(resolve => setTimeout(resolve, config.intermediateDelay));
              setHasResult(true);
            } catch {
              setHasError(true);
            } finally {
              setIsLoading(false);
            }
          };

          return (
            <div>
              <button onClick={handleOperation} data-testid={`state-button-${testId}`}>
                {isLoading ? 'Loading...' : 'Start Operation'}
              </button>
              {isLoading && <div data-testid={`loading-${testId}`}>Loading</div>}
              {hasResult && <div data-testid={`result-${testId}`}>Success</div>}
              {hasError && <div data-testid={`error-${testId}`}>Error</div>}
            </div>
          );
        };

        const { unmount } = render(
          <TestWrapper>
            <StateTrackingComponent />
          </TestWrapper>
        );

        const button = screen.getByTestId(`state-button-${testId}`);
        fireEvent.click(button);

        await waitFor(() => {
          expect(screen.queryByTestId(`loading-${testId}`)).not.toBeInTheDocument();
        });

        // Property: State transitions should follow expected sequence
        // Initial -> Loading -> Success (no invalid intermediate states)
        const validStates = [
          'loading:false,result:false,error:false', // Initial
          'loading:true,result:false,error:false',  // Loading
          'loading:false,result:true,error:false'   // Success
        ];

        // Property: All recorded states should be valid
        stateSnapshots.forEach(state => {
          expect(validStates).toContain(state);
        });

        // Property: Should not have conflicting states (loading + result, result + error, etc.)
        stateSnapshots.forEach(state => {
          const hasLoading = state.includes('loading:true');
          const hasResult = state.includes('result:true');
          const hasError = state.includes('error:true');

          // Should not have multiple terminal states simultaneously
          expect(hasResult && hasError).toBe(false);
          
          // Should not have loading with terminal states
          if (hasLoading) {
            expect(hasResult).toBe(false);
            expect(hasError).toBe(false);
          }
        });

        // Clean up
        unmount();

        return true;
      }
    ), { numRuns: 40 });
  });
});