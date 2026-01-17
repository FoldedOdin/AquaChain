import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Package, 
  Truck, 
  MapPin, 
  Clock, 
  CheckCircle, 
  XCircle,
  ExternalLink,
  AlertCircle,
  Wrench
} from 'lucide-react';
import { getShipmentByOrderId } from '../../services/shipmentService';
import { websocketService } from '../../services/websocketService';
import Toast from '../Toast/Toast';
import { 
  Shipment, 
  ShipmentProgress,
  STATUS_ICONS,
  STATUS_LABELS,
  COURIER_CONTACTS
} from '../../types/shipment';

interface ShipmentTrackingProps {
  orderId: string;
  orderStatus: string;
}

const ShipmentTracking: React.FC<ShipmentTrackingProps> = ({ orderId, orderStatus }) => {
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [progress, setProgress] = useState<ShipmentProgress | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info'; visible: boolean }>({
    message: '',
    type: 'info',
    visible: false
  });

  const showToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    setToast({ message, type, visible: true });
  };

  const hideToast = () => {
    setToast(prev => ({ ...prev, visible: false }));
  };

  // Fetch shipment data
  const fetchShipmentData = async () => {
    // Only fetch if order is shipped or beyond
    if (!['shipped', 'installing', 'completed'].includes(orderStatus)) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await getShipmentByOrderId(orderId);
      
      if (response.success && response.shipment) {
        setShipment(response.shipment);
        setProgress(response.progress);
      }
    } catch (err) {
      console.error('Error fetching shipment:', err);
      setError('Unable to load shipment tracking information');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchShipmentData();
  }, [orderId, orderStatus]);

  // WebSocket real-time updates
  useEffect(() => {
    if (!shipment) return;

    // Subscribe to shipment updates for this order
    const topic = `shipment-updates-${orderId}`;
    
    const handleShipmentUpdate = (data: any) => {
      console.log('Received shipment update:', data);
      
      // Ignore non-update messages
      if (data.type !== 'shipment_update') return;

      // Check if this update is for our shipment
      if (data.order_id !== orderId && data.shipment_id !== shipment.shipment_id) return;

      // Refresh shipment data
      fetchShipmentData();

      // Show toast notification for important status changes
      const importantStatuses = ['out_for_delivery', 'delivered', 'delivery_failed'];
      if (importantStatuses.includes(data.new_status)) {
        const statusMessages: Record<string, string> = {
          out_for_delivery: '🚛 Your package is out for delivery!',
          delivered: '✅ Your package has been delivered!',
          delivery_failed: '❌ Delivery attempt failed. We\'ll retry soon.'
        };
        
        showToast(statusMessages[data.new_status] || 'Shipment status updated', 'info');
      }
    };

    // Connect to WebSocket
    websocketService.connect(topic, handleShipmentUpdate);

    // Cleanup on unmount
    return () => {
      websocketService.disconnect(topic, handleShipmentUpdate);
    };
  }, [shipment, orderId]);

  // Don't show anything if order hasn't been shipped yet
  if (!['shipped', 'installing', 'completed'].includes(orderStatus)) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Shipment Tracking</h3>
        <div className="bg-gray-50 rounded-lg p-6 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mx-auto mb-2"></div>
          <p className="text-sm text-gray-600">Loading shipment information...</p>
        </div>
      </div>
    );
  }

  if (error || !shipment) {
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Shipment Tracking</h3>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-900">
              <p className="font-semibold mb-1">Tracking Information Unavailable</p>
              <p>{error || 'Shipment tracking will be available once the package is dispatched.'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const courierContact = COURIER_CONTACTS[shipment.courier_name];
  const trackingUrl = courierContact ? `${courierContact.tracking_url}${shipment.tracking_number}` : null;

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get status color
  const getStatusColor = () => {
    if (!progress) return 'bg-gray-500';
    
    switch (progress.status_color) {
      case 'blue': return 'bg-blue-500';
      case 'green': return 'bg-green-500';
      case 'red': return 'bg-red-500';
      case 'orange': return 'bg-orange-500';
      case 'gray': return 'bg-gray-500';
      default: return 'bg-cyan-500';
    }
  };

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Shipment Tracking</h3>
      
      {/* Delivery Confirmation Banner */}
      {shipment.internal_status === 'delivered' && shipment.delivered_at && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 mb-4 border-2 border-green-300"
        >
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                <CheckCircle className="w-7 h-7 text-white" />
              </div>
            </div>
            <div className="flex-1">
              <h4 className="text-lg font-bold text-green-900 mb-1">✅ Package Delivered!</h4>
              <p className="text-sm text-green-800 mb-2">
                Your device was successfully delivered on <span className="font-semibold">{formatDate(shipment.delivered_at)}</span>
              </p>
              <div className="bg-white rounded-lg p-3 border border-green-200">
                <div className="flex items-center gap-2 text-sm">
                  <Wrench className="w-4 h-4 text-cyan-600" />
                  <span className="font-semibold text-gray-900">Installation Ready</span>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Your device is ready for installation. Our technician will contact you shortly to schedule the installation.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}
      
      {/* Shipment Header */}
      <div className="bg-gradient-to-r from-cyan-50 to-blue-50 rounded-lg p-4 mb-4 border border-cyan-200">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Truck className="w-5 h-5 text-cyan-600" />
              <span className="font-semibold text-gray-900">
                {shipment.courier_name} - {shipment.courier_service_type}
              </span>
              {shipment.internal_status === 'delivered' && (
                <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
                  Delivered
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Package className="w-4 h-4" />
              <span>Tracking: <span className="font-mono font-semibold">{shipment.tracking_number}</span></span>
            </div>
          </div>
          
          {trackingUrl && (
            <a
              href={trackingUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors text-sm"
            >
              <span>Track Package</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>

        {/* Progress Bar */}
        {progress && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">{progress.status_message}</span>
              <span className="text-sm font-semibold text-gray-900">{progress.percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress.percentage}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className={`h-2.5 rounded-full ${getStatusColor()}`}
              />
            </div>
          </div>
        )}

        {/* Estimated Delivery */}
        {shipment.estimated_delivery && shipment.internal_status !== 'delivered' && (
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-gray-600" />
            <span className="text-gray-700">
              Estimated Delivery: <span className="font-semibold">{formatDate(shipment.estimated_delivery)}</span>
            </span>
          </div>
        )}

        {/* Delivered At */}
        {shipment.delivered_at && (
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span className="text-gray-700">
              Delivered: <span className="font-semibold text-green-600">{formatDate(shipment.delivered_at)}</span>
            </span>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-4">Shipment Timeline</h4>
        
        <div className="relative">
          {shipment.timeline.map((event, index) => {
            const isLast = index === shipment.timeline.length - 1;
            const icon = STATUS_ICONS[event.status as keyof typeof STATUS_ICONS] || '📦';
            const label = STATUS_LABELS[event.status as keyof typeof STATUS_LABELS] || event.status;
            
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start mb-4 last:mb-0"
              >
                {/* Timeline Line */}
                <div className="flex flex-col items-center mr-4">
                  <div className="w-10 h-10 rounded-full bg-cyan-100 flex items-center justify-center text-xl">
                    {icon}
                  </div>
                  {!isLast && (
                    <div className="w-0.5 h-full min-h-[40px] bg-gray-300 mt-2" />
                  )}
                </div>

                {/* Event Details */}
                <div className="flex-1 pt-2">
                  <div className="flex items-start justify-between mb-1">
                    <p className="font-semibold text-gray-900">{label}</p>
                    <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                      {formatDate(event.timestamp)}
                    </span>
                  </div>
                  
                  {event.location && (
                    <div className="flex items-center gap-1 text-sm text-gray-600 mb-1">
                      <MapPin className="w-3 h-3" />
                      <span>{event.location}</span>
                    </div>
                  )}
                  
                  {event.description && (
                    <p className="text-sm text-gray-600">{event.description}</p>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Empty Timeline */}
        {shipment.timeline.length === 0 && (
          <div className="text-center py-6 text-gray-500">
            <Package className="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <p className="text-sm">No tracking updates available yet</p>
          </div>
        )}
      </div>

      {/* Courier Contact Info */}
      {courierContact && (
        <div className="mt-4 bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs font-semibold text-gray-700 mb-2">Need Help?</p>
          <div className="flex items-center gap-4 text-xs text-gray-600">
            <span>📞 {courierContact.phone}</span>
            <span>✉️ {courierContact.email}</span>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.visible}
        onClose={hideToast}
      />
    </div>
  );
};

export default ShipmentTracking;
