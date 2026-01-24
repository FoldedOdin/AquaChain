/**
 * Sample Data Initialization
 * Provides sample data for development and testing
 */

import { database } from './database';
import { Technician, Device, Consumer, InventoryItem } from '../types/entities';
import { Logger } from './logger';

const logger = new Logger('SampleData');

/**
 * Initialize sample data if database is empty
 */
export function initializeSampleData(): void {
  try {
    // Check if data already exists
    const existingTechnicians = database.findAll<Technician>('technicians');
    const existingDevices = database.findAll<Device>('devices');
    const existingConsumers = database.findAll<Consumer>('consumers');
    const existingInventory = database.findAll<InventoryItem>('inventory');

    // Initialize technicians if none exist
    if (existingTechnicians.length === 0) {
      initializeTechnicians();
    }

    // Initialize devices if none exist
    if (existingDevices.length === 0) {
      initializeDevices();
    }

    // Initialize sample consumers if none exist
    if (existingConsumers.length === 0) {
      initializeConsumers();
    }

    // Initialize inventory if none exist
    if (existingInventory.length === 0) {
      initializeInventory();
    }

    logger.info('Sample data initialization completed');
  } catch (error) {
    logger.error('Failed to initialize sample data', error);
  }
}

/**
 * Initialize sample technicians
 */
function initializeTechnicians(): void {
  const technicians: Omit<Technician, 'id'>[] = [
    {
      name: 'Rajesh Kumar',
      email: 'rajesh.kumar@aquachain.com',
      phone: '+91-9876543210',
      skills: ['Water Quality Testing', 'IoT Device Installation', 'Calibration'],
      availability: 'AVAILABLE',
      location: {
        latitude: 28.6139,
        longitude: 77.2090
      },
      rating: 4.8,
      completedInstallations: 156
    },
    {
      name: 'Priya Sharma',
      email: 'priya.sharma@aquachain.com',
      phone: '+91-9876543211',
      skills: ['IoT Device Installation', 'Network Configuration', 'Customer Support'],
      availability: 'AVAILABLE',
      location: {
        latitude: 28.5355,
        longitude: 77.3910
      },
      rating: 4.9,
      completedInstallations: 203
    },
    {
      name: 'Amit Patel',
      email: 'amit.patel@aquachain.com',
      phone: '+91-9876543212',
      skills: ['Water Quality Testing', 'Device Maintenance', 'Troubleshooting'],
      availability: 'AVAILABLE',
      location: {
        latitude: 28.7041,
        longitude: 77.1025
      },
      rating: 4.7,
      completedInstallations: 134
    },
    {
      name: 'Sneha Reddy',
      email: 'sneha.reddy@aquachain.com',
      phone: '+91-9876543213',
      skills: ['IoT Device Installation', 'Water Quality Testing', 'Data Analysis'],
      availability: 'BUSY',
      location: {
        latitude: 28.4595,
        longitude: 77.0266
      },
      rating: 4.6,
      completedInstallations: 89
    },
    {
      name: 'Vikram Singh',
      email: 'vikram.singh@aquachain.com',
      phone: '+91-9876543214',
      skills: ['Network Configuration', 'Device Calibration', 'Customer Training'],
      availability: 'AVAILABLE',
      location: {
        latitude: 28.6692,
        longitude: 77.4538
      },
      rating: 4.8,
      completedInstallations: 178
    }
  ];

  technicians.forEach(tech => {
    database.create<Technician>('technicians', tech);
  });

  logger.info(`Initialized ${technicians.length} sample technicians`);
}

/**
 * Initialize sample devices
 */
function initializeDevices(): void {
  const devices: Omit<Device, 'id'>[] = [
    {
      serialNumber: 'AC-HOME-001',
      model: 'AC-HOME-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    },
    {
      serialNumber: 'AC-HOME-002',
      model: 'AC-HOME-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    },
    {
      serialNumber: 'AC-HOME-003',
      model: 'AC-HOME-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    },
    {
      serialNumber: 'AC-HOME-004',
      model: 'AC-HOME-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    },
    {
      serialNumber: 'AC-HOME-005',
      model: 'AC-HOME-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    },
    {
      serialNumber: 'AC-PRO-001',
      model: 'AC-PRO-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    },
    {
      serialNumber: 'AC-PRO-002',
      model: 'AC-PRO-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    },
    {
      serialNumber: 'AC-INDUSTRIAL-001',
      model: 'AC-INDUSTRIAL-V1',
      status: 'AVAILABLE',
      createdAt: new Date()
    }
  ];

  devices.forEach(device => {
    database.create<Device>('devices', device);
  });

  logger.info(`Initialized ${devices.length} sample devices`);
}

/**
 * Initialize sample consumers
 */
function initializeConsumers(): void {
  const consumers: Omit<Consumer, 'id'>[] = [
    {
      name: 'John Doe',
      email: 'john.doe@example.com',
      phone: '+91-9876543220',
      address: {
        street: '123 Main Street',
        city: 'New Delhi',
        state: 'Delhi',
        postalCode: '110001',
        country: 'India',
        coordinates: {
          latitude: 28.6139,
          longitude: 77.2090
        }
      },
      createdAt: new Date(),
      updatedAt: new Date()
    },
    {
      name: 'Jane Smith',
      email: 'jane.smith@example.com',
      phone: '+91-9876543221',
      address: {
        street: '456 Park Avenue',
        city: 'Mumbai',
        state: 'Maharashtra',
        postalCode: '400001',
        country: 'India',
        coordinates: {
          latitude: 19.0760,
          longitude: 72.8777
        }
      },
      createdAt: new Date(),
      updatedAt: new Date()
    },
    {
      name: 'Test Consumer',
      email: 'test@example.com',
      phone: '+91-9876543222',
      address: {
        street: '789 Test Street',
        city: 'Bangalore',
        state: 'Karnataka',
        postalCode: '560001',
        country: 'India',
        coordinates: {
          latitude: 12.9716,
          longitude: 77.5946
        }
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }
  ];

  consumers.forEach(consumer => {
    database.create<Consumer>('consumers', consumer);
  });

  logger.info(`Initialized ${consumers.length} sample consumers`);
}

/**
 * Initialize sample inventory
 */
function initializeInventory(): void {
  const inventory: Omit<InventoryItem, 'sku'>[] = [
    {
      name: 'AquaChain Home Water Quality Monitor',
      description: 'IoT-enabled water quality monitoring device for home use',
      price: 15000,
      currency: 'INR',
      totalCount: 100,
      availableCount: 95,
      reservedCount: 5,
      updatedAt: new Date()
    },
    {
      name: 'AquaChain Pro Water Quality Monitor',
      description: 'Professional-grade water quality monitoring device',
      price: 35000,
      currency: 'INR',
      totalCount: 50,
      availableCount: 48,
      reservedCount: 2,
      updatedAt: new Date()
    },
    {
      name: 'AquaChain Industrial Water Quality Monitor',
      description: 'Industrial-grade water quality monitoring system',
      price: 75000,
      currency: 'INR',
      totalCount: 20,
      availableCount: 19,
      reservedCount: 1,
      updatedAt: new Date()
    }
  ];

  inventory.forEach((item, index) => {
    const sku = `AC-${item.name.split(' ')[1].toUpperCase()}-${String(index + 1).padStart(3, '0')}`;
    database.create<InventoryItem>('inventory', { ...item, sku });
  });

  logger.info(`Initialized ${inventory.length} sample inventory items`);
}

/**
 * Get sample consumer ID for testing
 */
export function getSampleConsumerId(): string {
  const consumers = database.findAll<Consumer>('consumers');
  return consumers.length > 0 ? consumers[0].id : '';
}

/**
 * Get sample technician ID for testing
 */
export function getSampleTechnicianId(): string {
  const technicians = database.findAll<Technician>('technicians');
  const availableTechnicians = technicians.filter(t => t.availability === 'AVAILABLE');
  return availableTechnicians.length > 0 ? availableTechnicians[0].id : '';
}

/**
 * Get sample device ID for testing
 */
export function getSampleDeviceId(): string {
  const devices = database.findAll<Device>('devices');
  const availableDevices = devices.filter(d => d.status === 'AVAILABLE');
  return availableDevices.length > 0 ? availableDevices[0].id : '';
}