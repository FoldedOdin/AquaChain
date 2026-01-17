import { useState, useEffect } from 'react';
import { ShipmentListItem } from '../../types/shipment';
import { getStaleShipments, daysSinceUpdate, formatDate } from '../../services/shipmentService';

interface StaleShipmentsAlertProps {
  onInvestigate: (shipmentId: string) => void;
}

const StaleShipmentsAlert: React.FC<StaleShipmentsAlertProps> = ({ onInvestigate }) => {
  const [staleShipments, setStaleShipments] = useState<ShipmentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const fetchStaleShipments = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getStaleShipments();
        setStaleShipments(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stale shipments');
      } finally {
        setLoading(false);
      }
    };

    fetchStaleShipments();
    
    // Refresh every 5 minutes
    const interval = setInterval(fetchStaleShipments, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm">{error}</p>
      </div>
    );
  }

  if (staleShipments.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-green-800 font-medium">No stale shipments</p>
        </div>
        <p className="text-green-700 text-sm mt-1 ml-7">All shipments are being tracked normally</p>
      </div>
    );
  }

  return (
    <div className="bg-yellow-50 border border-yellow-300 rounded-lg shadow-sm">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-6 h-6 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h3 className="text-lg font-semibold text-yellow-900">
                Stale Shipments Alert
              </h3>
              <p className="text-sm text-yellow-700">
                {staleShipments.length} shipment{staleShipments.length !== 1 ? 's' : ''} with no updates for 7+ days
              </p>
            </div>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-yellow-700 hover:text-yellow-900 transition-colors"
          >
            <svg
              className={`w-5 h-5 transform transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Expanded List */}
      {expanded && (
        <div className="border-t border-yellow-300">
          <div className="p-4 space-y-3">
            {staleShipments.map((shipment) => {
              const daysSince = daysSinceUpdate(shipment.updated_at);
              
              return (
                <div
                  key={shipment.shipment_id}
                  className="bg-white rounded-lg border border-yellow-200 p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          {shipment.tracking_number}
                        </span>
                        <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full">
                          {daysSince} days stale
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>
                          <span className="font-medium">Order:</span> {shipment.order_id}
                        </p>
                        <p>
                          <span className="font-medium">Customer:</span> {shipment.destination.contact_name}
                        </p>
                        <p>
                          <span className="font-medium">Courier:</span> {shipment.courier_name}
                        </p>
                        <p>
                          <span className="font-medium">Last Update:</span> {formatDate(shipment.updated_at)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => onInvestigate(shipment.shipment_id)}
                      className="ml-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium whitespace-nowrap"
                    >
                      🔍 Investigate
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Quick Stats */}
      {!expanded && staleShipments.length > 0 && (
        <div className="px-4 pb-4">
          <button
            onClick={() => setExpanded(true)}
            className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium"
          >
            View All Stale Shipments
          </button>
        </div>
      )}
    </div>
  );
};

export default StaleShipmentsAlert;
