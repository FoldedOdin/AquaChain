import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Test if the component can be imported
describe('RazorpayCheckout Import Test', () => {
  it('can import the component', async () => {
    try {
      const RazorpayCheckout = await import('../RazorpayCheckout');
      expect(RazorpayCheckout.default).toBeDefined();
    } catch (error) {
      console.error('Import error:', error);
      throw error;
    }
  });

  it('can render a simple div', () => {
    const SimpleComponent = () => <div data-testid="simple">Hello</div>;
    render(<SimpleComponent />);
    expect(screen.getByTestId('simple')).toBeInTheDocument();
  });
});