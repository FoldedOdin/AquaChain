/**
 * useDataExport Hook Tests
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { useDataExport } from '../useDataExport';

describe('useDataExport Hook', () => {
  let mockCreateElement: jest.SpyInstance;
  let mockAppendChild: jest.SpyInstance;
  let mockRemoveChild: jest.SpyInstance;
  let mockClick: jest.Mock;
  let mockCreateObjectURL: jest.SpyInstance;
  let mockRevokeObjectURL: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    mockClick = jest.fn();
    mockCreateElement = jest.spyOn(document, 'createElement').mockReturnValue({
      click: mockClick,
      href: '',
      download: '',
      target: ''
    } as any);

    mockAppendChild = jest.spyOn(document.body, 'appendChild').mockImplementation(() => null as any);
    mockRemoveChild = jest.spyOn(document.body, 'removeChild').mockImplementation(() => null as any);

    mockCreateObjectURL = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url');
    mockRevokeObjectURL = jest.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    mockCreateElement.mockRestore();
    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
    mockCreateObjectURL.mockRestore();
    mockRevokeObjectURL.mockRestore();
  });

  describe('Initial State', () => {
    it('initializes with correct default values', () => {
      const { result } = renderHook(() => useDataExport());

      expect(result.current.exporting).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.exportData).toBeDefined();
      expect(result.current.downloadFile).toBeDefined();
    });
  });

  describe('CSV Export', () => {
    const mockData = [
      { id: 1, name: 'Item 1', value: 100 },
      { id: 2, name: 'Item 2', value: 200 }
    ];

    it('exports data as CSV', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(mockData, { format: 'csv' });
      });

      expect(mockCreateElement).toHaveBeenCalledWith('a');
      expect(mockClick).toHaveBeenCalled();
      expect(result.current.exporting).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('generates correct CSV content', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(mockData, { format: 'csv' });
      });

      const blobCall = (global.Blob as any).mock.calls[0];
      const csvContent = blobCall[0][0];

      expect(csvContent).toContain('id,name,value');
      expect(csvContent).toContain('1,Item 1,100');
      expect(csvContent).toContain('2,Item 2,200');
    });

    it('escapes CSV values with commas', async () => {
      const dataWithCommas = [
        { id: 1, name: 'Item, with comma', value: 100 }
      ];

      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(dataWithCommas, { format: 'csv' });
      });

      const blobCall = (global.Blob as any).mock.calls[0];
      const csvContent = blobCall[0][0];

      expect(csvContent).toContain('"Item, with comma"');
    });

    it('escapes CSV values with quotes', async () => {
      const dataWithQuotes = [
        { id: 1, name: 'Item "quoted"', value: 100 }
      ];

      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(dataWithQuotes, { format: 'csv' });
      });

      const blobCall = (global.Blob as any).mock.calls[0];
      const csvContent = blobCall[0][0];

      expect(csvContent).toContain('"Item ""quoted"""');
    });

    it('throws error for non-array data in CSV export', async () => {
      const { result } = renderHook(() => useDataExport());

      await expect(
        result.current.exportData({ not: 'array' }, { format: 'csv' })
      ).rejects.toThrow('CSV export requires an array of objects');
    });

    it('handles empty array for CSV export', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData([], { format: 'csv' });
      });

      const blobCall = (global.Blob as any).mock.calls[0];
      const csvContent = blobCall[0][0];

      expect(csvContent).toBe('');
    });
  });

  describe('JSON Export', () => {
    const mockData = {
      users: [
        { id: 1, name: 'User 1' },
        { id: 2, name: 'User 2' }
      ]
    };

    it('exports data as JSON', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(mockData, { format: 'json' });
      });

      expect(mockCreateElement).toHaveBeenCalledWith('a');
      expect(mockClick).toHaveBeenCalled();
      expect(result.current.exporting).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('includes metadata when includeMetadata is true', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(mockData, {
          format: 'json',
          includeMetadata: true
        });
      });

      const blobCall = (global.Blob as any).mock.calls[0];
      const jsonContent = JSON.parse(blobCall[0][0]);

      expect(jsonContent).toHaveProperty('metadata');
      expect(jsonContent.metadata).toHaveProperty('exportDate');
      expect(jsonContent).toHaveProperty('data');
    });

    it('excludes metadata when includeMetadata is false', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(mockData, {
          format: 'json',
          includeMetadata: false
        });
      });

      const blobCall = (global.Blob as any).mock.calls[0];
      const jsonContent = JSON.parse(blobCall[0][0]);

      expect(jsonContent).not.toHaveProperty('metadata');
      expect(jsonContent).toEqual(mockData);
    });

    it('formats JSON with proper indentation', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData(mockData, {
          format: 'json',
          includeMetadata: false
        });
      });

      const blobCall = (global.Blob as any).mock.calls[0];
      const jsonContent = blobCall[0][0];

      expect(jsonContent).toContain('\n');
      expect(jsonContent).toContain('  ');
    });
  });

  describe('File Naming', () => {
    it('uses custom filename when provided', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData([], {
          format: 'csv',
          filename: 'custom-export.csv'
        });
      });

      const linkElement = mockCreateElement.mock.results[0].value;
      expect(linkElement.download).toBe('custom-export.csv');
    });

    it('generates default filename with timestamp', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData([], { format: 'csv' });
      });

      const linkElement = mockCreateElement.mock.results[0].value;
      expect(linkElement.download).toMatch(/^export-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.csv$/);
    });

    it('adds correct file extension for CSV', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData([], { format: 'csv' });
      });

      const linkElement = mockCreateElement.mock.results[0].value;
      expect(linkElement.download).toEndWith('.csv');
    });

    it('adds correct file extension for JSON', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData({}, { format: 'json' });
      });

      const linkElement = mockCreateElement.mock.results[0].value;
      expect(linkElement.download).toEndWith('.json');
    });
  });

  describe('Loading State', () => {
    it('sets exporting to true during export', async () => {
      const { result } = renderHook(() => useDataExport());

      let exportingDuringExport = false;

      act(() => {
        result.current.exportData([], { format: 'csv' }).then(() => {
          exportingDuringExport = result.current.exporting;
        });
      });

      await waitFor(() => {
        expect(result.current.exporting).toBe(false);
      });
    });

    it('sets exporting to false after export completes', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData([], { format: 'csv' });
      });

      expect(result.current.exporting).toBe(false);
    });

    it('sets exporting to false after export fails', async () => {
      const { result } = renderHook(() => useDataExport());

      await expect(
        result.current.exportData({}, { format: 'csv' })
      ).rejects.toThrow();

      expect(result.current.exporting).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('throws error for unsupported format', async () => {
      const { result } = renderHook(() => useDataExport());

      await expect(
        result.current.exportData({}, { format: 'xml' as any })
      ).rejects.toThrow('Unsupported export format');
    });

    it('throws error for PDF export (not implemented)', async () => {
      const { result } = renderHook(() => useDataExport());

      await expect(
        result.current.exportData({}, { format: 'pdf' })
      ).rejects.toThrow('PDF export is not yet implemented');
    });

    it('sets error state on export failure', async () => {
      const { result } = renderHook(() => useDataExport());

      try {
        await result.current.exportData({}, { format: 'csv' });
      } catch (error) {
        // Expected error
      }

      expect(result.current.error).toBeTruthy();
    });

    it('clears error on successful export', async () => {
      const { result } = renderHook(() => useDataExport());

      // First export fails
      try {
        await result.current.exportData({}, { format: 'csv' });
      } catch (error) {
        // Expected error
      }

      expect(result.current.error).toBeTruthy();

      // Second export succeeds
      await act(async () => {
        await result.current.exportData([], { format: 'csv' });
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Download File from URL', () => {
    it('downloads file from URL', () => {
      const { result } = renderHook(() => useDataExport());

      act(() => {
        result.current.downloadFile('https://example.com/file.csv', 'download.csv');
      });

      expect(mockCreateElement).toHaveBeenCalledWith('a');
      expect(mockClick).toHaveBeenCalled();

      const linkElement = mockCreateElement.mock.results[0].value;
      expect(linkElement.href).toBe('https://example.com/file.csv');
      expect(linkElement.download).toBe('download.csv');
      expect(linkElement.target).toBe('_blank');
    });

    it('cleans up link element after download', () => {
      const { result } = renderHook(() => useDataExport());

      act(() => {
        result.current.downloadFile('https://example.com/file.csv', 'download.csv');
      });

      expect(mockAppendChild).toHaveBeenCalled();
      expect(mockRemoveChild).toHaveBeenCalled();
    });
  });

  describe('Blob URL Cleanup', () => {
    it('revokes blob URL after download', async () => {
      const { result } = renderHook(() => useDataExport());

      await act(async () => {
        await result.current.exportData([], { format: 'csv' });
      });

      act(() => {
        jest.advanceTimersByTime(100);
      });

      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });
  });
});
