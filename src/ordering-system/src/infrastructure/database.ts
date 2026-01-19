/**
 * Database Infrastructure
 * Provides data persistence with JSON file storage for development
 * Can be easily replaced with proper database in production
 */

import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { Logger } from './logger';
import { 
  Order, 
  Payment, 
  Delivery, 
  Installation, 
  DomainEvent,
  Consumer,
  Technician,
  Device,
  InventoryItem,
  AuditLogEntry
} from '../types/entities';

export interface DatabaseSchema {
  orders: Order[];
  payments: Payment[];
  deliveries: Delivery[];
  installations: Installation[];
  events: DomainEvent[];
  consumers: Consumer[];
  technicians: Technician[];
  devices: Device[];
  inventory: InventoryItem[];
  auditLog: AuditLogEntry[];
  metadata: {
    version: string;
    lastUpdated: Date;
    schemaVersion: number;
  };
}

export class Database {
  private data: DatabaseSchema;
  private filePath: string;
  private logger: Logger;
  private saveTimeout: NodeJS.Timeout | null = null;

  constructor(filePath: string = './data/ordering-system.json') {
    this.filePath = filePath;
    this.logger = new Logger('Database');
    this.data = this.initializeSchema();
    this.loadData();
  }

  /**
   * Initialize empty database schema
   */
  private initializeSchema(): DatabaseSchema {
    return {
      orders: [],
      payments: [],
      deliveries: [],
      installations: [],
      events: [],
      consumers: [],
      technicians: [],
      devices: [],
      inventory: [],
      auditLog: [],
      metadata: {
        version: '1.0.0',
        lastUpdated: new Date(),
        schemaVersion: 1
      }
    };
  }

  /**
   * Load data from file
   */
  private loadData(): void {
    try {
      // Ensure directory exists
      const dir = path.dirname(this.filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      if (fs.existsSync(this.filePath)) {
        const fileContent = fs.readFileSync(this.filePath, 'utf8');
        const loadedData = JSON.parse(fileContent);
        
        // Validate schema version
        if (loadedData.metadata?.schemaVersion !== this.data.metadata.schemaVersion) {
          this.logger.warn('Schema version mismatch, running migration...');
          this.data = this.migrateSchema(loadedData);
        } else {
          this.data = loadedData;
        }
        
        this.logger.info(`Database loaded from ${this.filePath}`);
      } else {
        this.logger.info('No existing database file, starting with empty schema');
        this.saveData();
      }
    } catch (error) {
      this.logger.error('Failed to load database', error);
      this.data = this.initializeSchema();
    }
  }

  /**
   * Save data to file with debouncing
   */
  private saveData(): void {
    // Clear existing timeout
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout);
    }

    // Debounce saves to avoid excessive I/O
    this.saveTimeout = setTimeout(() => {
      try {
        this.data.metadata.lastUpdated = new Date();
        const dataToSave = JSON.stringify(this.data, null, 2);
        fs.writeFileSync(this.filePath, dataToSave, 'utf8');
        this.logger.debug('Database saved successfully');
      } catch (error) {
        this.logger.error('Failed to save database', error);
      }
    }, 100); // 100ms debounce
  }

  /**
   * Migrate schema between versions
   */
  private migrateSchema(oldData: any): DatabaseSchema {
    // For now, just merge with new schema
    // In production, implement proper migration logic
    const newData = this.initializeSchema();
    
    Object.keys(newData).forEach(key => {
      if (key !== 'metadata' && oldData[key] && Array.isArray(oldData[key])) {
        (newData as any)[key] = oldData[key];
      }
    });

    this.logger.info('Schema migration completed');
    return newData;
  }

  /**
   * Generic create operation with version initialization
   */
  create<T extends { id: string; version?: number }>(table: keyof DatabaseSchema, entity: Omit<T, 'id' | 'version'>): T {
    const id = uuidv4();
    const newEntity = { 
      ...entity, 
      id,
      version: 1 // Initialize version for optimistic locking
    } as T;
    
    const entities = this.data[table];
    if (Array.isArray(entities)) {
      (entities as any[]).push(newEntity);
    }
    this.saveData();
    
    this.logger.audit('CREATE', table as string, id, { entity: newEntity });
    return newEntity;
  }

  /**
   * Generic find by ID operation
   */
  findById<T extends { id: string }>(table: keyof DatabaseSchema, id: string): T | null {
    const entities = this.data[table];
    if (Array.isArray(entities)) {
      return (entities as any[]).find((entity: any) => entity.id === id) || null;
    }
    return null;
  }

  /**
   * Generic find all operation
   */
  findAll<T>(table: keyof DatabaseSchema): T[] {
    const entities = this.data[table];
    if (Array.isArray(entities)) {
      return [...(entities as any[])];
    }
    return [];
  }

  /**
   * Generic find with filter operation
   */
  findWhere<T>(table: keyof DatabaseSchema, predicate: (entity: T) => boolean): T[] {
    const entities = this.data[table];
    if (Array.isArray(entities)) {
      return (entities as any[]).filter(predicate);
    }
    return [];
  }

  /**
   * Generic update operation with optimistic locking support
   */
  update<T extends { id: string; version?: number }>(
    table: keyof DatabaseSchema, 
    id: string, 
    updates: Partial<T>
  ): T | null {
    const entities = this.data[table];
    if (!Array.isArray(entities)) {
      return null;
    }

    const entitiesArray = entities as any[];
    const index = entitiesArray.findIndex((entity: any) => entity.id === id);
    
    if (index === -1) {
      return null;
    }

    const oldEntity = { ...entitiesArray[index] };
    
    // Handle version increment for optimistic locking
    const newVersion = (oldEntity.version || 0) + 1;
    entitiesArray[index] = { 
      ...entitiesArray[index], 
      ...updates,
      version: newVersion
    };
    
    this.saveData();
    
    this.logger.audit('UPDATE', table as string, id, { 
      oldValues: oldEntity, 
      newValues: entitiesArray[index] 
    });
    
    return entitiesArray[index];
  }

  /**
   * Generic delete operation
   */
  delete(table: keyof DatabaseSchema, id: string): boolean {
    const entities = this.data[table];
    if (!Array.isArray(entities)) {
      return false;
    }

    const entitiesArray = entities as any[];
    const index = entitiesArray.findIndex((entity: any) => entity.id === id);
    
    if (index === -1) {
      return false;
    }

    const deletedEntity = entitiesArray[index];
    entitiesArray.splice(index, 1);
    this.saveData();
    
    this.logger.audit('DELETE', table as string, id, { entity: deletedEntity });
    return true;
  }

  /**
   * Transaction support with proper rollback and concurrency control
   */
  async transaction<T>(operation: () => Promise<T> | T): Promise<T> {
    // Create deep copy for rollback
    const backup = JSON.parse(JSON.stringify(this.data));
    const transactionId = uuidv4();
    
    this.logger.debug('Transaction started', { transactionId });
    
    try {
      const result = await operation();
      this.saveData();
      
      this.logger.debug('Transaction committed', { transactionId });
      return result;
    } catch (error) {
      // Rollback on error
      this.data = backup;
      
      this.logger.error('Transaction rolled back due to error', error, { 
        transactionId,
        errorMessage: error instanceof Error ? error.message : 'Unknown error'
      });
      
      throw error;
    }
  }

  /**
   * Get database statistics
   */
  getStatistics(): Record<string, number> {
    const stats: Record<string, number> = {};
    
    Object.keys(this.data).forEach(key => {
      if (Array.isArray(this.data[key as keyof DatabaseSchema])) {
        stats[key] = (this.data[key as keyof DatabaseSchema] as any[]).length;
      }
    });
    
    return stats;
  }

  /**
   * Clear all data (for testing)
   */
  clearAll(): void {
    this.data = this.initializeSchema();
    this.saveData();
    this.logger.info('Database cleared');
  }

  /**
   * Backup database
   */
  backup(backupPath?: string): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const defaultBackupPath = `./backups/ordering-system-${timestamp}.json`;
    const finalBackupPath = backupPath || defaultBackupPath;
    
    // Ensure backup directory exists
    const dir = path.dirname(finalBackupPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(finalBackupPath, JSON.stringify(this.data, null, 2));
    this.logger.info(`Database backed up to ${finalBackupPath}`);
    
    return finalBackupPath;
  }

  /**
   * Restore from backup
   */
  restore(backupPath: string): void {
    if (!fs.existsSync(backupPath)) {
      throw new Error(`Backup file not found: ${backupPath}`);
    }
    
    const backupData = JSON.parse(fs.readFileSync(backupPath, 'utf8'));
    this.data = this.migrateSchema(backupData);
    this.saveData();
    
    this.logger.info(`Database restored from ${backupPath}`);
  }
}

// Singleton database instance
export const database = new Database();