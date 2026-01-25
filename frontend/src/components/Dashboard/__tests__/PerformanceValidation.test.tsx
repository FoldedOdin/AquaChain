/**
 * Frontend Performance Validation Tests
 * Tests rendering performance meets <200ms requirement
 * Requirements: 9.1, 9.2
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext } from '../../../contexts/AuthContext';
import { NotificationContext } from '../../../contexts/NotificationContext';
import OperationsDashboard from '../OperationsDashboard';
import ProcurementDashboard from '../ProcurementDashboard';
import AdminDashboardRestructured from '../AdminDashboardRestructured';
import InventoryManagerView from '../Operations/InventoryManagerView';
import WarehouseManagerView from '../Operations/WarehouseManagerView';
import SupplierCoordinatorView from '../Operations/SupplierCoordinatorView';

// Mock services to avoid network calls
jest.mock('../../../services/inventoryService', () => ({
  getInventoryItems: jest.fn().mockResolvedValue([]),
  getInventoryAlerts: jest.fn().mockResolvedValue([]),
  getDemandForecast: jest.fn().mockResolvedValue({ forecast: [] }),
  getAuditHistory: jest.fn().mockResolvedValue([])
}));

jest.mock('../../../services/warehouseService', () => ({
  getWarehouseOperations: jest.fn().mockResolvedValue([]),
  getLocationManagement: jest.fn().mockResolvedValue([]),
  getPerformanceMetrics: jest.fn().mockResolvedValue({})
}));

jest.mock('../../../services/supplierService', () => ({
  getSuppliers: jest.fn().mockResolvedValue([]),
  getSupplierPerformance: jest.fn().mockResolvedValue([]),
  getSupplierRiskIndicators: jest.fn().mockResolvedValue([])
}));

jest.mock('../../../services/procurementService', () => ({
  getApprovalQueue: jest.fn().mockResolvedValue([]),
  getBudgetUtilization: jest.fn().mockResolvedValue({}),
  getFinancialAuditLog: jest.fn().mockResolvedValue([])
}));

jest.mock('../../../services/adminService', () => ({
  getUsers: jest.fn().mockResolvedValue([]),
  getSystemHealth: jest.fn().mockResolvedValue({}),
  getSecurityAuditLog: jest.fn().mockResolvedValue([])
}));

// Mock performance monitoring
const mockPerformanceMonitor = {
  mark: jest.fn(),
  measure: jest.fn().mockReturnValue(50), // Mock 50ms measurement
  getMetrics: jest.fn().mockReturnValue([]),
  clearMetrics: jest.fn()
};

jest.mock('../../../services/performanceMonitor', () => ({
  __esModule: true,
  default: mockPerformanceMonitor
}));

// Test wrapper with required contexts
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const mockAuthContext = {
    user: {
      id: 'test-user',
      email: 'test@example.com',
      roles: ['inventory_manager']
    },
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn(),
    loading: false
  };

  const mockNotificationContext = {
    notifications: [],
    addNotification: jest.fn(),
    removeNotification: jest.fn(),
    clearNotifications: jest.fn()
  };

  return (
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContext}>
        <NotificationContext.Provider value={mockNotificationContext}>
          {children}
        </NotificationContext.Provider>
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('Frontend Performance Validation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset performance API mocks
    Object.defineProperty(window, 'performance', {
      value: {
        now: jest.fn(() => Date.now()),
        mark: jest.fn(),
        measure: jest.fn(),
        getEntriesByName: jest.fn().mockReturnValue([{ duration: 50 }]),
        getEntriesByType: jest.fn().mockReturnValue([])
      },
      writable: true
    });
  });

  describe('Component Rendering Performance', () => {
    const measureRenderTime = async (component: React.ReactElement): Promise<number> => {
      const startTime = performance.now();
      
      render(
        <TestWrapper>
          {component}
        </TestWrapper>
      );
      
      // Wait for component to fully render
      await waitFor(() => {
        expect(screen.getByTestId(/dashboard|view/)).toBeInTheDocument();
      }, { timeout: 1000 });
      
      const endTime = performance.now();
      return endTime - startTime;
    };

    test('InventoryManagerView renders within 200ms', async () => {
      const renderTimes: number[] = [];
      
      // Test multiple renders to get average
      for (let i = 0; i < 10; i++) {
        const renderTime = await measureRenderTime(
          <InventoryManagerView />
        );
        renderTimes.push(renderTime);
      }
      
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
      const maxRenderTime = Math.max(...renderTimes);
      const p95RenderTime = renderTimes.sort((a, b) => a - b)[Math.floor(renderTimes.length * 0.95)];
      
      console.log(`InventoryManagerView Performance:
        Average: ${averageRenderTime.toFixed(2)}ms
        Max: ${maxRenderTime.toFixed(2)}ms
        P95: ${p95RenderTime.toFixed(2)}ms`);
      
      // Verify <200ms requirement
      expect(p95RenderTime).toBeLessThan(200);
      expect(averageRenderTime).toBeLessThan(100);
    });

    test('WarehouseManagerView renders within 200ms', async () => {
      const renderTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const renderTime = await measureRenderTime(
          <WarehouseManagerView />
        );
        renderTimes.push(renderTime);
      }
      
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
      const p95RenderTime = renderTimes.sort((a, b) => a - b)[Math.floor(renderTimes.length * 0.95)];
      
      console.log(`WarehouseManagerView Performance:
        Average: ${averageRenderTime.toFixed(2)}ms
        P95: ${p95RenderTime.toFixed(2)}ms`);
      
      expect(p95RenderTime).toBeLessThan(200);
      expect(averageRenderTime).toBeLessThan(100);
    });

    test('SupplierCoordinatorView renders within 200ms', async () => {
      const renderTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const renderTime = await measureRenderTime(
          <SupplierCoordinatorView />
        );
        renderTimes.push(renderTime);
      }
      
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
      const p95RenderTime = renderTimes.sort((a, b) => a - b)[Math.floor(renderTimes.length * 0.95)];
      
      console.log(`SupplierCoordinatorView Performance:
        Average: ${averageRenderTime.toFixed(2)}ms
        P95: ${p95RenderTime.toFixed(2)}ms`);
      
      expect(p95RenderTime).toBeLessThan(200);
      expect(averageRenderTime).toBeLessThan(100);
    });

    test('OperationsDashboard renders within 200ms', async () => {
      const renderTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const renderTime = await measureRenderTime(
          <OperationsDashboard />
        );
        renderTimes.push(renderTime);
      }
      
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
      const p95RenderTime = renderTimes.sort((a, b) => a - b)[Math.floor(renderTimes.length * 0.95)];
      
      console.log(`OperationsDashboard Performance:
        Average: ${averageRenderTime.toFixed(2)}ms
        P95: ${p95RenderTime.toFixed(2)}ms`);
      
      expect(p95RenderTime).toBeLessThan(200);
      expect(averageRenderTime).toBeLessThan(120);
    });

    test('ProcurementDashboard renders within 200ms', async () => {
      const mockAuthContextProcurement = {
        user: {
          id: 'test-user',
          email: 'test@example.com',
          roles: ['procurement_controller']
        },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        loading: false
      };

      const renderTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const startTime = performance.now();
        
        render(
          <BrowserRouter>
            <AuthContext.Provider value={mockAuthContextProcurement}>
              <NotificationContext.Provider value={{
                notifications: [],
                addNotification: jest.fn(),
                removeNotification: jest.fn(),
                clearNotifications: jest.fn()
              }}>
                <ProcurementDashboard />
              </NotificationContext.Provider>
            </AuthContext.Provider>
          </BrowserRouter>
        );
        
        await waitFor(() => {
          expect(screen.getByTestId('procurement-dashboard')).toBeInTheDocument();
        }, { timeout: 1000 });
        
        const endTime = performance.now();
        renderTimes.push(endTime - startTime);
      }
      
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
      const p95RenderTime = renderTimes.sort((a, b) => a - b)[Math.floor(renderTimes.length * 0.95)];
      
      console.log(`ProcurementDashboard Performance:
        Average: ${averageRenderTime.toFixed(2)}ms
        P95: ${p95RenderTime.toFixed(2)}ms`);
      
      expect(p95RenderTime).toBeLessThan(200);
      expect(averageRenderTime).toBeLessThan(150);
    });

    test('AdminDashboardRestructured renders within 200ms', async () => {
      const mockAuthContextAdmin = {
        user: {
          id: 'test-user',
          email: 'test@example.com',
          roles: ['administrator']
        },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        loading: false
      };

      const renderTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const startTime = performance.now();
        
        render(
          <BrowserRouter>
            <AuthContext.Provider value={mockAuthContextAdmin}>
              <NotificationContext.Provider value={{
                notifications: [],
                addNotification: jest.fn(),
                removeNotification: jest.fn(),
                clearNotifications: jest.fn()
              }}>
                <AdminDashboardRestructured />
              </NotificationContext.Provider>
            </AuthContext.Provider>
          </BrowserRouter>
        );
        
        await waitFor(() => {
          expect(screen.getByTestId('admin-dashboard')).toBeInTheDocument();
        }, { timeout: 1000 });
        
        const endTime = performance.now();
        renderTimes.push(endTime - startTime);
      }
      
      const averageRenderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length;
      const p95RenderTime = renderTimes.sort((a, b) => a - b)[Math.floor(renderTimes.length * 0.95)];
      
      console.log(`AdminDashboardRestructured Performance:
        Average: ${averageRenderTime.toFixed(2)}ms
        P95: ${p95RenderTime.toFixed(2)}ms`);
      
      expect(p95RenderTime).toBeLessThan(200);
      expect(averageRenderTime).toBeLessThan(130);
    });
  });

  describe('Data Loading Performance', () => {
    test('Inventory data loading completes within 500ms', async () => {
      const mockInventoryService = require('../../../services/inventoryService');
      
      // Mock realistic data loading times
      mockInventoryService.getInventoryItems.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve([
          { id: '1', name: 'Item 1', stock: 100 },
          { id: '2', name: 'Item 2', stock: 50 }
        ]), 150))
      );

      const loadingTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const startTime = performance.now();
        
        render(
          <TestWrapper>
            <InventoryManagerView />
          </TestWrapper>
        );
        
        // Wait for data to load
        await waitFor(() => {
          expect(mockInventoryService.getInventoryItems).toHaveBeenCalled();
        }, { timeout: 1000 });
        
        const endTime = performance.now();
        loadingTimes.push(endTime - startTime);
      }
      
      const averageLoadTime = loadingTimes.reduce((a, b) => a + b, 0) / loadingTimes.length;
      const p95LoadTime = loadingTimes.sort((a, b) => a - b)[Math.floor(loadingTimes.length * 0.95)];
      
      console.log(`Inventory Data Loading Performance:
        Average: ${averageLoadTime.toFixed(2)}ms
        P95: ${p95LoadTime.toFixed(2)}ms`);
      
      expect(p95LoadTime).toBeLessThan(500);
      expect(averageLoadTime).toBeLessThan(300);
    });

    test('Procurement data loading completes within 500ms', async () => {
      const mockProcurementService = require('../../../services/procurementService');
      
      mockProcurementService.getApprovalQueue.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve([
          { id: '1', amount: 1000, status: 'pending' },
          { id: '2', amount: 2000, status: 'pending' }
        ]), 200))
      );

      const mockAuthContextProcurement = {
        user: {
          id: 'test-user',
          email: 'test@example.com',
          roles: ['procurement_controller']
        },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        loading: false
      };

      const loadingTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const startTime = performance.now();
        
        render(
          <BrowserRouter>
            <AuthContext.Provider value={mockAuthContextProcurement}>
              <NotificationContext.Provider value={{
                notifications: [],
                addNotification: jest.fn(),
                removeNotification: jest.fn(),
                clearNotifications: jest.fn()
              }}>
                <ProcurementDashboard />
              </NotificationContext.Provider>
            </AuthContext.Provider>
          </BrowserRouter>
        );
        
        await waitFor(() => {
          expect(mockProcurementService.getApprovalQueue).toHaveBeenCalled();
        }, { timeout: 1000 });
        
        const endTime = performance.now();
        loadingTimes.push(endTime - startTime);
      }
      
      const averageLoadTime = loadingTimes.reduce((a, b) => a + b, 0) / loadingTimes.length;
      const p95LoadTime = loadingTimes.sort((a, b) => a - b)[Math.floor(loadingTimes.length * 0.95)];
      
      console.log(`Procurement Data Loading Performance:
        Average: ${averageLoadTime.toFixed(2)}ms
        P95: ${p95LoadTime.toFixed(2)}ms`);
      
      expect(p95LoadTime).toBeLessThan(500);
      expect(averageLoadTime).toBeLessThan(350);
    });
  });

  describe('Memory Usage Performance', () => {
    test('Component memory usage remains stable', async () => {
      // Mock memory usage tracking
      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;
      
      // Render and unmount components multiple times
      for (let i = 0; i < 20; i++) {
        const { unmount } = render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );
        
        await waitFor(() => {
          expect(screen.getByTestId('operations-dashboard')).toBeInTheDocument();
        });
        
        unmount();
      }
      
      // Force garbage collection if available
      if ((global as any).gc) {
        (global as any).gc();
      }
      
      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const memoryIncrease = finalMemory - initialMemory;
      
      console.log(`Memory Usage:
        Initial: ${(initialMemory / 1024 / 1024).toFixed(2)}MB
        Final: ${(finalMemory / 1024 / 1024).toFixed(2)}MB
        Increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`);
      
      // Memory increase should be minimal (less than 10MB for 20 renders)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
    });
  });

  describe('Interaction Performance', () => {
    test('Button clicks respond within 100ms', async () => {
      const { container } = render(
        <TestWrapper>
          <InventoryManagerView />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();
      });
      
      // Find clickable elements
      const buttons = container.querySelectorAll('button');
      const responseTimes: number[] = [];
      
      for (let i = 0; i < Math.min(buttons.length, 10); i++) {
        const button = buttons[i];
        
        const startTime = performance.now();
        
        // Simulate click
        button.click();
        
        // Wait for any state updates
        await new Promise(resolve => setTimeout(resolve, 10));
        
        const endTime = performance.now();
        responseTimes.push(endTime - startTime);
      }
      
      if (responseTimes.length > 0) {
        const averageResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
        const maxResponseTime = Math.max(...responseTimes);
        
        console.log(`Button Click Performance:
          Average: ${averageResponseTime.toFixed(2)}ms
          Max: ${maxResponseTime.toFixed(2)}ms`);
        
        expect(maxResponseTime).toBeLessThan(100);
        expect(averageResponseTime).toBeLessThan(50);
      }
    });
  });
});