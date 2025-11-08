/**
 * GDPR Service Tests
 */

import { gdprService } from '../gdprService';

// Mock fetch
global.fetch = jest.fn();

describe('GDPR Service', () => {
  const mockToken = 'test-token';
  const mockUserId = 'user-123';
  const mockEmail = 'test@example.com';

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('token', mockToken);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Data Export', () => {
    describe('requestDataExport', () => {
      it('requests data export successfully', async () => {
        const mockResponse = {
          request_id: 'export-123',
          status: 'processing',
          message: 'Export request received'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse
        });

        const result = await gdprService.requestDataExport(mockUserId, mockEmail);

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/export'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Authorization': `Bearer ${mockToken}`,
              'Content-Type': 'application/json'
            }),
            body: JSON.stringify({
              user_id: mockUserId,
              email: mockEmail
            })
          })
        );

        expect(result).toEqual(mockResponse);
      });

      it('throws error on failed export request', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          json: async () => ({ message: 'Export failed' })
        });

        await expect(
          gdprService.requestDataExport(mockUserId, mockEmail)
        ).rejects.toThrow('Export failed');
      });
    });

    describe('getExportStatus', () => {
      it('gets export status successfully', async () => {
        const mockStatus = {
          request_id: 'export-123',
          status: 'completed',
          created_at: '2024-01-01T00:00:00Z',
          download_url: 'https://example.com/export.json'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockStatus
        });

        const result = await gdprService.getExportStatus('export-123');

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/export/export-123'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': `Bearer ${mockToken}`
            })
          })
        );

        expect(result).toEqual(mockStatus);
      });

      it('throws error on failed status request', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          json: async () => ({ message: 'Status check failed' })
        });

        await expect(
          gdprService.getExportStatus('export-123')
        ).rejects.toThrow('Status check failed');
      });
    });

    describe('listUserExports', () => {
      it('lists user exports successfully', async () => {
        const mockExports = {
          exports: [
            { request_id: 'export-1', status: 'completed' },
            { request_id: 'export-2', status: 'processing' }
          ],
          count: 2
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockExports
        });

        const result = await gdprService.listUserExports();

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/exports'),
          expect.any(Object)
        );

        expect(result).toEqual(mockExports);
      });
    });
  });

  describe('Data Deletion', () => {
    describe('requestDataDeletion', () => {
      it('requests data deletion successfully', async () => {
        const mockResponse = {
          request_id: 'deletion-123',
          status: 'pending',
          message: 'Deletion request received',
          scheduled_deletion_date: '2024-02-01T00:00:00Z',
          days_until_deletion: 30
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse
        });

        const result = await gdprService.requestDataDeletion(mockUserId, mockEmail);

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/delete'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              user_id: mockUserId,
              email: mockEmail,
              immediate: false
            })
          })
        );

        expect(result).toEqual(mockResponse);
      });

      it('requests immediate deletion when specified', async () => {
        const mockResponse = {
          request_id: 'deletion-123',
          status: 'processing',
          message: 'Immediate deletion initiated'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse
        });

        await gdprService.requestDataDeletion(mockUserId, mockEmail, true);

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/delete'),
          expect.objectContaining({
            body: JSON.stringify({
              user_id: mockUserId,
              email: mockEmail,
              immediate: true
            })
          })
        );
      });

      it('throws error on failed deletion request', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          json: async () => ({ message: 'Deletion failed' })
        });

        await expect(
          gdprService.requestDataDeletion(mockUserId, mockEmail)
        ).rejects.toThrow('Deletion failed');
      });
    });

    describe('getDeletionStatus', () => {
      it('gets deletion status successfully', async () => {
        const mockStatus = {
          request_id: 'deletion-123',
          status: 'pending',
          created_at: '2024-01-01T00:00:00Z',
          scheduled_deletion_date: '2024-02-01T00:00:00Z',
          days_remaining: 30
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockStatus
        });

        const result = await gdprService.getDeletionStatus('deletion-123');

        expect(result).toEqual(mockStatus);
      });
    });

    describe('listUserDeletions', () => {
      it('lists user deletions successfully', async () => {
        const mockDeletions = {
          deletions: [
            { request_id: 'deletion-1', status: 'completed' },
            { request_id: 'deletion-2', status: 'pending' }
          ],
          count: 2
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockDeletions
        });

        const result = await gdprService.listUserDeletions();

        expect(result).toEqual(mockDeletions);
      });
    });

    describe('cancelDeletionRequest', () => {
      it('cancels deletion request successfully', async () => {
        const mockResponse = {
          request_id: 'deletion-123',
          status: 'cancelled',
          message: 'Deletion request cancelled'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse
        });

        const result = await gdprService.cancelDeletionRequest('deletion-123');

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/delete/deletion-123/cancel'),
          expect.objectContaining({
            method: 'POST'
          })
        );

        expect(result).toEqual(mockResponse);
      });

      it('throws error on failed cancellation', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          json: async () => ({ message: 'Cancellation failed' })
        });

        await expect(
          gdprService.cancelDeletionRequest('deletion-123')
        ).rejects.toThrow('Cancellation failed');
      });
    });
  });

  describe('Consent Management', () => {
    describe('getUserConsents', () => {
      it('gets user consents successfully', async () => {
        const mockConsents = {
          consents: {
            data_processing: true,
            marketing: false,
            analytics: true
          }
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockConsents
        });

        const result = await gdprService.getUserConsents();

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/consents'),
          expect.any(Object)
        );

        expect(result).toEqual(mockConsents);
      });
    });

    describe('updateConsent', () => {
      it('updates single consent successfully', async () => {
        const mockResponse = {
          consent_type: 'marketing',
          granted: true,
          updated_at: '2024-01-01T00:00:00Z'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse
        });

        const result = await gdprService.updateConsent('marketing', true);

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/consents'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              consent_type: 'marketing',
              granted: true
            })
          })
        );

        expect(result).toEqual(mockResponse);
      });

      it('throws error on failed consent update', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          json: async () => ({ message: 'Update failed' })
        });

        await expect(
          gdprService.updateConsent('marketing', true)
        ).rejects.toThrow('Update failed');
      });
    });

    describe('bulkUpdateConsents', () => {
      it('updates multiple consents successfully', async () => {
        const consents = {
          data_processing: true,
          marketing: false,
          analytics: true
        };

        const mockResponse = {
          updated: 3,
          consents: consents
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse
        });

        const result = await gdprService.bulkUpdateConsents(consents);

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/consents/bulk'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ consents })
          })
        );

        expect(result).toEqual(mockResponse);
      });
    });

    describe('checkConsent', () => {
      it('checks consent and returns true when granted', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ granted: true })
        });

        const result = await gdprService.checkConsent('marketing');

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/consents/check?consent_type=marketing'),
          expect.any(Object)
        );

        expect(result).toBe(true);
      });

      it('checks consent and returns false when not granted', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ granted: false })
        });

        const result = await gdprService.checkConsent('marketing');

        expect(result).toBe(false);
      });

      it('throws error on failed consent check', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          json: async () => ({ message: 'Check failed' })
        });

        await expect(
          gdprService.checkConsent('marketing')
        ).rejects.toThrow('Check failed');
      });
    });

    describe('getConsentHistory', () => {
      it('gets all consent history', async () => {
        const mockHistory = {
          history: [
            { consent_type: 'marketing', granted: true, timestamp: '2024-01-01' },
            { consent_type: 'analytics', granted: false, timestamp: '2024-01-02' }
          ]
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHistory
        });

        const result = await gdprService.getConsentHistory();

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/consents/history'),
          expect.any(Object)
        );

        expect(result).toEqual(mockHistory);
      });

      it('gets consent history for specific type', async () => {
        const mockHistory = {
          history: [
            { consent_type: 'marketing', granted: true, timestamp: '2024-01-01' }
          ]
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockHistory
        });

        const result = await gdprService.getConsentHistory('marketing');

        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/gdpr/consents/history?consent_type=marketing'),
          expect.any(Object)
        );

        expect(result).toEqual(mockHistory);
      });
    });
  });

  describe('Authentication Headers', () => {
    it('includes auth token in headers', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      await gdprService.getUserConsents();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockToken}`
          })
        })
      );
    });

    it('handles missing auth token', async () => {
      localStorage.removeItem('token');

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      await gdprService.getUserConsents();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': ''
          })
        })
      );
    });

    it('includes Content-Type header', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      await gdprService.requestDataExport(mockUserId, mockEmail);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('uses default error message when none provided', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({})
      });

      await expect(
        gdprService.requestDataExport(mockUserId, mockEmail)
      ).rejects.toThrow('Failed to request data export');
    });

    it('uses custom error message when provided', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message: 'Custom error message' })
      });

      await expect(
        gdprService.requestDataExport(mockUserId, mockEmail)
      ).rejects.toThrow('Custom error message');
    });
  });
});
