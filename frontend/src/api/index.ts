/**
 * API Module Barrel Export
 *
 * Import from here for convenience:
 *   import { readingsApi, alertsApi, devicesApi } from '../api';
 *
 * Or import directly from domain modules for tree-shaking:
 *   import { readingsApi } from '../api/readings';
 */

export { apiFetch, API_BASE_URL } from './client';
export type { ApiError, RequestOptions } from './client';

export { ENDPOINTS } from './endpoints';

export { readingsApi } from './readings';
export type { ReadingHistoryResponse, LatestReadingResponse, TrendDataPoint } from './readings';

export { alertsApi } from './alerts';

export { devicesApi } from './devices';

export { usersApi } from './users';
