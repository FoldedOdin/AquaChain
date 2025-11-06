import React from 'react';
import AnimatedLogo from './AnimatedLogo';
import TypewriterText from './TypewriterText';
import UnderwaterBackground from './UnderwaterBackground';

interface HeroSectionProps {
  onGetStartedClick: () => void;
}

/**
 * Hero Section Component
 * Full-viewport height section with immersive underwater animations,
 * animated logo, typewriter effect, and call-to-action button
 */
const HeroSection: React.FC<HeroSectionProps> = ({
  onGetStartedClick,
}) => {
  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
      role="banner"
      aria-label="AquaChain Hero Section"
    >
      {/* Underwater Background Animation */}
      <UnderwaterBackground />

      {/* Hero Content */}
      <div className="relative z-10 text-center text-white px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Animated Logo */}
        <div className="mb-8 lg:mb-12">
          <AnimatedLogo />
        </div>

        {/* Main Heading with Typewriter Effect */}
        <div className="mb-6 lg:mb-8 overflow-x-auto">
          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-4xl xl:text-4xl font-display font-bold leading-tight whitespace-nowrap">
            <TypewriterText
              text="Real-Time Water Quality You Can Trust"
              className="inline-block"
            />
          </h1>
        </div>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl lg:text-2xl text-gray-300 mb-8 lg:mb-12 max-w-4xl mx-auto leading-relaxed">
          Monitor water quality with tamper-evident IoT sensors, blockchain-secured data,
          and AI-powered insights for complete peace of mind.
        </p>

        {/* Call-to-Action Button */}
        <div className="flex justify-center items-center mb-16 lg:mb-20">
          {/* Primary CTA */}
          <button
            onClick={onGetStartedClick}
            className="group relative bg-gradient-to-r from-aqua-500 to-aqua-600 hover:from-aqua-600 hover:to-aqua-700 text-white font-semibold px-8 py-4 lg:px-10 lg:py-5 rounded-full transition-all duration-300 shadow-lg hover:shadow-underwater transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2 focus:ring-offset-transparent min-w-[200px]"
            aria-label="Get started with AquaChain"
          >
            <span className="relative z-10 text-lg lg:text-xl">Get Started</span>
            <div className="absolute inset-0 bg-gradient-to-r from-aqua-400 to-aqua-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-sm"></div>
          </button>
        </div>
      </div>

      {/* Scroll Indicator 
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-aqua-400 rounded-full flex justify-center">
          <div className="w-1 h-3 bg-aqua-400 rounded-full mt-2 animate-pulse"></div>
        </div>
      </div>*/}
    </section>
  );
};

export default HeroSection;