import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText } from 'lucide-react';

const TermsOfService: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link
            to="/"
            className="inline-flex items-center text-aqua-600 hover:text-aqua-700 transition-colors duration-200 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>
          <div className="flex items-center space-x-3">
            <FileText className="w-8 h-8 text-aqua-600" />
            <h1 className="text-3xl font-bold text-gray-900">Terms of Service</h1>
          </div>
          <p className="mt-2 text-sm text-gray-600">Last updated: March 7, 2026</p>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow-sm p-8 space-y-8">
          {/* Introduction */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Agreement to Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              By accessing or using AquaChain's water quality monitoring services ("Service"), you agree to be bound by these Terms of Service ("Terms"). If you disagree with any part of these terms, you may not access the Service.
            </p>
          </section>

          {/* Service Description */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Service Description</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              AquaChain provides real-time water quality monitoring services using IoT sensors and AI-powered analytics. Our services include:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Real-time monitoring of water parameters (pH, turbidity, TDS, temperature)</li>
              <li>ML-powered water quality predictions and alerts</li>
              <li>Device management and maintenance services</li>
              <li>Data analytics and reporting</li>
              <li>Technician dispatch and service request management</li>
            </ul>
          </section>

          {/* User Accounts */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. User Accounts</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>3.1 Account Creation:</strong> You must create an account to use our Service. You agree to provide accurate, current, and complete information during registration.
              </p>
              <p className="leading-relaxed">
                <strong>3.2 Account Security:</strong> You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.
              </p>
              <p className="leading-relaxed">
                <strong>3.3 Account Types:</strong> We offer different account types (Consumer, Technician, Admin) with varying access levels and responsibilities.
              </p>
            </div>
          </section>

          {/* Device Usage */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Device Usage and Ownership</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>4.1 Device Ownership:</strong> AquaChain devices remain the property of AquaChain until full payment is received. Upon full payment, ownership transfers to the customer.
              </p>
              <p className="leading-relaxed">
                <strong>4.2 Device Care:</strong> You agree to use the devices in accordance with provided instructions and to protect them from damage, theft, or misuse.
              </p>
              <p className="leading-relaxed">
                <strong>4.3 Maintenance:</strong> Regular maintenance and calibration are required to ensure accurate readings. Failure to maintain devices may void warranties.
              </p>
            </div>
          </section>

          {/* Data Usage */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Data Collection and Usage</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>5.1 Data Collection:</strong> We collect water quality data from your devices, including pH, turbidity, TDS, and temperature readings.
              </p>
              <p className="leading-relaxed">
                <strong>5.2 Data Ownership:</strong> You retain ownership of your water quality data. We use this data to provide services, generate insights, and improve our ML models.
              </p>
              <p className="leading-relaxed">
                <strong>5.3 Data Sharing:</strong> We do not sell your data to third parties. Aggregated, anonymized data may be used for research and service improvement.
              </p>
            </div>
          </section>

          {/* Payment Terms */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Payment and Billing</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>6.1 Device Purchase:</strong> Device prices are listed on our website. Payment can be made online or cash on delivery (COD).
              </p>
              <p className="leading-relaxed">
                <strong>6.2 Service Fees:</strong> Technician services may incur additional fees. You will be notified of all charges before services are rendered.
              </p>
              <p className="leading-relaxed">
                <strong>6.3 Refunds:</strong> Refunds are available within 30 days of purchase for defective devices. Service fees are non-refundable once services are completed.
              </p>
            </div>
          </section>

          {/* Prohibited Uses */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Prohibited Uses</h2>
            <p className="text-gray-700 leading-relaxed mb-4">You agree not to:</p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Use the Service for any illegal purpose or in violation of any laws</li>
              <li>Attempt to gain unauthorized access to our systems or other users' accounts</li>
              <li>Interfere with or disrupt the Service or servers</li>
              <li>Reverse engineer, decompile, or disassemble our devices or software</li>
              <li>Use the Service to transmit malware, viruses, or harmful code</li>
              <li>Impersonate another person or entity</li>
            </ul>
          </section>

          {/* Warranties and Disclaimers */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Warranties and Disclaimers</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>8.1 Device Warranty:</strong> Devices come with a 1-year limited warranty covering manufacturing defects. This warranty does not cover damage from misuse, accidents, or unauthorized modifications.
              </p>
              <p className="leading-relaxed">
                <strong>8.2 Service Accuracy:</strong> While we strive for accuracy, water quality readings are estimates and should not be the sole basis for critical decisions. Always verify with certified laboratory testing when necessary.
              </p>
              <p className="leading-relaxed">
                <strong>8.3 Disclaimer:</strong> THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED. WE DO NOT GUARANTEE UNINTERRUPTED OR ERROR-FREE SERVICE.
              </p>
            </div>
          </section>

          {/* Limitation of Liability */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Limitation of Liability</h2>
            <p className="text-gray-700 leading-relaxed">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, AQUACHAIN SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, DATA, OR USE, ARISING OUT OF OR RELATED TO YOUR USE OF THE SERVICE.
            </p>
          </section>

          {/* Termination */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Termination</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>10.1 By You:</strong> You may terminate your account at any time by contacting our support team.
              </p>
              <p className="leading-relaxed">
                <strong>10.2 By Us:</strong> We may suspend or terminate your account if you violate these Terms or engage in fraudulent or illegal activities.
              </p>
              <p className="leading-relaxed">
                <strong>10.3 Effect of Termination:</strong> Upon termination, your right to use the Service will cease immediately. You may request a copy of your data within 30 days of termination.
              </p>
            </div>
          </section>

          {/* Changes to Terms */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Changes to Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              We reserve the right to modify these Terms at any time. We will notify you of significant changes via email or through the Service. Your continued use of the Service after changes constitutes acceptance of the modified Terms.
            </p>
          </section>

          {/* Governing Law */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">12. Governing Law</h2>
            <p className="text-gray-700 leading-relaxed">
              These Terms shall be governed by and construed in accordance with the laws of India, without regard to its conflict of law provisions. Any disputes shall be resolved in the courts of Ernakulam, Kerala, India.
            </p>
          </section>

          {/* Contact Information */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">13. Contact Us</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              If you have any questions about these Terms, please contact us:
            </p>
            <div className="bg-gray-50 rounded-lg p-6 space-y-2 text-gray-700">
              <p><strong>Email:</strong> info@aquachain.io</p>
              <p><strong>Phone:</strong> +91 2345678901</p>
              <p><strong>Address:</strong> Ernakulam, Kerala, India</p>
            </div>
          </section>
        </div>

        {/* Footer Navigation */}
        <div className="mt-8 flex justify-between items-center">
          <Link
            to="/privacy"
            className="text-aqua-600 hover:text-aqua-700 transition-colors duration-200"
          >
            View Privacy Policy →
          </Link>
          <Link
            to="/"
            className="text-gray-600 hover:text-gray-700 transition-colors duration-200"
          >
            Back to Home
          </Link>
        </div>
      </main>
    </div>
  );
};

export default TermsOfService;
