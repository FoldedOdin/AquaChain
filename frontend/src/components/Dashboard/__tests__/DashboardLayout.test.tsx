/**
 * DashboardLayout Component Tests
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DashboardLayout } from '../DashboardLayout';

describe('DashboardLayout Component', () => {
  const mockHeader = <div>Test Header</div>;
  const mockSidebar = <div>Test Sidebar</div>;
  const mockChildren = <div>Test Content</div>;

  describe('Basic Rendering', () => {
    it('renders header content', () => {
      render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(screen.getByText('Test Header')).toBeInTheDocument();
    });

    it('renders main content', () => {
      render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders sidebar when provided', () => {
      render(
        <DashboardLayout header={mockHeader} sidebar={mockSidebar} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(screen.getByText('Test Sidebar')).toBeInTheDocument();
    });

    it('does not render sidebar when not provided', () => {
      render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(screen.queryByText('Test Sidebar')).not.toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin" className="custom-class">
          {mockChildren}
        </DashboardLayout>
      );
      
      const layout = container.firstChild;
      expect(layout).toHaveClass('custom-class');
    });
  });

  describe('Role-Based Theming', () => {
    it('applies admin theme', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      const layout = container.firstChild;
      expect(layout).toHaveClass('bg-blue-50');
    });

    it('applies technician theme', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="technician">
          {mockChildren}
        </DashboardLayout>
      );
      
      const layout = container.firstChild;
      expect(layout).toHaveClass('bg-green-50');
    });

    it('applies consumer theme', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="consumer">
          {mockChildren}
        </DashboardLayout>
      );
      
      const layout = container.firstChild;
      expect(layout).toHaveClass('bg-gray-50');
    });

    it('applies role-specific border colors to header', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.querySelector('.border-blue-200')).toBeInTheDocument();
    });
  });

  describe('Layout Structure', () => {
    it('uses grid layout when sidebar is provided', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} sidebar={mockSidebar} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.querySelector('.grid')).toBeInTheDocument();
      expect(container.querySelector('.lg\\:col-span-1')).toBeInTheDocument();
      expect(container.querySelector('.lg\\:col-span-3')).toBeInTheDocument();
    });

    it('does not use grid layout when sidebar is not provided', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.querySelector('.grid')).not.toBeInTheDocument();
    });

    it('makes sidebar sticky', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} sidebar={mockSidebar} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.querySelector('.sticky')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('has responsive padding classes', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.querySelector('.px-4')).toBeInTheDocument();
      expect(container.querySelector('.sm\\:px-6')).toBeInTheDocument();
      expect(container.querySelector('.lg\\:px-8')).toBeInTheDocument();
    });

    it('has max-width container', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.querySelector('.max-w-7xl')).toBeInTheDocument();
    });

    it('centers content with mx-auto', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.querySelector('.mx-auto')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(screen.getByText('Test Header')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('maintains minimum height for full viewport', () => {
      const { container } = render(
        <DashboardLayout header={mockHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(container.firstChild).toHaveClass('min-h-screen');
    });
  });

  describe('Complex Layouts', () => {
    it('renders complex header with multiple elements', () => {
      const complexHeader = (
        <div>
          <h1>Dashboard Title</h1>
          <p>Dashboard Description</p>
        </div>
      );
      
      render(
        <DashboardLayout header={complexHeader} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(screen.getByText('Dashboard Title')).toBeInTheDocument();
      expect(screen.getByText('Dashboard Description')).toBeInTheDocument();
    });

    it('renders complex sidebar with navigation', () => {
      const complexSidebar = (
        <nav>
          <ul>
            <li>Menu Item 1</li>
            <li>Menu Item 2</li>
          </ul>
        </nav>
      );
      
      render(
        <DashboardLayout header={mockHeader} sidebar={complexSidebar} role="admin">
          {mockChildren}
        </DashboardLayout>
      );
      
      expect(screen.getByText('Menu Item 1')).toBeInTheDocument();
      expect(screen.getByText('Menu Item 2')).toBeInTheDocument();
    });

    it('renders multiple children elements', () => {
      const multipleChildren = (
        <>
          <div>Content 1</div>
          <div>Content 2</div>
          <div>Content 3</div>
        </>
      );
      
      render(
        <DashboardLayout header={mockHeader} role="admin">
          {multipleChildren}
        </DashboardLayout>
      );
      
      expect(screen.getByText('Content 1')).toBeInTheDocument();
      expect(screen.getByText('Content 2')).toBeInTheDocument();
      expect(screen.getByText('Content 3')).toBeInTheDocument();
    });
  });
});
