import { useState, useEffect, useMemo, useCallback } from 'react';
import { ShipmentListItem, STATUS_COLORS, STATUS_LABELS, STATUS_ICONS } from '../../types/shipment';
import { getAllShipments, formatDate } from '../../services/shipmentService';

interface ShipmentsListProps {
  onShipmentClick: (shipmentId: string) => void;
}

const ShipmentsList: React.FC<ShipmentsListProps> = ({ onShipmentClick }) => {
  const [shipments, setShipments] = useState<ShipmentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch shipments
  const fetchShipments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAllShipments();
      setShipments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load shipments');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchShipments();
  }, [fetchShipments]);

  // Filter shipments
  const filteredShipments = useMemo(() => {
    return shipments.filter(shipment => {
      // Status filter
      if (statusFilter !== 'all' && shipment.internal_status !== statusFilter) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          shipment.tracking_number.toLowerCase().includes(query) ||
          shipment.order_id.toLowerCase().includes(query) ||
          shipment.destination.contact_name.toLowerCase().includes(query)
        );
      }

      return true;
    });
  }, [shipments, statusFilter, searchQuery]);

  // Count shipments by status
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: shipments.length,
      in_transit: 0,
      delivered: 0,
      delivery_failed: 0,
      delayed: 0
    };

    shipments.forEach(shipment => {
      if (shipment.internal_status === 'in_transit' || 
          shipment.internal_status === 'picked_up' || 
          shipment.internal_status === 'out_for_delivery') {
        counts.in_transit++;
      }
      if (shipment.internal_status === 'delivered') {
        counts.delivered++;
      }
      if (shipment.internal_status === 'delivery_failed') {
        counts.delivery_failed++;
      }
      if (shipment.is_delayed) {
        counts.delayed++;
      }
    });

    return counts;
  }, [shipments]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading shipments...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Shipments</h3>
        <p className="text-red-700">{error}</p>
        <button
          onClick={fetchShipments}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Shipments</h2>
          <button
            onClick={fetchShipments}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Search */}
        <div className="mb-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by tracking number, order ID, or customer name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg
              className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        {/* Status Filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({statusCounts.all})
          </button>
          <button
            onClick={() => setStatusFilter('in_transit')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === 'in_transit'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            In Transit ({statusCounts.in_transit})
          </button>
          <button
            onClick={() => setStatusFilter('delivered')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === 'delivered'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Delivered ({statusCounts.delivered})
          </button>
          <button
            onClick={() => setStatusFilter('delivery_failed')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === 'delivery_failed'
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Failed ({statusCounts.delivery_failed})
          </button>
          {statusCounts.delayed > 0 && (
            <div className="px-4 py-2 rounded-lg text-sm font-medium bg-red-100 text-red-800">
              ⚠️ {statusCounts.delayed} Delayed
            </div>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tracking Number
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Order ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Customer
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Courier
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Est. Delivery
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredShipments.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                  {searchQuery || statusFilter !== 'all'
                    ? 'No shipments match your filters'
                    : 'No shipments found'}
                </td>
              </tr>
            ) : (
              filteredShipments.map((shipment) => (
                <tr
                  key={shipment.shipment_id}
                  className={`hover:bg-gray-50 transition-colors ${
                    shipment.is_delayed ? 'bg-red-50' : ''
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-900">
                        {shipment.tracking_number}
                      </span>
                      {shipment.is_delayed && (
                        <span className="ml-2 text-red-600" title="Delayed">
                          ⚠️
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {shipment.order_id}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      {shipment.destination.contact_name}
                    </div>
                    <div className="text-xs text-gray-500 truncate max-w-xs">
                      {shipment.destination.address}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {shipment.courier_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        STATUS_COLORS[shipment.internal_status]
                      }`}
                    >
                      <span className="mr-1">{STATUS_ICONS[shipment.internal_status]}</span>
                      {STATUS_LABELS[shipment.internal_status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {formatDate(shipment.estimated_delivery)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => onShipmentClick(shipment.shipment_id)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      {filteredShipments.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <p className="text-sm text-gray-600">
            Showing {filteredShipments.length} of {shipments.length} shipments
          </p>
        </div>
      )}
    </div>
  );
};

export default ShipmentsList;
