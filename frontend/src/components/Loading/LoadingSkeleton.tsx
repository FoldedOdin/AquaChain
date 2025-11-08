/**
 * Loading Skeleton Components
 * Provides placeholder components for lazy-loaded content
 */

import React from 'react';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
}

/**
 * Base skeleton component with shimmer animation
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  width = '100%',
  height = '1rem',
  rounded = false,
}) => {
  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  return (
    <div
      className={`
        animate-pulse bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200
        bg-[length:200%_100%] animate-shimmer
        ${rounded ? 'rounded-full' : 'rounded'}
        ${className}
      `}
      style={style}
      aria-label="Loading..."
      role="status"
    />
  );
};

/**
 * Hero section loading skeleton
 */
export const HeroSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-900 to-blue-600">
      <div className="text-center space-y-8 px-4">
        {/* Logo skeleton */}
        <Skeleton width={120} height={120} rounded className="mx-auto" />
        
        {/* Title skeleton */}
        <div className="space-y-4">
          <Skeleton width={400} height={48} className="mx-auto" />
          <Skeleton width={300} height={24} className="mx-auto" />
        </div>
        
        {/* Button skeletons */}
        <div className="flex gap-4 justify-center">
          <Skeleton width={140} height={48} rounded />
          <Skeleton width={160} height={48} rounded />
        </div>
      </div>
    </div>
  );
};

/**
 * Feature card loading skeleton
 */
export const FeatureCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
      {/* Icon skeleton */}
      <Skeleton width={48} height={48} rounded />
      
      {/* Title skeleton */}
      <Skeleton width="80%" height={24} />
      
      {/* Description skeleton */}
      <div className="space-y-2">
        <Skeleton width="100%" height={16} />
        <Skeleton width="90%" height={16} />
        <Skeleton width="75%" height={16} />
      </div>
      
      {/* Benefits list skeleton */}
      <div className="space-y-2">
        <Skeleton width="60%" height={14} />
        <Skeleton width="70%" height={14} />
        <Skeleton width="55%" height={14} />
      </div>
    </div>
  );
};

/**
 * Features showcase loading skeleton
 */
export const FeaturesShowcaseSkeleton: React.FC = () => {
  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section title skeleton */}
        <div className="text-center mb-12">
          <Skeleton width={300} height={32} className="mx-auto mb-4" />
          <Skeleton width={500} height={20} className="mx-auto" />
        </div>
        
        {/* Feature cards grid skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {Array.from({ length: 3 }).map((_, index) => (
            <FeatureCardSkeleton key={index} />
          ))}
        </div>
        
        {/* Trust indicators skeleton */}
        <div className="mt-16 flex justify-center space-x-8">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="text-center">
              <Skeleton width={80} height={32} className="mx-auto mb-2" />
              <Skeleton width={100} height={16} className="mx-auto" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

/**
 * Role selection loading skeleton
 */
export const RoleSelectionSkeleton: React.FC = () => {
  return (
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4">
        {/* Section title skeleton */}
        <div className="text-center mb-12">
          <Skeleton width={250} height={32} className="mx-auto mb-4" />
          <Skeleton width={400} height={20} className="mx-auto" />
        </div>
        
        {/* Role cards skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {Array.from({ length: 2 }).map((_, index) => (
            <div key={index} className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-8 space-y-6">
              {/* Icon skeleton */}
              <Skeleton width={64} height={64} rounded className="mx-auto" />
              
              {/* Title skeleton */}
              <Skeleton width={150} height={24} className="mx-auto" />
              
              {/* Description skeleton */}
              <div className="space-y-2">
                <Skeleton width="100%" height={16} />
                <Skeleton width="90%" height={16} />
              </div>
              
              {/* Benefits skeleton */}
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, benefitIndex) => (
                  <Skeleton key={benefitIndex} width="80%" height={14} />
                ))}
              </div>
              
              {/* Button skeleton */}
              <Skeleton width={140} height={44} rounded className="mx-auto" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

/**
 * Contact section loading skeleton
 */
export const ContactSkeleton: React.FC = () => {
  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto">
          {/* Title skeleton */}
          <div className="text-center mb-8">
            <Skeleton width={200} height={32} className="mx-auto mb-4" />
            <Skeleton width={350} height={20} className="mx-auto" />
          </div>
          
          {/* Form skeleton */}
          <div className="bg-white rounded-lg shadow-lg p-8 space-y-6">
            {/* Form fields skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Skeleton width={60} height={16} />
                <Skeleton width="100%" height={44} />
              </div>
              <div className="space-y-2">
                <Skeleton width={60} height={16} />
                <Skeleton width="100%" height={44} />
              </div>
            </div>
            
            <div className="space-y-2">
              <Skeleton width={60} height={16} />
              <Skeleton width="100%" height={44} />
            </div>
            
            <div className="space-y-2">
              <Skeleton width={80} height={16} />
              <Skeleton width="100%" height={120} />
            </div>
            
            {/* Submit button skeleton */}
            <Skeleton width={120} height={44} rounded />
          </div>
        </div>
      </div>
    </section>
  );
};

/**
 * Generic page loading skeleton
 */
export const PageSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen">
      <HeroSkeleton />
      <FeaturesShowcaseSkeleton />
      <RoleSelectionSkeleton />
      <ContactSkeleton />
    </div>
  );
};