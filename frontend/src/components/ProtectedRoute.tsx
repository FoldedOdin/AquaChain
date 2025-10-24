import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'consumer' | 'technician' | 'admin';
  allowedRoles?: ('consumer' | 'technician' | 'admin')[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  allowedRoles
}) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

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
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  // Check role-based access
  if (requiredRole && user.role !== requiredRole) {
    // Redirect to appropriate dashboard based on user's actual role
    return <Navigate to={`/dashboard/${user.role}`} replace />;
  }

  // Check if user role is in allowed roles
  if (allowedRoles && !allowedRoles.includes(user.role as any)) {
    // Redirect to appropriate dashboard based on user's actual role
    return <Navigate to={`/dashboard/${user.role}`} replace />;
  }

  // If this is the generic dashboard route, redirect to role-specific dashboard
  if (location.pathname === '/dashboard' && !requiredRole && !allowedRoles) {
    return <Navigate to={`/dashboard/${user.role}`} replace />;
  }

  // User is authenticated and has proper role access
  return <>{children}</>;
};

export default ProtectedRoute;