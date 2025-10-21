import React, { useRef, useEffect, useState } from 'react';
import { motion, useInView, useAnimation, useReducedMotion } from 'framer-motion';
import { 
  ActivityIcon, 
  ShieldCheckIcon, 
  BrainCircuitIcon,
  ClockIcon,
  TrendingUpIcon
} from 'lucide-react';
import { useRippleEffect } from '../../utils/rippleEffect';

interface FeatureCard {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  benefits: string[];
  color: string;
  delay: number;
}

interface TrustMetric {
  id: string;
  value: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const features: FeatureCard[] = [
  {
    id: 'real-time-monitoring',
    icon: ActivityIcon,
    title: 'Real-Time Monitoring',
    description: 'Continuous water quality tracking with instant alerts and multi-parameter sensing capabilities.',
    benefits: [
      'Multi-parameter sensing (pH, turbidity, chlorine)',
      'Cloud-based analytics and data processing',
      'Instant notifications for quality issues',
      'Historical trend analysis and reporting'
    ],
    color: 'aqua',
    delay: 0
  },
  {
    id: 'tamper-evident-ledger',
    icon: ShieldCheckIcon,
    title: 'Tamper-Evident Ledger',
    description: 'Blockchain-inspired immutable records ensuring data integrity and regulatory compliance.',
    benefits: [
      'Append-only audit trail for all measurements',
      'Cryptographic verification of data integrity',
      'Compliance-ready documentation',
      'Transparent chain of custody tracking'
    ],
    color: 'teal',
    delay: 0.2
  },
  {
    id: 'ai-powered-insights',
    icon: BrainCircuitIcon,
    title: 'AI-Powered Insights',
    description: 'Machine learning algorithms provide predictive analytics and intelligent anomaly detection.',
    benefits: [
      'Random Forest classification for pattern recognition',
      'Anomaly detection with 99.2% accuracy',
      'Predictive maintenance alerts',
      'Automated quality trend forecasting'
    ],
    color: 'emerald',
    delay: 0.4
  }
];

const trustMetrics: TrustMetric[] = [
  {
    id: 'uptime',
    value: '99.8%',
    label: 'System Uptime',
    icon: TrendingUpIcon,
    color: 'aqua'
  },
  {
    id: 'response-time',
    value: '<30s',
    label: 'Alert Response',
    icon: ClockIcon,
    color: 'teal'
  },
  {
    id: 'data-integrity',
    value: '100%',
    label: 'Data Integrity',
    icon: ShieldCheckIcon,
    color: 'emerald'
  }
];

/**
 * Features Showcase Component
 * Displays key AquaChain capabilities with interactive cards and trust indicators
 * Implements responsive grid layout with scroll-triggered animations
 */
const FeaturesShowcase: React.FC = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: '-100px' });
  const controls = useAnimation();
  const shouldReduceMotion = useReducedMotion();
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  // Trigger animations when section comes into view
  useEffect(() => {
    if (isInView) {
      controls.start('visible');
    }
  }, [isInView, controls]);

  // Animation variants for staggered reveal with reduced motion support
  const containerVariants = {
    hidden: { opacity: shouldReduceMotion ? 1 : 0 },
    visible: {
      opacity: 1,
      transition: shouldReduceMotion ? {} : {
        staggerChildren: 0.2,
        delayChildren: 0.1
      }
    }
  };

  const cardVariants = {
    hidden: { 
      opacity: shouldReduceMotion ? 1 : 0, 
      y: shouldReduceMotion ? 0 : 50,
      scale: shouldReduceMotion ? 1 : 0.95
    },
    visible: { 
      opacity: 1, 
      y: 0,
      scale: 1,
      transition: shouldReduceMotion ? {} : {
        duration: 0.6,
        ease: [0.25, 0.46, 0.45, 0.94]
      }
    }
  };

  const trustBarVariants = {
    hidden: { 
      opacity: shouldReduceMotion ? 1 : 0, 
      y: shouldReduceMotion ? 0 : 30 
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: shouldReduceMotion ? {} : {
        duration: 0.8,
        delay: 0.6,
        ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number]
      }
    }
  };

  return (
    <section 
      ref={sectionRef}
      id="features" 
      className="py-20 lg:py-32 bg-gradient-to-b from-slate-900 to-slate-800 relative overflow-hidden"
      aria-labelledby="features-heading"
    >
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-r from-aqua-500/5 via-transparent to-teal-500/5" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.1)_0%,transparent_70%)]" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Section Header */}
        <motion.div 
          className="text-center mb-16 lg:mb-20"
          initial={{ opacity: 0, y: 30 }}
          animate={controls}
          variants={{
            visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
          }}
        >
          <h2 
            id="features-heading"
            className="text-3xl sm:text-4xl lg:text-5xl font-display font-bold text-white mb-6"
          >
            Trusted Water Quality
            <span className="block text-aqua-400 mt-2">You Can Rely On</span>
          </h2>
          <p className="text-lg sm:text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Advanced monitoring technology meets blockchain security to deliver 
            real-time insights you can trust for your water quality needs.
          </p>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          className="features-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-10 mb-20"
          initial="hidden"
          animate={controls}
          variants={containerVariants}
        >
          {features.map((feature) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
              variants={cardVariants}
              isHovered={hoveredCard === feature.id}
              onHover={() => setHoveredCard(feature.id)}
              onLeave={() => setHoveredCard(null)}
            />
          ))}
        </motion.div>

        {/* Trust Indicators Bar */}
        <motion.div
          className="trust-indicators"
          initial="hidden"
          animate={controls}
          variants={trustBarVariants}
        >
          <TrustIndicatorsBar metrics={trustMetrics} />
        </motion.div>
      </div>
    </section>
  );
};

/**
 * Individual Feature Card Component
 */
interface FeatureCardProps {
  feature: FeatureCard;
  variants: any;
  isHovered: boolean;
  onHover: () => void;
  onLeave: () => void;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  feature,
  variants,
  isHovered,
  onHover,
  onLeave
}) => {
  const { icon: Icon, title, description, benefits, color } = feature;
  const createRipple = useRippleEffect({ 
    color: color === 'aqua' ? 'rgba(6, 182, 212, 0.3)' : 
           color === 'teal' ? 'rgba(8, 131, 149, 0.3)' : 
           'rgba(29, 233, 182, 0.3)',
    duration: 600 
  });

  const getColorClasses = (colorName: string) => {
    const colorMap = {
      aqua: {
        icon: 'text-aqua-400',
        border: 'border-aqua-500/20',
        hover: 'hover:border-aqua-400/40',
        glow: 'group-hover:shadow-aqua-500/20'
      },
      teal: {
        icon: 'text-teal-400',
        border: 'border-teal-500/20',
        hover: 'hover:border-teal-400/40',
        glow: 'group-hover:shadow-teal-500/20'
      },
      emerald: {
        icon: 'text-emerald-400',
        border: 'border-emerald-500/20',
        hover: 'hover:border-emerald-400/40',
        glow: 'group-hover:shadow-emerald-500/20'
      }
    };
    return colorMap[colorName as keyof typeof colorMap] || colorMap.aqua;
  };

  const colors = getColorClasses(color);

  return (
    <motion.article
      className={`
        group relative bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 
        border ${colors.border} ${colors.hover}
        transition-all duration-300 ease-out
        hover:bg-slate-800/70 hover:scale-105
        ${colors.glow} hover:shadow-2xl
        cursor-pointer overflow-hidden
      `}
      variants={variants}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      onFocus={onHover}
      onBlur={onLeave}
      onClick={createRipple}
      tabIndex={0}
      role="button"
      aria-label={`Learn more about ${title}`}
    >
      {/* Icon */}
      <div className="mb-6">
        <div className={`
          inline-flex items-center justify-center w-16 h-16 
          rounded-xl bg-slate-700/50 ${colors.icon}
          group-hover:scale-110 transition-transform duration-300
        `}>
          <Icon className="w-8 h-8" aria-hidden="true" />
        </div>
      </div>

      {/* Content */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-white group-hover:text-gray-100 transition-colors">
          {title}
        </h3>
        
        <p className="text-gray-300 leading-relaxed">
          {description}
        </p>

        {/* Benefits List */}
        <ul className="space-y-2">
          {benefits.map((benefit, index) => (
            <li 
              key={index}
              className="flex items-start text-sm text-gray-400 group-hover:text-gray-300 transition-colors"
            >
              <span className={`inline-block w-1.5 h-1.5 rounded-full ${colors.icon} mt-2 mr-3 flex-shrink-0`} />
              {benefit}
            </li>
          ))}
        </ul>
      </div>

      {/* Hover Effect Overlay */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
    </motion.article>
  );
};

/**
 * Trust Indicators Bar Component
 */
interface TrustIndicatorsBarProps {
  metrics: TrustMetric[];
}

const TrustIndicatorsBar: React.FC<TrustIndicatorsBarProps> = ({ metrics }) => {
  return (
    <motion.div 
      className="bg-slate-800/30 backdrop-blur-sm rounded-2xl p-8 lg:p-12 border border-slate-700/50 hover:border-slate-600/50 transition-colors duration-300"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="text-center mb-12">
        <motion.h3 
          className="text-2xl lg:text-3xl font-semibold text-white mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          Proven Reliability
        </motion.h3>
        <motion.p 
          className="text-lg text-gray-400 max-w-2xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          Industry-leading performance metrics you can trust for mission-critical water quality monitoring
        </motion.p>
      </div>

      {/* Metrics Grid */}
      <div 
        className="grid grid-cols-1 sm:grid-cols-3 gap-8 lg:gap-12"
        role="region"
        aria-label="System performance metrics"
      >
        {metrics.map((metric, index) => (
          <TrustMetricCard key={metric.id} metric={metric} index={index} />
        ))}
      </div>

      {/* Additional Context */}
      <motion.div 
        className="mt-12 pt-8 border-t border-slate-700/50 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 1 }}
      >
        <p className="text-sm text-gray-500">
          Metrics updated in real-time • Last updated: {new Date().toLocaleDateString()}
        </p>
      </motion.div>
    </motion.div>
  );
};

/**
 * Individual Trust Metric Card
 */
interface TrustMetricCardProps {
  metric: TrustMetric;
  index: number;
}

const TrustMetricCard: React.FC<TrustMetricCardProps> = ({ metric, index }) => {
  const { icon: Icon, value, label, color } = metric;
  const [count, setCount] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  // Enhanced counter animation with easing
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          
          if (shouldReduceMotion) {
            // Show final value immediately if reduced motion is preferred
            const numericValue = parseFloat(value.replace(/[^\d.]/g, ''));
            if (!isNaN(numericValue)) {
              setCount(numericValue);
            }
            return;
          }
          
          // Extract numeric value for animation
          const numericValue = parseFloat(value.replace(/[^\d.]/g, ''));
          if (!isNaN(numericValue)) {
            setIsAnimating(true);
            const start = 0;
            const duration = 2000;
            const startTime = Date.now();
            
            const animate = () => {
              const elapsed = Date.now() - startTime;
              const progress = Math.min(elapsed / duration, 1);
              
              // Easing function (ease-out cubic)
              const easeOut = 1 - Math.pow(1 - progress, 3);
              const currentValue = start + (numericValue - start) * easeOut;
              
              setCount(currentValue);
              
              if (progress < 1) {
                requestAnimationFrame(animate);
              } else {
                setCount(numericValue);
                setIsAnimating(false);
              }
            };
            
            requestAnimationFrame(animate);
          }
        }
      },
      { threshold: 0.5 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [value, isVisible, shouldReduceMotion]);

  const getColorClasses = (colorName: string) => {
    const colorMap = {
      aqua: {
        text: 'text-aqua-400',
        bg: 'bg-aqua-500/10',
        border: 'border-aqua-500/20'
      },
      teal: {
        text: 'text-teal-400',
        bg: 'bg-teal-500/10',
        border: 'border-teal-500/20'
      },
      emerald: {
        text: 'text-emerald-400',
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/20'
      }
    };
    return colorMap[colorName as keyof typeof colorMap] || colorMap.aqua;
  };

  const colors = getColorClasses(color);

  const formatValue = (val: number) => {
    if (value.includes('%')) {
      return `${val.toFixed(1)}%`;
    } else if (value.includes('<')) {
      return `<${Math.ceil(val)}s`;
    }
    return `${val.toFixed(1)}%`;
  };

  const displayValue = isVisible ? 
    (value.includes('%') || value.includes('<') ? formatValue(count) : value) : 
    '0';

  return (
    <motion.div
      ref={ref}
      className="text-center group"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: index * 0.2 }}
    >
      {/* Icon Container */}
      <div className={`
        inline-flex items-center justify-center w-16 h-16 rounded-xl 
        ${colors.bg} ${colors.border} border ${colors.text} mb-6
        group-hover:scale-110 transition-transform duration-300
      `}>
        <Icon className="w-8 h-8" aria-hidden="true" />
      </div>
      
      {/* Metric Value */}
      <div 
        className={`
          text-4xl font-bold text-white mb-3 tabular-nums
          ${isAnimating ? 'animate-pulse' : ''}
        `}
        aria-live="polite"
        aria-label={`${label}: ${displayValue}`}
      >
        {displayValue}
      </div>
      
      {/* Metric Label */}
      <div className="text-base text-gray-400 font-medium">
        {label}
      </div>
      
      {/* Progress indicator for animation */}
      {isAnimating && !shouldReduceMotion && (
        <div className="mt-3">
          <div className="w-12 h-0.5 bg-slate-700 rounded-full mx-auto overflow-hidden">
            <motion.div
              className={`h-full ${colors.text.replace('text-', 'bg-')} rounded-full`}
              initial={{ width: '0%' }}
              animate={{ width: '100%' }}
              transition={{ duration: 2, ease: 'easeOut' }}
            />
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default FeaturesShowcase;