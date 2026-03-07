import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';

const PrivacyPolicy: React.FC = () => {
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
            <Shield className="w-8 h-8 text-aqua-600" />
            <h1 className="text-3xl font-bold text-gray-900">Privacy Policy</h1>
          </div>
          <p className="mt-2 text-sm text-gray-600">Last updated: March 7, 2026</p>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow-sm p-8 space-y-8">
          {/* Introduction */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Introduction</h2>
            <p className="text-gray-700 leading-relaxed">
              AquaChain ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our water quality monitoring services. This policy complies with GDPR and applicable data protection laws.
            </p>
          </section>

          {/* Information We Collect */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Information We Collect</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">2.1 Personal Information</h3>
                <p className="text-gray-700 leading-relaxed mb-2">We collect the following personal information:</p>
                <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                  <li><strong>Account Information:</strong> Name, email address, phone number, password (encrypted)</li>
                  <li><strong>Profile Information:</strong> User role (Consumer, Technician, Admin), preferences</li>
                  <li><strong>Location Data:</strong> Address for device installation and service requests</li>
                  <li><strong>Payment Information:</strong> Processed securely through Razorpay (we do not store full credit card details)</li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">2.2 Device and Sensor Data</h3>
                <p className="text-gray-700 leading-relaxed mb-2">Our IoT devices collect:</p>
                <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                  <li><strong>Water Quality Readings:</strong> pH levels, turbidity, TDS (Total Dissolved Solids), temperature</li>
                  <li><strong>Device Metadata:</strong> Device ID, firmware version, battery level, signal strength</li>
                  <li><strong>Timestamps:</strong> Date and time of each reading</li>
                  <li><strong>Device Status:</strong> Online/offline status, maintenance history</li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">2.3 Usage Data</h3>
                <p className="text-gray-700 leading-relaxed mb-2">We automatically collect:</p>
                <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                  <li><strong>Log Data:</strong> IP address, browser type, pages visited, time spent</li>
                  <li><strong>Analytics Data:</strong> Dashboard usage, feature interactions, error logs</li>
                  <li><strong>Communication Data:</strong> Support tickets, service requests, feedback</li>
                </ul>
              </div>
            </div>
          </section>

          {/* How We Use Your Information */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. How We Use Your Information</h2>
            <p className="text-gray-700 leading-relaxed mb-4">We use your information for the following purposes:</p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li><strong>Service Delivery:</strong> Provide real-time water quality monitoring and alerts</li>
              <li><strong>ML Analysis:</strong> Train and improve our water quality prediction models</li>
              <li><strong>Device Management:</strong> Monitor device health, schedule maintenance, dispatch technicians</li>
              <li><strong>Communication:</strong> Send alerts, notifications, service updates, and support responses</li>
              <li><strong>Payment Processing:</strong> Process orders and payments securely</li>
              <li><strong>Analytics:</strong> Improve our services, understand usage patterns, and optimize performance</li>
              <li><strong>Compliance:</strong> Meet legal obligations and enforce our Terms of Service</li>
              <li><strong>Security:</strong> Detect and prevent fraud, unauthorized access, and security threats</li>
            </ul>
          </section>

          {/* Data Sharing */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. How We Share Your Information</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>4.1 We Do Not Sell Your Data:</strong> We never sell your personal information to third parties.
              </p>
              <p className="leading-relaxed">
                <strong>4.2 Service Providers:</strong> We share data with trusted service providers who help us operate our business:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><strong>AWS:</strong> Cloud hosting and data storage (GDPR-compliant)</li>
                <li><strong>Razorpay:</strong> Payment processing (PCI DSS compliant)</li>
                <li><strong>Email Services:</strong> Transactional emails and notifications</li>
              </ul>
              <p className="leading-relaxed mt-4">
                <strong>4.3 Technicians:</strong> When you request service, we share your name, location, and device information with assigned technicians.
              </p>
              <p className="leading-relaxed">
                <strong>4.4 Legal Requirements:</strong> We may disclose information if required by law, court order, or government request.
              </p>
              <p className="leading-relaxed">
                <strong>4.5 Aggregated Data:</strong> We may share anonymized, aggregated data for research and industry insights.
              </p>
            </div>
          </section>

          {/* Data Retention */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Data Retention</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>5.1 Retention Periods:</strong>
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><strong>Raw Sensor Data:</strong> 90 days in active database, then archived to cold storage</li>
                <li><strong>Aggregated Data:</strong> 2 years for analytics and reporting</li>
                <li><strong>User Account Data:</strong> Retained while your account is active</li>
                <li><strong>Audit Logs:</strong> 7 years for compliance purposes</li>
              </ul>
              <p className="leading-relaxed mt-4">
                <strong>5.2 Account Deletion:</strong> When you delete your account, we delete your personal information within 30 days, except where retention is required by law.
              </p>
            </div>
          </section>

          {/* Your Rights (GDPR) */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Your Privacy Rights</h2>
            <p className="text-gray-700 leading-relaxed mb-4">Under GDPR and applicable laws, you have the following rights:</p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li><strong>Right to Access:</strong> Request a copy of your personal data</li>
              <li><strong>Right to Rectification:</strong> Correct inaccurate or incomplete data</li>
              <li><strong>Right to Erasure:</strong> Request deletion of your data ("right to be forgotten")</li>
              <li><strong>Right to Data Portability:</strong> Receive your data in a machine-readable format</li>
              <li><strong>Right to Restrict Processing:</strong> Limit how we use your data</li>
              <li><strong>Right to Object:</strong> Object to certain types of data processing</li>
              <li><strong>Right to Withdraw Consent:</strong> Withdraw consent for data processing at any time</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-4">
              To exercise these rights, contact us at <a href="mailto:privacy@aquachain.io" className="text-aqua-600 hover:text-aqua-700 underline">privacy@aquachain.io</a>
            </p>
          </section>

          {/* Data Security */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Data Security</h2>
            <p className="text-gray-700 leading-relaxed mb-4">We implement industry-standard security measures:</p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li><strong>Encryption:</strong> TLS 1.2+ for data in transit, AES-256 for data at rest</li>
              <li><strong>Authentication:</strong> AWS Cognito with MFA support</li>
              <li><strong>Access Control:</strong> Role-based access control (RBAC) with least privilege</li>
              <li><strong>Monitoring:</strong> 24/7 security monitoring and intrusion detection</li>
              <li><strong>Auditing:</strong> Comprehensive audit logs for all sensitive operations</li>
              <li><strong>Regular Testing:</strong> Penetration testing and security audits</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-4">
              However, no method of transmission over the internet is 100% secure. We cannot guarantee absolute security.
            </p>
          </section>

          {/* Cookies and Tracking */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Cookies and Tracking Technologies</h2>
            <div className="space-y-4 text-gray-700">
              <p className="leading-relaxed">
                <strong>8.1 Essential Cookies:</strong> Required for authentication and basic functionality
              </p>
              <p className="leading-relaxed">
                <strong>8.2 Analytics Cookies:</strong> Help us understand how you use our service (you can opt out)
              </p>
              <p className="leading-relaxed">
                <strong>8.3 Managing Cookies:</strong> You can control cookies through your browser settings. Disabling essential cookies may affect functionality.
              </p>
            </div>
          </section>

          {/* Children's Privacy */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Children's Privacy</h2>
            <p className="text-gray-700 leading-relaxed">
              Our Service is not intended for children under 18. We do not knowingly collect personal information from children. If you believe we have collected information from a child, please contact us immediately.
            </p>
          </section>

          {/* International Data Transfers */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. International Data Transfers</h2>
            <p className="text-gray-700 leading-relaxed">
              Your data is stored on AWS servers in India (ap-south-1 region). If you access our Service from outside India, your data may be transferred internationally. We ensure appropriate safeguards are in place for such transfers.
            </p>
          </section>

          {/* Changes to Privacy Policy */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Changes to This Privacy Policy</h2>
            <p className="text-gray-700 leading-relaxed">
              We may update this Privacy Policy from time to time. We will notify you of significant changes via email or through the Service. The "Last updated" date at the top indicates when the policy was last revised.
            </p>
          </section>

          {/* Contact Information */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">12. Contact Us</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              For privacy-related questions or to exercise your rights, contact us:
            </p>
            <div className="bg-gray-50 rounded-lg p-6 space-y-2 text-gray-700">
              <p><strong>Data Protection Officer:</strong> privacy@aquachain.io</p>
              <p><strong>General Inquiries:</strong> info@aquachain.io</p>
              <p><strong>Phone:</strong> +91 2345678901</p>
              <p><strong>Address:</strong> Ernakulam, Kerala, India</p>
            </div>
          </section>

          {/* Supervisory Authority */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">13. Supervisory Authority</h2>
            <p className="text-gray-700 leading-relaxed">
              If you believe we have not addressed your privacy concerns adequately, you have the right to lodge a complaint with your local data protection authority.
            </p>
          </section>
        </div>

        {/* Footer Navigation */}
        <div className="mt-8 flex justify-between items-center">
          <Link
            to="/terms"
            className="text-aqua-600 hover:text-aqua-700 transition-colors duration-200"
          >
            View Terms of Service →
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

export default PrivacyPolicy;
