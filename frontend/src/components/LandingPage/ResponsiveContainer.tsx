import React, { ReactNode } from 'react';

interface ResponsiveContainerProps {
  children: ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

/**
 * Responsive container component with mobile-first design
 * Implements flexible layouts with CSS Grid and Flexbox
 * Breakpoints: mobile (320px+), tablet (768px+), desktop (1024px+), wide (1440px+)
 */
const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className = '',
  size = 'lg',
  padding = 'md'
}) => {
  // Size classes for different container widths
  const sizeClasses = {
    sm: 'max-w-2xl',      // 672px
    md: 'max-w-4xl',      // 896px  
    lg: 'max-w-6xl',      // 1152px
    xl: 'max-w-7xl',      // 1280px
    full: 'max-w-full'    // 100%
  };

  // Padding classes for responsive spacing
  const paddingClasses = {
    none: '',
    sm: 'px-4 sm:px-6',
    md: 'px-4 sm:px-6 lg:px-8',
    lg: 'px-4 sm:px-6 lg:px-8 xl:px-12'
  };

  return (
    <div className={`
      w-full mx-auto
      ${sizeClasses[size]}
      ${paddingClasses[padding]}
      ${className}
    `}>
      {children}
    </div>
  );
};

export default ResponsiveContainer;