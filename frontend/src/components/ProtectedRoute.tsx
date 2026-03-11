import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Helper function to determine dashboard route based on user role
const getDashboardRoute = (role: string): string => {
  switch (role) {
    case 'consumer':
      return '/dashboard/consumer';
    case 'technician':
      return '/dashboard/technician';
    case 'admin':
    case 'administrator':
      return '/dashboard/administrator';
    case 'inventory_manager':
    case 'warehouse_manager':
    case 'supplier_coordinator':
      return '/dashboard/operations';
    case 'procurement_controller':
      return '/dashboard/procurement';
    default:
      return '/dashboard/consumer'; // Default fallback
  }
};

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'consumer' | 'technician' | 'admin' | 'inventory_manager' | 'warehouse_manager' | 'supplier_coordinator' | 'procurement_controller' | string[];
  allowedRoles?: ('consumer' | 'technician' | 'admin' | 'inventory_manager' | 'warehouse_manager' | 'supplier_coordinator' | 'procurement_controller')[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  allowedRoles
}) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  // Debug logging
  console.log('🔒 ProtectedRoute check:', {
    pathname: location.pathname,
    isLoading,
    hasUser: !!user,
    userRole: user?.role,
    requiredRole,
    allowedRoles
  });

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aqua-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    console.log('❌ No user found, redirecting to landing page');
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  // Check role-based access
  if (requiredRole) {
    // Handle array of required roles
    if (Array.isArray(requiredRole)) {
      if (!requiredRole.includes(user.role)) {
        // Redirect to appropriate dashboard based on user's actual role
        const dashboardRoute = getDashboardRoute(user.role);
        return <Navigate to={dashboardRoute} replace />;
      }
    } else {
      // Handle single required role
      if (user.role !== requiredRole) {
        // Redirect to appropriate dashboard based on user's actual role
        const dashboardRoute = getDashboardRoute(user.role);
        return <Navigate to={dashboardRoute} replace />;
      }
    }
  }

  // Check if user role is in allowed roles
  if (allowedRoles && !allowedRoles.includes(user.role as any)) {
    // Redirect to appropriate dashboard based on user's actual role
    const dashboardRoute = getDashboardRoute(user.role);
    return <Navigate to={dashboardRoute} replace />;
  }

  // If this is the generic dashboard route, redirect to role-specific dashboard
  if (location.pathname === '/dashboard' && !requiredRole && !allowedRoles) {
    const dashboardRoute = getDashboardRoute(user.role);
    return <Navigate to={dashboardRoute} replace />;
  }

  // User is authenticated and has proper role access
  return <>{children}</>;
};

export default ProtectedRoute;