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

  // Check if API key is configured
  const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
  const hasApiKey = apiKey && apiKey.length > 0;

  // Initialize Google Maps
  useEffect(() => {
    if (!hasApiKey) return; // Skip if no API key
    
    let mounted = true;
    
    const initMap = () => {
      if (!mounted) return;
      
      // Check if Google Maps is fully loaded
      if (!window.google?.maps?.Map || !window.google?.maps?.Marker || !mapContainerRef.current) {
        console.warn('Google Maps not fully ready yet, retrying...');
        setTimeout(initMap, 100);
        return;
      }

      try {
        console.log('Initializing Google Maps...');
        
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
        
        // Initialize services after map is created
        if (window.google?.maps?.places?.AutocompleteService) {
          autocompleteService.current = new window.google.maps.places.AutocompleteService();
        }
        if (window.google?.maps?.Geocoder) {
          geocoder.current = new window.google.maps.Geocoder();
        }
        
        console.log('Google Maps initialized successfully');
      } catch (error) {
        console.error('Error initializing Google Maps:', error);
      }
    };

    // Check if script is already loaded
    const existingScript = document.querySelector('script[src*="maps.googleapis.com"]');
    
    if (existingScript) {
      // Script already exists, wait for it to load
      if (window.google?.maps) {
        initMap();
      } else {
        // Wait for existing script to load
        const checkInterval = setInterval(() => {
          if (window.google?.maps) {
            clearInterval(checkInterval);
            initMap();
          }
        }, 100);
        
        // Cleanup interval after 10 seconds
        setTimeout(() => clearInterval(checkInterval), 10000);
      }
    } else {
      // Load new script
      const script = document.createElement('script');
      const callbackName = `initGoogleMaps_${Date.now()}`;
      
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=${callbackName}`;
      script.async = true;
      script.defer = true;
      
      // Set up callback
      (window as any)[callbackName] = () => {
        console.log('Google Maps script loaded');
        if (mounted) {
          setTimeout(initMap, 200); // Give it a bit more time
        }
        delete (window as any)[callbackName];
      };
      
      script.onerror = () => {
        console.error('Failed to load Google Maps script');
        delete (window as any)[callbackName];
      };
      
      document.head.appendChild(script);
    }

    // Cleanup
    return () => {
      mounted = false;
    };
  }, [hasApiKey, apiKey]);

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

  // Show setup message if no API key
  if (!hasApiKey) {
    return (
      <div className="bg-amber-50 border-2 border-amber-200 rounded-lg p-6">
        <div className="flex items-start gap-3 mb-4">
          <MapPin className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-amber-900 mb-2">Google Maps Not Configured</h3>
            <p className="text-sm text-amber-800 mb-3">
              To use the interactive map for address selection, you need to add a Google Maps API key.
            </p>
            <div className="bg-white rounded p-3 mb-3">
              <p className="text-xs font-mono text-gray-700">
                REACT_APP_GOOGLE_MAPS_API_KEY=your-key-here
              </p>
            </div>
            <p className="text-xs text-amber-700">
              See <code className="bg-amber-100 px-1 rounded">GOOGLE_MAPS_QUICK_SETUP.md</code> for setup instructions (takes 5 minutes).
            </p>
          </div>
        </div>
        <button
          onClick={() => onAddressSelect({
            formatted: searchQuery,
            street: searchQuery,
            city: '',
            state: '',
            zipCode: '',
            country: 'India',
            latitude: 10.8505,
            longitude: 76.2711
          })}
          disabled={!searchQuery.trim()}
          className="w-full px-4 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          Use Text Address (Without Map)
        </button>
      </div>
    );
  }

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
