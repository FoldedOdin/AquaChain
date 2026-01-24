/**
 * Concurrency Service
 * Provides optimistic locking, transaction handling, and thread-safe operations
 * Implements Requirements 9.2 - Concurrent order processing without data corruption
 */

import { Logger } from '../infrastructure/logger';
import { database, DatabaseSchema } from '../infrastructure/database';

export interface VersionedEntity {
  id: string;
  version: number;
}

export interface OptimisticLockError extends Error {
  name: 'OptimisticLockError';
  entityId: string;
  expectedVersion: number;
  actualVersion: number;
}

export interface ConcurrencyConfig {
  maxRetries: number;
  retryDelayMs: number;
  lockTimeoutMs: number;
}

/**
 * Concurrency Service Implementation
 */
export class ConcurrencyService {
  private logger: Logger;
  private config: ConcurrencyConfig;
  private activeLocks: Map<string, { timestamp: number; operation: string }>;
  private operationQueue: Map<string, Promise<any>>;

  constructor(config?: Partial<ConcurrencyConfig>) {
    this.logger = new Logger('ConcurrencyService');
    this.config = {
      maxRetries: 3,
      retryDelayMs: 100,
      lockTimeoutMs: 5000,
      ...config
    };
    this.activeLocks = new Map();
    this.operationQueue = new Map();

    // Clean up expired locks periodically
    setInterval(() => this.cleanupExpiredLocks(), 1000);

    this.logger.info('Concurrency service initialized', {
      maxRetries: this.config.maxRetries,
      retryDelayMs: this.config.retryDelayMs,
      lockTimeoutMs: this.config.lockTimeoutMs
    });
  }

  /**
   * Execute operation with optimistic locking and retry logic
   */
  async withOptimisticLock<T extends VersionedEntity>(
    table: keyof DatabaseSchema,
    entityId: string,
    operation: (entity: T) => Promise<Partial<T>>,
    operationName: string = 'update'
  ): Promise<T> {
    const lockKey = `${table}:${entityId}`;
    
    // Ensure only one operation per entity at a time
    if (this.operationQueue.has(lockKey)) {
      await this.operationQueue.get(lockKey);
    }

    const operationPromise = this.executeWithRetry(
      table,
      entityId,
      operation,
      operationName
    );

    this.operationQueue.set(lockKey, operationPromise);

    try {
      const result = await operationPromise;
      return result;
    } finally {
      this.operationQueue.delete(lockKey);
    }
  }

  /**
   * Execute operation with retry logic for optimistic locking conflicts
   */
  private async executeWithRetry<T extends VersionedEntity>(
    table: keyof DatabaseSchema,
    entityId: string,
    operation: (entity: T) => Promise<Partial<T>>,
    operationName: string
  ): Promise<T> {
    let attempt = 0;
    let lastError: Error | null = null;

    while (attempt < this.config.maxRetries) {
      try {
        return await this.executeOperation(table, entityId, operation, operationName);
      } catch (error) {
        lastError = error as Error;
        
        if (this.isOptimisticLockError(error)) {
          attempt++;
          
          if (attempt < this.config.maxRetries) {
            const delay = this.config.retryDelayMs * Math.pow(2, attempt - 1); // Exponential backoff
            
            this.logger.warn('Optimistic lock conflict, retrying', {
              entityId,
              table: table as string,
              attempt,
              maxRetries: this.config.maxRetries,
              delayMs: delay,
              error: (error as OptimisticLockError).message
            });

            await this.sleep(delay);
            continue;
          }
        }
        
        // Non-retryable error or max retries exceeded
        break;
      }
    }

    this.logger.error('Operation failed after retries', lastError, {
      entityId,
      table: table as string,
      operationName,
      attempts: attempt,
      maxRetries: this.config.maxRetries
    });

    throw lastError || new Error('Operation failed after retries');
  }

  /**
   * Execute single operation with optimistic locking
   */
  private async executeOperation<T extends VersionedEntity>(
    table: keyof DatabaseSchema,
    entityId: string,
    operation: (entity: T) => Promise<Partial<T>>,
    operationName: string
  ): Promise<T> {
    const lockKey = `${table}:${entityId}`;

    // Acquire lock
    await this.acquireLock(lockKey, operationName);

    try {
      // Get current entity
      const currentEntity = database.findById<T>(table, entityId);
      if (!currentEntity) {
        throw new Error(`Entity not found: ${entityId}`);
      }

      const currentVersion = currentEntity.version;

      // Execute operation
      const updates = await operation(currentEntity);

      // Prepare update with version increment
      const updatedData = {
        ...updates,
        version: currentVersion + 1,
        updatedAt: new Date()
      };

      // Perform optimistic update
      const result = await this.optimisticUpdate(table, entityId, currentVersion, updatedData);

      this.logger.debug('Operation completed successfully', {
        entityId,
        table: table as string,
        operationName,
        oldVersion: currentVersion,
        newVersion: result.version
      });

      return result as unknown as T;

    } finally {
      this.releaseLock(lockKey);
    }
  }

  /**
   * Perform optimistic update with version checking
   */
  private async optimisticUpdate<T extends VersionedEntity>(
    table: keyof DatabaseSchema,
    entityId: string,
    expectedVersion: number,
    updates: Partial<T>
  ): Promise<T> {
    return database.transaction(async () => {
      // Re-read entity to check version
      const currentEntity = database.findById<T>(table, entityId);
      if (!currentEntity) {
        throw new Error(`Entity not found during update: ${entityId}`);
      }

      // Check version for optimistic locking
      if (currentEntity.version !== expectedVersion) {
        const error = new Error(
          `Optimistic lock failure: expected version ${expectedVersion}, ` +
          `but current version is ${currentEntity.version}`
        ) as OptimisticLockError;
        
        error.name = 'OptimisticLockError';
        error.entityId = entityId;
        error.expectedVersion = expectedVersion;
        error.actualVersion = currentEntity.version;
        
        throw error;
      }

      // Perform update
      const updatedEntity = database.update<T>(table, entityId, updates);
      if (!updatedEntity) {
        throw new Error(`Failed to update entity: ${entityId}`);
      }

      return updatedEntity;
    });
  }

  /**
   * Execute multiple operations in a transaction with proper rollback
   */
  async withTransaction<R>(
    operations: Array<() => Promise<any>>,
    transactionName: string = 'transaction'
  ): Promise<R[]> {
    this.logger.info('Starting transaction', {
      transactionName,
      operationCount: operations.length
    });

    return database.transaction(async () => {
      const results: any[] = [];
      
      try {
        for (let i = 0; i < operations.length; i++) {
          const result = await operations[i]();
          results.push(result);
          
          this.logger.debug('Transaction operation completed', {
            transactionName,
            operationIndex: i,
            totalOperations: operations.length
          });
        }

        this.logger.business('Transaction completed successfully', {
          transactionName,
          operationCount: operations.length
        });

        return results;

      } catch (error) {
        this.logger.error('Transaction failed, rolling back', error, {
          transactionName,
          completedOperations: results.length,
          totalOperations: operations.length
        });
        
        throw error; // Database will handle rollback
      }
    });
  }

  /**
   * Acquire lock for entity operation
   */
  private async acquireLock(lockKey: string, operationName: string): Promise<void> {
    const startTime = Date.now();
    
    while (this.activeLocks.has(lockKey)) {
      const lockInfo = this.activeLocks.get(lockKey)!;
      const lockAge = Date.now() - lockInfo.timestamp;
      
      // Check for lock timeout
      if (lockAge > this.config.lockTimeoutMs) {
        this.logger.warn('Lock timeout, forcibly releasing', {
          lockKey,
          lockAge,
          timeoutMs: this.config.lockTimeoutMs,
          previousOperation: lockInfo.operation
        });
        
        this.activeLocks.delete(lockKey);
        break;
      }
      
      // Check for overall timeout
      if (Date.now() - startTime > this.config.lockTimeoutMs) {
        throw new Error(`Failed to acquire lock within timeout: ${lockKey}`);
      }
      
      // Wait before retrying
      await this.sleep(10);
    }
    
    // Acquire lock
    this.activeLocks.set(lockKey, {
      timestamp: Date.now(),
      operation: operationName
    });

    this.logger.debug('Lock acquired', {
      lockKey,
      operationName,
      waitTime: Date.now() - startTime
    });
  }

  /**
   * Release lock for entity operation
   */
  private releaseLock(lockKey: string): void {
    const lockInfo = this.activeLocks.get(lockKey);
    if (lockInfo) {
      const lockDuration = Date.now() - lockInfo.timestamp;
      
      this.activeLocks.delete(lockKey);
      
      this.logger.debug('Lock released', {
        lockKey,
        operation: lockInfo.operation,
        lockDuration
      });
    }
  }

  /**
   * Clean up expired locks
   */
  private cleanupExpiredLocks(): void {
    const now = Date.now();
    const expiredLocks: string[] = [];
    
    for (const [lockKey, lockInfo] of this.activeLocks.entries()) {
      if (now - lockInfo.timestamp > this.config.lockTimeoutMs) {
        expiredLocks.push(lockKey);
      }
    }
    
    if (expiredLocks.length > 0) {
      this.logger.warn('Cleaning up expired locks', {
        expiredLockCount: expiredLocks.length,
        expiredLocks
      });
      
      expiredLocks.forEach(lockKey => this.activeLocks.delete(lockKey));
    }
  }

  /**
   * Check if error is an optimistic lock error
   */
  private isOptimisticLockError(error: any): error is OptimisticLockError {
    return error && error.name === 'OptimisticLockError';
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get concurrency statistics
   */
  getConcurrencyStatistics(): {
    activeLocks: number;
    queuedOperations: number;
    lockDetails: Array<{
      lockKey: string;
      operation: string;
      ageMs: number;
    }>;
  } {
    const now = Date.now();
    
    return {
      activeLocks: this.activeLocks.size,
      queuedOperations: this.operationQueue.size,
      lockDetails: Array.from(this.activeLocks.entries()).map(([lockKey, lockInfo]) => ({
        lockKey,
        operation: lockInfo.operation,
        ageMs: now - lockInfo.timestamp
      }))
    };
  }

  /**
   * Force release all locks (for testing/emergency use)
   */
  forceReleaseAllLocks(): void {
    const lockCount = this.activeLocks.size;
    this.activeLocks.clear();
    
    this.logger.warn('Force released all locks', { lockCount });
  }
}

// Export singleton instance
export const concurrencyService = new ConcurrencyService();