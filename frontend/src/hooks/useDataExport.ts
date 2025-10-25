/**
 * Data Export Hook
 * Manages data export functionality for dashboards
 */

import { useState, useCallback } from 'react';

export type ExportFormat = 'csv' | 'json' | 'pdf';

interface ExportOptions {
  format: ExportFormat;
  filename?: string;
  includeMetadata?: boolean;
}

interface UseDataExportReturn {
  exporting: boolean;
  error: Error | null;
  exportData: (data: any, options: ExportOptions) => Promise<void>;
  downloadFile: (url: string, filename: string) => void;
}

/**
 * Custom hook for exporting dashboard data in various formats
 * @returns Export functions and state
 */
export function useDataExport(): UseDataExportReturn {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const convertToCSV = useCallback((data: any[]): string => {
    if (!data || data.length === 0) {
      return '';
    }

    // Get headers from first object
    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');

    // Convert data rows
    const csvRows = data.map(row => {
      return headers.map(header => {
        const value = row[header];
        // Escape values containing commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',');
    });

    return [csvHeaders, ...csvRows].join('\n');
  }, []);

  const convertToJSON = useCallback((data: any, includeMetadata: boolean): string => {
    const exportData = includeMetadata
      ? {
          metadata: {
            exportDate: new Date().toISOString(),
            recordCount: Array.isArray(data) ? data.length : 1
          },
          data
        }
      : data;

    return JSON.stringify(exportData, null, 2);
  }, []);

  const downloadFile = useCallback((content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up the URL object
    setTimeout(() => URL.revokeObjectURL(url), 100);
  }, []);

  const exportData = useCallback(async (data: any, options: ExportOptions): Promise<void> => {
    try {
      setExporting(true);
      setError(null);

      const { format, filename, includeMetadata = true } = options;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const defaultFilename = `export-${timestamp}`;

      let content: string;
      let mimeType: string;
      let fileExtension: string;

      switch (format) {
        case 'csv':
          if (!Array.isArray(data)) {
            throw new Error('CSV export requires an array of objects');
          }
          content = convertToCSV(data);
          mimeType = 'text/csv;charset=utf-8;';
          fileExtension = 'csv';
          break;

        case 'json':
          content = convertToJSON(data, includeMetadata);
          mimeType = 'application/json;charset=utf-8;';
          fileExtension = 'json';
          break;

        case 'pdf':
          throw new Error('PDF export is not yet implemented');

        default:
          throw new Error(`Unsupported export format: ${format}`);
      }

      const finalFilename = filename || `${defaultFilename}.${fileExtension}`;
      downloadFile(content, finalFilename, mimeType);

    } catch (err) {
      console.error('Error exporting data:', err);
      setError(err instanceof Error ? err : new Error('Export failed'));
      throw err;
    } finally {
      setExporting(false);
    }
  }, [convertToCSV, convertToJSON, downloadFile]);

  const downloadFileFromUrl = useCallback((url: string, filename: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);

  return {
    exporting,
    error,
    exportData,
    downloadFile: downloadFileFromUrl
  };
}
