import React from 'react';
import { motion } from 'framer-motion';
import {
  MapPinIcon,
  PhoneIcon,
  EnvelopeIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import ContactForm from './ContactForm';
import { useScrollAnimation } from '../../hooks/useScrollAnimation';

interface ContactSectionProps {
  onFormSubmit?: (data: any) => Promise<void>;
}

/**
 * Contact Section Component
 * Displays contact information and technician inquiry form
 * Includes company details and multiple contact methods
 */
const ContactSection: React.FC<ContactSectionProps> = ({ onFormSubmit }) => {
  const { ref, isInView } = useScrollAnimation();

  const contactInfo = [
    {
      icon: MapPinIcon,
      title: 'Headquarters',
      details: ['123 Water Quality Blvd', 'Tech City, TC 12345', 'United States'],
      color: 'text-aqua-400'
    },
    {
      icon: PhoneIcon,
      title: 'Phone Support',
      details: ['+1 (555) 123-AQUA', 'Mon-Fri: 8AM-6PM EST', 'Emergency: 24/7'],
      color: 'text-emerald-400'
    },
    {
      icon: EnvelopeIcon,
      title: 'Email Contact',
      details: ['info@aquachain.io', 'support@aquachain.io', 'careers@aquachain.io'],
      color: 'text-teal-400'
    },
    {
      icon: ClockIcon,
      title: 'Business Hours',
      details: ['Monday - Friday: 8AM-6PM', 'Saturday: 9AM-3PM', 'Sunday: Emergency Only'],
      color: 'text-cyan-400'
    }
  ];

  return (
    <div className="py-20 px-4 bg-slate-800/50 relative overflow-hidden"
      aria-labelledby="contact-heading"
    >
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-800/30 to-slate-900/50" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_var(--tw-gradient-stops))] from-aqua-900/10 via-transparent to-transparent" />
      
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Section Header */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-16"
        >
          <h2 
            id="contact-heading"
            className="text-4xl lg:text-5xl font-display font-bold text-white mb-6"
          >
            Get in Touch
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Ready to join our network of field technicians or have questions about AquaChain? 
            We'd love to hear from you.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16">
          {/* Contact Information */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <h3 className="text-2xl font-display font-bold text-white mb-8">
              Contact Information
            </h3>
            
            <div className="space-y-8">
              {contactInfo.map((info, index) => (
                <motion.div
                  key={info.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
                  transition={{ duration: 0.4, delay: 0.3 + (index * 0.1), ease: "easeOut" }}
                  className="flex items-start space-x-4"
                >
                  <div className={`flex-shrink-0 w-12 h-12 rounded-xl bg-slate-700/50 flex items-center justify-center ${info.color}`}>
                    <info.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-2">{info.title}</h4>
                    <div className="space-y-1">
                      {info.details.map((detail, detailIndex) => (
                        <p key={detailIndex} className="text-gray-300">
                          {detail}
                        </p>
                      ))}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Additional Information */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ duration: 0.4, delay: 0.7, ease: "easeOut" }}
              className="mt-12 p-6 bg-slate-700/30 rounded-xl border border-slate-600/50"
            >
              <h4 className="text-lg font-semibold text-white mb-3">
                Technician Opportunities
              </h4>
              <p className="text-gray-300 mb-4">
                Join our growing network of certified water quality technicians. We offer:
              </p>
              <ul className="space-y-2 text-gray-300">
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-aqua-400 rounded-full" />
                  <span>Competitive compensation based on performance</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-aqua-400 rounded-full" />
                  <span>Flexible scheduling and service zones</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-aqua-400 rounded-full" />
                  <span>Professional training and certification</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-aqua-400 rounded-full" />
                  <span>Advanced diagnostic tools and support</span>
                </li>
              </ul>
            </motion.div>
          </motion.div>

          {/* Contact Form */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: 30 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
            className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8"
          >
            <h3 className="text-2xl font-display font-bold text-white mb-6">
              Send us a Message
            </h3>
            
            <ContactForm onSubmit={onFormSubmit} />
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ContactSection;