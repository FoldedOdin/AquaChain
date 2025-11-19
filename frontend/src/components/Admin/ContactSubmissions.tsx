import { useState, useEffect } from 'react';
import { 
  EnvelopeIcon, 
  PhoneIcon, 
  UserIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

interface ContactSubmission {
  submissionId: string;
  name: string;
  email: string;
  phone?: string;
  message: string;
  inquiryType: 'technician' | 'general' | 'support';
  status: 'pending' | 'contacted' | 'resolved';
  createdAt: string;
  updatedAt: string;
}

const ContactSubmissions = () => {
  const [submissions, setSubmissions] = useState<ContactSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'contacted' | 'resolved'>('all');
  const [selectedSubmission, setSelectedSubmission] = useState<ContactSubmission | null>(null);

  useEffect(() => {
    fetchSubmissions();
  }, [filter]);

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${API_URL}/admin/contact-submissions?status=${filter}`);
      // const data = await response.json();
      
      // Mock data for demonstration
      const mockData: ContactSubmission[] = [
        {
          submissionId: '1',
          name: 'John Doe',
          email: 'john@example.com',
          phone: '+1234567890',
          message: 'I am interested in becoming a technician in the Kerala area.',
          inquiryType: 'technician',
          status: 'pending',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        },
        {
          submissionId: '2',
          name: 'Jane Smith',
          email: 'jane@example.com',
          message: 'What are the pricing plans for residential users?',
          inquiryType: 'general',
          status: 'contacted',
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          updatedAt: new Date().toISOString()
        }
      ];
      
      setSubmissions(mockData);
    } catch (error) {
      console.error('Error fetching submissions:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (submissionId: string, newStatus: ContactSubmission['status']) => {
    try {
      // TODO: Replace with actual API call
      // await fetch(`${API_URL}/admin/contact-submissions/${submissionId}`, {
      //   method: 'PATCH',
      //   body: JSON.stringify({ status: newStatus })
      // });
      
      setSubmissions(prev =>
        prev.map(sub =>
          sub.submissionId === submissionId
            ? { ...sub, status: newStatus, updatedAt: new Date().toISOString() }
            : sub
        )
      );
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'contacted':
        return 'bg-blue-100 text-blue-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getInquiryTypeColor = (type: string) => {
    switch (type) {
      case 'technician':
        return 'bg-purple-100 text-purple-800';
      case 'support':
        return 'bg-red-100 text-red-800';
      case 'general':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredSubmissions = filter === 'all' 
    ? submissions 
    : submissions.filter(sub => sub.status === filter);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Contact Submissions</h2>
        <div className="flex space-x-2">
          {(['all', 'pending', 'contacted', 'resolved'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === status
                  ? 'bg-aqua-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aqua-600"></div>
        </div>
      ) : filteredSubmissions.length === 0 ? (
        <div className="text-center py-12">
          <ExclamationCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-gray-600">No submissions found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredSubmissions.map((submission) => (
            <div
              key={submission.submissionId}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedSubmission(submission)}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center space-x-3">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <h3 className="font-semibold text-gray-900">{submission.name}</h3>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <EnvelopeIcon className="h-4 w-4" />
                      <span>{submission.email}</span>
                      {submission.phone && (
                        <>
                          <PhoneIcon className="h-4 w-4 ml-2" />
                          <span>{submission.phone}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex flex-col items-end space-y-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(submission.status)}`}>
                    {submission.status}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getInquiryTypeColor(submission.inquiryType)}`}>
                    {submission.inquiryType}
                  </span>
                </div>
              </div>

              <p className="text-gray-700 mb-3 line-clamp-2">{submission.message}</p>

              <div className="flex justify-between items-center">
                <div className="flex items-center text-sm text-gray-500">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  <span>{new Date(submission.createdAt).toLocaleString()}</span>
                </div>
                <div className="flex space-x-2">
                  {submission.status === 'pending' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        updateStatus(submission.submissionId, 'contacted');
                      }}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                    >
                      Mark Contacted
                    </button>
                  )}
                  {submission.status === 'contacted' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        updateStatus(submission.submissionId, 'resolved');
                      }}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                    >
                      Mark Resolved
                    </button>
                  )}
                  {submission.status === 'resolved' && (
                    <div className="flex items-center text-green-600 text-sm">
                      <CheckCircleIcon className="h-4 w-4 mr-1" />
                      <span>Resolved</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedSubmission && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setSelectedSubmission(null)}
        >
          <div
            className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-2xl font-semibold text-gray-900">Submission Details</h3>
              <button
                onClick={() => setSelectedSubmission(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Name</label>
                <p className="text-gray-900">{selectedSubmission.name}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Email</label>
                <p className="text-gray-900">{selectedSubmission.email}</p>
              </div>

              {selectedSubmission.phone && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Phone</label>
                  <p className="text-gray-900">{selectedSubmission.phone}</p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-gray-500">Inquiry Type</label>
                <p className="text-gray-900 capitalize">{selectedSubmission.inquiryType}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Message</label>
                <p className="text-gray-900 whitespace-pre-wrap">{selectedSubmission.message}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Status</label>
                <p className="text-gray-900 capitalize">{selectedSubmission.status}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Submitted</label>
                  <p className="text-gray-900">{new Date(selectedSubmission.createdAt).toLocaleString()}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Last Updated</label>
                  <p className="text-gray-900">{new Date(selectedSubmission.updatedAt).toLocaleString()}</p>
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                {selectedSubmission.status !== 'resolved' && (
                  <>
                    {selectedSubmission.status === 'pending' && (
                      <button
                        onClick={() => {
                          updateStatus(selectedSubmission.submissionId, 'contacted');
                          setSelectedSubmission({ ...selectedSubmission, status: 'contacted' });
                        }}
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Mark as Contacted
                      </button>
                    )}
                    {selectedSubmission.status === 'contacted' && (
                      <button
                        onClick={() => {
                          updateStatus(selectedSubmission.submissionId, 'resolved');
                          setSelectedSubmission({ ...selectedSubmission, status: 'resolved' });
                        }}
                        className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Mark as Resolved
                      </button>
                    )}
                  </>
                )}
                <a
                  href={`mailto:${selectedSubmission.email}`}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-center"
                >
                  Send Email
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContactSubmissions;
