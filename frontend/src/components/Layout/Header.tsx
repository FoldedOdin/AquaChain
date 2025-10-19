import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-primary-600">AquaChain</h1>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {user?.role === 'technician' ? (
                <a
                  href="/technician"
                  className="text-gray-900 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Field Service
                </a>
              ) : (
                <>
                  <a
                    href="/dashboard"
                    className="text-gray-900 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Dashboard
                  </a>
                  <a
                    href="/history"
                    className="text-gray-500 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    History
                  </a>
                  <a
                    href="/service"
                    className="text-gray-500 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Service
                  </a>
                </>
              )}
            </div>
          </div>

          {/* User Menu */}
          <div className="hidden md:block">
            <div className="ml-4 flex items-center md:ml-6">
              <div className="relative">
                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className="max-w-xs bg-white flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <span className="sr-only">Open user menu</span>
                  <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {user?.profile.firstName?.[0]}{user?.profile.lastName?.[0]}
                    </span>
                  </div>
                </button>

                {isMenuOpen && (
                  <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                    <div className="py-1">
                      <div className="px-4 py-2 text-sm text-gray-700 border-b">
                        <div className="font-medium">{user?.profile.firstName} {user?.profile.lastName}</div>
                        <div className="text-gray-500">{user?.email}</div>
                      </div>
                      <a
                        href="/profile"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Profile
                      </a>
                      <a
                        href="/settings"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Settings
                      </a>
                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Sign out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="bg-white inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className="h-6 w-6"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t">
            {user?.role === 'technician' ? (
              <a
                href="/technician"
                className="text-gray-900 hover:text-primary-600 block px-3 py-2 rounded-md text-base font-medium"
              >
                Field Service
              </a>
            ) : (
              <>
                <a
                  href="/dashboard"
                  className="text-gray-900 hover:text-primary-600 block px-3 py-2 rounded-md text-base font-medium"
                >
                  Dashboard
                </a>
                <a
                  href="/history"
                  className="text-gray-500 hover:text-primary-600 block px-3 py-2 rounded-md text-base font-medium"
                >
                  History
                </a>
                <a
                  href="/service"
                  className="text-gray-500 hover:text-primary-600 block px-3 py-2 rounded-md text-base font-medium"
                >
                  Service
                </a>
              </>
            )}
            <div className="border-t pt-4">
              <div className="flex items-center px-3">
                <div className="h-10 w-10 rounded-full bg-primary-500 flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user?.profile.firstName?.[0]}{user?.profile.lastName?.[0]}
                  </span>
                </div>
                <div className="ml-3">
                  <div className="text-base font-medium text-gray-800">
                    {user?.profile.firstName} {user?.profile.lastName}
                  </div>
                  <div className="text-sm font-medium text-gray-500">{user?.email}</div>
                </div>
              </div>
              <div className="mt-3 px-2 space-y-1">
                <a
                  href="/profile"
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                >
                  Profile
                </a>
                <a
                  href="/settings"
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                >
                  Settings
                </a>
                <button
                  onClick={handleLogout}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                >
                  Sign out
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;