/**
 * Users API Domain Module
 */

import { apiFetch } from './client';
import { ENDPOINTS } from './endpoints';
import type { User } from '../types';

export const usersApi = {
  async getAll(tokenRefresher?: () => Promise<string | null>): Promise<User[]> {
    const data = await apiFetch<User[]>(ENDPOINTS.users.list, {}, tokenRefresher);
    return Array.isArray(data) ? data : [];
  },

  async getById(
    userId: string,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<User | null> {
    try {
      return await apiFetch<User>(ENDPOINTS.users.byId(userId), {}, tokenRefresher);
    } catch (err: any) {
      if (err?.status === 404) return null;
      throw err;
    }
  },

  async update(
    userId: string,
    updates: Partial<User>,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<User> {
    return apiFetch<User>(
      ENDPOINTS.users.update(userId),
      { method: 'PUT', body: JSON.stringify(updates) },
      tokenRefresher
    );
  },

  async create(
    user: Partial<User>,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<User> {
    return apiFetch<User>(
      ENDPOINTS.users.create,
      { method: 'POST', body: JSON.stringify(user) },
      tokenRefresher
    );
  },
};
