/**
 * Dashboard Layout Component
 * Provides a consistent layout structure for all dashboard types with role-based rendering
 */

import React, { ReactNode } from 'react';

export type UserRole = 'admin' | 'technician' | 'consumer';

interface DashboardLayoutProps {
  /** Dashboard header content */
  header: ReactNode;
  /** Optional sidebar content */
  sidebar?: ReactNode;
  /** Main dashboard content */
  children: ReactNode;
  /** User role for role-based styling */
  role: UserRole;
  /** Optional className for custom styling */
  className?: string;
}

/**
 * DashboardLayout provides a consistent structure for all dashboard types
 * with role-based theming and responsive design
 */
export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  header,
  sidebar,
  children,
  role,
  className = ''
}) => {
  // Role-based theme colors
  const roleThemes = {
    admin: 'bg-blue-50',
    technician: 'bg-green-50',
    consumer: 'bg-gray-50'
  };

  const roleAccents = {
    admin: 'border-blue-200',
    technician: 'border-green-200',
    consumer: 'border-gray-200'
  };

  return (
    <div className={`min-h-screen ${roleThemes[role]} ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className={`mb-8 bg-white rounded-lg shadow-sm border ${roleAccents[role]} p-6`}>
          {header}
        </div>

        {/* Main Content Area */}
        <div className={sidebar ? 'grid grid-cols-1 lg:grid-cols-4 gap-6' : ''}>
          {/* Sidebar (if provided) */}
          {sidebar && (
            <div className="lg:col-span-1">
              <div className={`bg-white rounded-lg shadow-sm border ${roleAccents[role]} p-4 sticky top-4`}>
                {sidebar}
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={sidebar ? 'lg:col-span-3' : ''}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;
