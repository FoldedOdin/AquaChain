import { useState } from 'react';
import ShipmentsList from './ShipmentsList';
import ShipmentDetailsModal from './ShipmentDetailsModal';
import StaleShipmentsAlert from './StaleShipmentsAlert';

const ShipmentTracking: React.FC = () => {
  const [selectedShipmentId, setSelectedShipmentId] = useState<string | null>(null);

  const handleShipmentClick = (shipmentId: string) => {
    setSelectedShipmentId(shipmentId);
  };

  const handleCloseModal = () => {
    setSelectedShipmentId(null);
  };

  return (
    <div className="space-y-6">
      {/* Stale Shipments Alert */}
      <StaleShipmentsAlert onInvestigate={handleShipmentClick} />

      {/* Shipments List */}
      <ShipmentsList onShipmentClick={handleShipmentClick} />

      {/* Shipment Details Modal */}
      {selectedShipmentId && (
        <ShipmentDetailsModal
          shipmentId={selectedShipmentId}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default ShipmentTracking;
