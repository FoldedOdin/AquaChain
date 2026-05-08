import React from 'react';
import { Wrench } from 'lucide-react';

interface MaintenanceScreenProps {
  message?: string;
}

const MaintenanceScreen: React.FC<MaintenanceScreenProps> = ({
  message = 'System is under maintenance. Please try again later.',
}) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div className="max-w-md w-full text-center">
      <div className="flex justify-center mb-6">
        <div className="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center">
          <Wrench className="w-10 h-10 text-yellow-600" />
        </div>
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-3">System Maintenance</h1>
      <p className="text-gray-600 mb-8">{message}</p>
      <p className="text-sm text-gray-400">
        We'll be back shortly. Thank you for your patience.
      </p>
    </div>
  </div>
);

export default MaintenanceScreen;
