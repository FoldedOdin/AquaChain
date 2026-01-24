import { useState, useEffect } from 'react';
import {
  Shipment,
  ShipmentStatusResponse,
  STATUS_COLORS,
  STATUS_LABELS,
  STATUS_ICONS,
  COURIER_CONTACTS
} from '../../types/shipment';
import { getShipmentById, formatDate } from '../../services/shipmentService';

interface ShipmentDetailsModalProps {
  shipmentId: string;
  onClose: () => void;
}

const ShipmentDetailsModal: React.FC<ShipmentDetailsModalProps> = ({ shipmentId, onClose }) => {
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [progress, setProgress] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'webhooks'>('timeline');

  useEffect(() => {
    const fetchShipmentDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        const response: ShipmentStatusResponse = await getShipmentById(shipmentId);
        setShipment(response.shipment);
        setProgress(response.progress);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load shipment details');
      } finally {
        setLoading(false);
      }
    };

    fetchShipmentDetails();
  }, [shipmentId]);

  const courierContact = shipment ? COURIER_CONTACTS[shipment.courier_name] : null;

  const handleContactCourier = () => {
    if (courierContact) {
      window.open(`tel:${courierContact.phone}`);
    }
  };

  const handleTrackOnCourierSite = () => {
    if (courierContact && shipment) {
      window.open(`${courierContact.tracking_url}${shipment.tracking_number}`, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Shipment Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading shipment details...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-red-800 font-semibold mb-2">Error</h3>
              <p className="text-red-700">{error}</p>
            </div>
          ) : shipment ? (
            <div className="space-y-6">
              {/* Shipment Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Tracking Number</h3>
                  <p className="text-lg font-semibold text-gray-900">{shipment.tracking_number}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Order ID</h3>
                  <p className="text-lg font-semibold text-gray-900">{shipment.order_id}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Courier</h3>
                  <p className="text-lg font-semibold text-gray-900">
                    {shipment.courier_name} ({shipment.courier_service_type})
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Status</h3>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                      STATUS_COLORS[shipment.internal_status]
                    }`}
                  >
                    <span className="mr-1">{STATUS_ICONS[shipment.internal_status]}</span>
                    {STATUS_LABELS[shipment.internal_status]}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              {progress && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-gray-500">Delivery Progress</h3>
                    <span className="text-sm font-medium text-gray-900">{progress.percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        progress.status_color === 'green'
                          ? 'bg-green-500'
                          : progress.status_color === 'blue'
                          ? 'bg-blue-500'
                          : progress.status_color === 'yellow'
                          ? 'bg-yellow-500'
                          : progress.status_color === 'red'
                          ? 'bg-red-500'
                          : 'bg-gray-500'
                      }`}
                      style={{ width: `${progress.percentage}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{progress.status_message}</p>
                </div>
              )}

              {/* Destination */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Destination</h3>
                <p className="text-gray-900 font-medium">{shipment.destination.contact_name}</p>
                <p className="text-gray-700">{shipment.destination.contact_phone}</p>
                <p className="text-gray-700">{shipment.destination.address}</p>
                <p className="text-gray-700">PIN: {shipment.destination.pincode}</p>
              </div>

              {/* Delivery Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Estimated Delivery</h3>
                  <p className="text-gray-900">{formatDate(shipment.estimated_delivery)}</p>
                </div>
                {shipment.delivered_at && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Delivered At</h3>
                    <p className="text-gray-900">{formatDate(shipment.delivered_at)}</p>
                  </div>
                )}
                {shipment.failed_at && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Failed At</h3>
                    <p className="text-gray-900">{formatDate(shipment.failed_at)}</p>
                  </div>
                )}
              </div>

              {/* Retry Info */}
              {shipment.retry_config.retry_count > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-yellow-800 mb-2">Delivery Attempts</h3>
                  <p className="text-yellow-700">
                    Retry {shipment.retry_config.retry_count} of {shipment.retry_config.max_retries}
                  </p>
                  {shipment.retry_config.last_retry_at && (
                    <p className="text-sm text-yellow-600 mt-1">
                      Last attempt: {formatDate(shipment.retry_config.last_retry_at)}
                    </p>
                  )}
                </div>
              )}

              {/* Tabs */}
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-4">
                  <button
                    onClick={() => setActiveTab('timeline')}
                    className={`py-2 px-3 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'timeline'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Timeline ({shipment.timeline.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('webhooks')}
                    className={`py-2 px-3 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'webhooks'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Webhook History ({shipment.webhook_events.length})
                  </button>
                </nav>
              </div>

              {/* Timeline Tab */}
              {activeTab === 'timeline' && (
                <div className="space-y-4">
                  {shipment.timeline.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No timeline events yet</p>
                  ) : (
                    <div className="relative">
                      {/* Timeline line */}
                      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

                      {/* Timeline events */}
                      {shipment.timeline.map((event, index) => (
                        <div key={index} className="relative flex items-start mb-6 last:mb-0">
                          {/* Icon */}
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center z-10">
                            <span className="text-lg">{STATUS_ICONS[event.status as keyof typeof STATUS_ICONS] || '📍'}</span>
                          </div>

                          {/* Content */}
                          <div className="ml-4 flex-1">
                            <div className="bg-gray-50 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="font-medium text-gray-900">
                                  {STATUS_LABELS[event.status as keyof typeof STATUS_LABELS] || event.status}
                                </h4>
                                <span className="text-sm text-gray-500">
                                  {formatDate(event.timestamp)}
                                </span>
                              </div>
                              <p className="text-sm text-gray-700">{event.description}</p>
                              {event.location && (
                                <p className="text-sm text-gray-500 mt-1">📍 {event.location}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Webhooks Tab */}
              {activeTab === 'webhooks' && (
                <div className="space-y-3">
                  {shipment.webhook_events.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No webhook events yet</p>
                  ) : (
                    shipment.webhook_events.map((event, index) => (
                      <div key={index} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-900">
                            Event ID: {event.event_id}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatDate(event.received_at)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">
                          Courier Status: <span className="font-medium">{event.courier_status}</span>
                        </p>
                        <details className="text-sm">
                          <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                            View Raw Payload
                          </summary>
                          <pre className="mt-2 p-3 bg-gray-900 text-gray-100 rounded overflow-x-auto text-xs">
                            {JSON.stringify(JSON.parse(event.raw_payload || '{}'), null, 2)}
                          </pre>
                        </details>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Courier Contact */}
              {courierContact && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-blue-900 mb-3">Courier Contact</h3>
                  <div className="space-y-2 text-sm text-blue-800">
                    <p>
                      <span className="font-medium">Phone:</span> {courierContact.phone}
                    </p>
                    <p>
                      <span className="font-medium">Email:</span> {courierContact.email}
                    </p>
                  </div>
                  <div className="mt-4 flex gap-3">
                    <button
                      onClick={handleContactCourier}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                    >
                      📞 Call Courier
                    </button>
                    <button
                      onClick={handleTrackOnCourierSite}
                      className="px-4 py-2 bg-white border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-sm"
                    >
                      🔗 Track on Courier Site
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShipmentDetailsModal;
