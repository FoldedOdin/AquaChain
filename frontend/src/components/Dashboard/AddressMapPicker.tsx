import React, { useState, useCallback, useEffect, useRef } from 'react';
import { MapPin, Search, Navigation, X } from 'lucide-react';

interface AddressMapPickerProps {
  onAddressSelect: (address: {
    formatted: string;
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
    latitude: number;
    longitude: number;
  }) => void;
  initialAddress?: string;
  initialLat?: number;
  initialLng?: number;
}

const AddressMapPicker: React.FC<AddressMapPickerProps> = ({
  onAddressSelect,
  initialAddress = '',
  initialLat = 10.8505,
  initialLng = 76.2711
}) => {
  const [searchQuery, setSearchQuery] = useState(initialAddress);
  const [selectedAddress, setSelectedAddress] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [mapCenter, setMapCenter] = useState({ lat: initialLat, lng: initialLng });
  const [markerPosition, setMarkerPosition] = useState({ lat: initialLat, lng: initialLng });
  const [isLoadingLocation, setIsLoadingLocation] = useState(false);
  
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const autocompleteService = useRef<any>(null);
  const geocoder = useRef<any>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);

  // Initialize Google Maps
  useEffect(() => {
    const initMap = () => {
      if (!window.google || !mapContainerRef.current) return;

      // Create map
      const map = new window.google.maps.Map(mapContainerRef.current, {
        center: mapCenter,
        zoom: 15,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        zoomControl: true,
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ]
      });

      // Create draggable marker
      const marker = new window.google.maps.Marker({
        position: markerPosition,
        map: map,
        draggable: true,
        animation: window.google.maps.Animation.DROP,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: '#3B82F6',
          fillOpacity: 1,
          strokeColor: '#FFFFFF',
          strokeWeight: 2
        }
      });

      // Handle marker drag
      marker.addListener('dragend', () => {
        const position = marker.getPosition();
        if (position) {
          const lat = position.lat();
          const lng = position.lng();
          setMarkerPosition({ lat, lng });
          reverseGeocode(lat, lng);
        }
      });

      // Handle map click
      map.addListener('click', (e: any) => {
        const lat = e.latLng.lat();
        const lng = e.latLng.lng();
        marker.setPosition(e.latLng);
        setMarkerPosition({ lat, lng });
        reverseGeocode(lat, lng);
      });

      mapRef.current = map;
      markerRef.current = marker;
      autocompleteService.current = new window.google.maps.places.AutocompleteService();
      geocoder.current = new window.google.maps.Geocoder();
    };

    // Load Google Maps script
    if (!window.google) {
      const script = document.createElement('script');
      const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || '';
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = initMap;
      document.head.appendChild(script);
    } else {
      initMap();
    }
  }, []);

  // Update map when center changes
  useEffect(() => {
    if (mapRef.current) {
      mapRef.current.setCenter(mapCenter);
      if (markerRef.current) {
        markerRef.current.setPosition(markerPosition);
      }
    }
  }, [mapCenter, markerPosition]);

  // Reverse geocode to get address from coordinates
  const reverseGeocode = useCallback(async (lat: number, lng: number) => {
    if (!geocoder.current) return;

    try {
      const response = await geocoder.current.geocode({
        location: { lat, lng }
      });

      if (response.results && response.results[0]) {
        const result = response.results[0];
        const address = parseGoogleAddress(result);
        setSelectedAddress(address);
        setSearchQuery(address.formatted);
      }
    } catch (error) {
      console.error('Reverse geocoding error:', error);
    }
  }, []);

  // Parse Google address components
  const parseGoogleAddress = (result: any) => {
    const components = result.address_components;
    const address: any = {
      formatted: result.formatted_address,
      street: '',
      city: '',
      state: '',
      zipCode: '',
      country: '',
      latitude: result.geometry.location.lat(),
      longitude: result.geometry.location.lng()
    };

    components.forEach((component: any) => {
      const types = component.types;
      if (types.includes('street_number')) {
        address.street = component.long_name + ' ';
      }
      if (types.includes('route')) {
        address.street += component.long_name;
      }
      if (types.includes('locality')) {
        address.city = component.long_name;
      }
      if (types.includes('administrative_area_level_1')) {
        address.state = component.long_name;
      }
      if (types.includes('postal_code')) {
        address.zipCode = component.long_name;
      }
      if (types.includes('country')) {
        address.country = component.long_name;
      }
    });

    return address;
  };

  // Search for address
  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);

    if (!query || query.length < 3 || !autocompleteService.current) {
      setSuggestions([]);
      return;
    }

    setIsSearching(true);

    try {
      const response = await autocompleteService.current.getPlacePredictions({
        input: query,
        componentRestrictions: { country: 'in' } // Restrict to India
      });

      setSuggestions(response.predictions || []);
    } catch (error) {
      console.error('Autocomplete error:', error);
      setSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Select address from suggestions
  const handleSelectSuggestion = useCallback(async (placeId: string) => {
    if (!geocoder.current) return;

    try {
      const response = await geocoder.current.geocode({ placeId });

      if (response.results && response.results[0]) {
        const result = response.results[0];
        const address = parseGoogleAddress(result);
        const location = result.geometry.location;

        setSelectedAddress(address);
        setSearchQuery(address.formatted);
        setMapCenter({ lat: location.lat(), lng: location.lng() });
        setMarkerPosition({ lat: location.lat(), lng: location.lng() });
        setSuggestions([]);
      }
    } catch (error) {
      console.error('Geocoding error:', error);
    }
  }, []);

  // Get current location
  const handleGetCurrentLocation = useCallback(() => {
    setIsLoadingLocation(true);

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          setMapCenter({ lat, lng });
          setMarkerPosition({ lat, lng });
          reverseGeocode(lat, lng);
          setIsLoadingLocation(false);
        },
        (error) => {
          console.error('Geolocation error:', error);
          alert('Unable to get your location. Please search for your address or click on the map.');
          setIsLoadingLocation(false);
        }
      );
    } else {
      alert('Geolocation is not supported by your browser.');
      setIsLoadingLocation(false);
    }
  }, [reverseGeocode]);

  // Confirm address selection
  const handleConfirm = useCallback(() => {
    if (selectedAddress) {
      onAddressSelect(selectedAddress);
    } else {
      alert('Please select an address on the map');
    }
  }, [selectedAddress, onAddressSelect]);

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search for your address..."
            className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSuggestions([]);
              }}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Suggestions Dropdown */}
        {suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion.place_id}
                onClick={() => handleSelectSuggestion(suggestion.place_id)}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition"
              >
                <div className="flex items-start gap-2">
                  <MapPin className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {suggestion.structured_formatting.main_text}
                    </p>
                    <p className="text-xs text-gray-500">
                      {suggestion.structured_formatting.secondary_text}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Current Location Button */}
      <button
        onClick={handleGetCurrentLocation}
        disabled={isLoadingLocation}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-blue-500 text-blue-600 rounded-lg hover:bg-blue-50 transition disabled:opacity-50"
      >
        <Navigation className="w-4 h-4" />
        {isLoadingLocation ? 'Getting location...' : 'Use Current Location'}
      </button>

      {/* Map Container */}
      <div className="relative">
        <div
          ref={mapContainerRef}
          className="w-full h-96 rounded-lg border-2 border-gray-300"
        />
        <div className="absolute top-4 left-4 bg-white px-3 py-2 rounded-lg shadow-md">
          <p className="text-xs text-gray-600 flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            Drag marker or click map to set location
          </p>
        </div>
      </div>

      {/* Selected Address Display */}
      {selectedAddress && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium text-gray-900 mb-1">Selected Address:</p>
              <p className="text-sm text-gray-700">{selectedAddress.formatted}</p>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-600">
                <div>
                  <span className="font-medium">City:</span> {selectedAddress.city}
                </div>
                <div>
                  <span className="font-medium">State:</span> {selectedAddress.state}
                </div>
                <div>
                  <span className="font-medium">ZIP:</span> {selectedAddress.zipCode}
                </div>
                <div>
                  <span className="font-medium">Coordinates:</span> {selectedAddress.latitude.toFixed(4)}, {selectedAddress.longitude.toFixed(4)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Button */}
      <button
        onClick={handleConfirm}
        disabled={!selectedAddress}
        className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        Confirm Address
      </button>
    </div>
  );
};

export default AddressMapPicker;
