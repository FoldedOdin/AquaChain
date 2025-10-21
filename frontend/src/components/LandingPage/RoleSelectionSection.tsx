import React from 'react';
import { motion } from 'framer-motion';
import { 
  HomeIcon, 
  WrenchScrewdriverIcon,
  CheckIcon,
  ArrowRightIcon 
} from '@heroicons/react/24/outline';
import { useScrollAnimation } from '../../hooks/useScrollAnimation';

interface RoleSelectionSectionProps {
  onConsumerClick: () => void;
  onTechnicianClick: () => void;
  onViewDashboardsClick: () => void;
}

interface RoleCardProps {
  role: 'consumer' | 'technician';
  title: string;
  description: string;
  benefits: string[];
  ctaText: string;
  onCtaClick: () => void;
  icon: React.ComponentType<{ className?: string }>;
  colorScheme: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    border: string;
  };
  delay?: number;
}

const RoleCard: React.FC<RoleCardProps> = ({
  role,
  title,
  description,
  benefits,
  ctaText,
  onCtaClick,
  icon: Icon,
  colorScheme,
  delay = 0
}) => {
  const { ref, isInView } = useScrollAnimation();

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
      transition={{ 
        duration: 0.6, 
        delay: delay,
        ease: [0.25, 0.46, 0.45, 0.94]
      }}
      className={`
        relative overflow-hidden rounded-2xl p-8 
        ${colorScheme.background} ${colorScheme.border}
        border-2 transition-all duration-300 ease-out
        hover:scale-105 hover:shadow-2xl
        group cursor-pointer
      `}
      onClick={onCtaClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onCtaClick();
        }
      }}
      aria-label={`${title} role selection`}
    >
      {/* Background Gradient Overlay */}
      <div className={`
        absolute inset-0 opacity-0 group-hover:opacity-10 
        transition-opacity duration-300
        bg-gradient-to-br ${colorScheme.primary} to-transparent
      `} />
      
      {/* Icon */}
      <div className={`
        inline-flex items-center justify-center w-16 h-16 mb-6
        rounded-xl ${colorScheme.secondary} 
        group-hover:scale-110 transition-transform duration-300
      `}>
        <Icon className={`w-8 h-8 ${colorScheme.accent}`} />
      </div>

      {/* Title */}
      <h3 className="text-2xl font-display font-bold text-white mb-4 group-hover:text-aqua-300 transition-colors duration-300">
        {title}
      </h3>

      {/* Description */}
      <p className="text-gray-300 text-lg mb-6 leading-relaxed">
        {description}
      </p>

      {/* Benefits List */}
      <ul className="space-y-3 mb-8">
        {benefits.map((benefit, index) => (
          <motion.li
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
            transition={{ 
              duration: 0.4, 
              delay: delay + 0.1 + (index * 0.1),
              ease: "easeOut"
            }}
            className="flex items-start space-x-3"
          >
            <CheckIcon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${colorScheme.accent}`} />
            <span className="text-gray-200 leading-relaxed">{benefit}</span>
          </motion.li>
        ))}
      </ul>

      {/* CTA Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={`
          w-full flex items-center justify-center space-x-2 py-4 px-6
          ${colorScheme.primary} hover:${colorScheme.secondary}
          text-white font-semibold rounded-xl
          transition-all duration-300 ease-out
          focus:outline-none focus:ring-4 focus:ring-aqua-500/50
          group-hover:shadow-lg
        `}
        onClick={(e) => {
          e.stopPropagation();
          onCtaClick();
        }}
      >
        <span>{ctaText}</span>
        <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
      </motion.button>

      {/* Decorative Elements */}
      <div className="absolute top-4 right-4 opacity-10 group-hover:opacity-20 transition-opacity duration-300">
        <Icon className="w-24 h-24 text-white" />
      </div>
    </motion.div>
  );
};

/**
 * Role Selection Section Component
 * Displays Consumer and Technician role cards with distinct styling
 * Implements responsive layout and smooth animations
 */
const RoleSelectionSection: React.FC<RoleSelectionSectionProps> = ({
  onConsumerClick,
  onTechnicianClick,
  onViewDashboardsClick
}) => {
  const { ref: sectionRef, isInView: sectionVisible } = useScrollAnimation();

  const consumerColorScheme = {
    primary: 'bg-aqua-600',
    secondary: 'bg-aqua-700',
    accent: 'text-aqua-400',
    background: 'bg-slate-800/80 backdrop-blur-sm',
    border: 'border-aqua-500/30 hover:border-aqua-400/50'
  };

  const technicianColorScheme = {
    primary: 'bg-teal-600',
    secondary: 'bg-teal-700', 
    accent: 'text-emerald-400',
    background: 'bg-slate-800/80 backdrop-blur-sm',
    border: 'border-teal-500/30 hover:border-emerald-400/50'
  };

  return (
    <div className="py-20 px-4 relative overflow-hidden"
      aria-labelledby="roles-heading"
    >
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900/50 to-slate-800/50" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-aqua-900/20 via-transparent to-transparent" />
      
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Section Header */}
        <motion.div
          ref={sectionRef}
          initial={{ opacity: 0, y: 30 }}
          animate={sectionVisible ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-16"
        >
          <h2 
            id="roles-heading"
            className="text-4xl lg:text-5xl font-display font-bold text-white mb-6"
          >
            Choose Your Experience
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Whether you're monitoring water quality at home or maintaining IoT devices in the field, 
            AquaChain provides tailored solutions for your needs.
          </p>
        </motion.div>

        {/* Role Cards Grid */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 max-w-6xl mx-auto">
          {/* Consumer Role Card */}
          <RoleCard
            role="consumer"
            title="For Consumers"
            description="Monitor your water quality with real-time insights and instant safety alerts. Perfect for homes, schools, and communities."
            benefits={[
              "Real-time water quality monitoring",
              "Instant safety alerts and notifications", 
              "Historical trends and analytics",
              "Easy-to-use dashboard interface",
              "Mobile app for on-the-go monitoring"
            ]}
            ctaText="Explore Dashboard"
            onCtaClick={onViewDashboardsClick}
            icon={HomeIcon}
            colorScheme={consumerColorScheme}
            delay={0.2}
          />

          {/* Technician Role Card */}
          <RoleCard
            role="technician"
            title="For Technicians"
            description="Join our network of field service professionals. Maintain devices, respond to alerts, and earn competitive compensation."
            benefits={[
              "Device diagnostics and maintenance tools",
              "Priority maintenance alerts",
              "Field service mobile app",
              "Performance-based compensation",
              "Flexible scheduling and service zones"
            ]}
            ctaText="Become a Technician"
            onCtaClick={onTechnicianClick}
            icon={WrenchScrewdriverIcon}
            colorScheme={technicianColorScheme}
            delay={0.4}
          />
        </div>

        {/* Additional CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={sectionVisible ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.6, delay: 0.6, ease: "easeOut" }}
          className="text-center mt-16"
        >
          <p className="text-gray-400 mb-6">
            Want to see AquaChain in action first?
          </p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onViewDashboardsClick}
            className="
              inline-flex items-center space-x-2 px-8 py-3
              bg-transparent border-2 border-aqua-500 text-aqua-400
              hover:bg-aqua-500 hover:text-white
              rounded-xl font-semibold transition-all duration-300
              focus:outline-none focus:ring-4 focus:ring-aqua-500/50
            "
          >
            <span>View Demo Dashboards</span>
            <ArrowRightIcon className="w-5 h-5" />
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
};

export default RoleSelectionSection;