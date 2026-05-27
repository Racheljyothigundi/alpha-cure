import React, { useState, useEffect } from 'react';
import {
  Brain, Activity, FileText, MessageCircle, MapPin,
  Star, Navigation, Clock, Loader, Building2
} from 'lucide-react';
import Sidebar from '../components/common/Sidebar';
import api from '../services/api';
import toast from 'react-hot-toast';

const NAV = [
  { to: '/dashboard', icon: Activity, label: 'Dashboard' },
  { to: '/predict', icon: Brain, label: 'Cancer Detection' },
  { to: '/reports', icon: FileText, label: 'My Reports' },
  { to: '/chat', icon: MessageCircle, label: 'Chat & Consult' },
  { to: '/hospitals', icon: MapPin, label: 'Nearby Hospitals' },
  { to: '/profile', icon: Activity, label: 'My Profile' },
];

export default function HospitalsPage() {
  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState('hospital');
  const [locationError, setLocationError] = useState(null);
  const [coords, setCoords] = useState(null);

  const fetchNearby = (lat, lng, t) => {
    setLoading(true);
    api.get(`/hospitals/nearby?lat=${lat}&lng=${lng}&type=${t}`)
      .then(r => setPlaces(r.data.places || []))
      .catch(err => {
        setPlaces([]);
        const data = err.response?.data;
        if (data?.code === 'MAPS_KEY_MISSING') {
          toast.error('Google Maps is not configured. Add GOOGLE_MAPS_API_KEY to backend/.env and restart the server.');
        } else {
          toast.error(data?.error || 'Failed to fetch nearby places');
        }
      })
      .finally(() => setLoading(false));
  };

  const getLocation = () => {
    setLocationError(null);
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported by your browser');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        const { latitude: lat, longitude: lng } = pos.coords;
        setCoords({ lat, lng });
        fetchNearby(lat, lng, type);
      },
      () => {
        const lat = 28.6139, lng = 77.2090;
        setCoords({ lat, lng });
        fetchNearby(lat, lng, type);
        toast('Using default location: New Delhi', { icon: '📍' });
      }
    );
  };

  useEffect(() => {
    getLocation();
  }, []);

  const switchType = (t) => {
    setType(t);
    if (coords) fetchNearby(coords.lat, coords.lng, t);
  };

  const openInMaps = (place) => {
    let url;
    if (place.lat != null && place.lng != null) {
      url = `https://www.google.com/maps/search/?api=1&query=${place.lat},${place.lng}`;
      if (place.place_id) url += `&query_place_id=${place.place_id}`;
    } else {
      url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name)}`;
    }
    window.open(url, '_blank');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar navItems={NAV} role="patient" />
      <main className="lg:ml-64 pt-14 lg:pt-0">
        <div className="max-w-5xl mx-auto p-6 space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Nearby Facilities</h1>
            <p className="text-slate-500 text-sm mt-1">Find cancer hospitals and vaccination centers near you</p>
          </div>

          {/* Type Toggle */}
          <div className="flex gap-3 flex-wrap">
            <div className="flex gap-2 p-1 bg-white rounded-xl border border-slate-200 shadow-sm">
              {[
                { id: 'hospital', label: '🏥 Cancer Hospitals' },
                { id: 'vaccination', label: '💉 Vaccination Centers' }
              ].map(({ id, label }) => (
                <button key={id} onClick={() => switchType(id)}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                    type === id ? 'bg-primary-600 text-white shadow-sm' : 'text-slate-600 hover:text-primary-600'
                  }`}>
                  {label}
                </button>
              ))}
            </div>
            <button onClick={getLocation} disabled={loading}
              className="btn-primary">
              {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Navigation className="w-4 h-4" />}
              {coords ? 'Refresh' : 'Find Near Me'}
            </button>
          </div>

          {locationError && (
            <p className="text-sm text-red-600">{locationError}</p>
          )}

          {/* No location yet */}
          {!coords && !loading && (
            <div className="card text-center py-16">
              <MapPin className="w-12 h-12 text-slate-200 mx-auto mb-4" />
              <h3 className="font-semibold text-slate-700 mb-2">Find Nearby {type === 'hospital' ? 'Hospitals' : 'Vaccination Centers'}</h3>
              <p className="text-sm text-slate-400 mb-6">Allow location access to discover certified facilities near you</p>
              <button onClick={getLocation} className="btn-primary mx-auto">
                <Navigation className="w-4 h-4" /> Enable Location
              </button>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="card flex items-center justify-center py-16">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-primary-100 border-t-primary-500 rounded-full animate-spin mx-auto mb-4" />
                <p className="text-slate-500 text-sm">Searching nearby facilities...</p>
              </div>
            </div>
          )}

          {/* Empty results */}
          {!loading && coords && places.length === 0 && (
            <div className="card text-center py-16">
              <Building2 className="w-12 h-12 text-slate-200 mx-auto mb-4" />
              <h3 className="font-semibold text-slate-700 mb-2">No facilities found</h3>
              <p className="text-sm text-slate-400 mb-6">
                No {type === 'hospital' ? 'cancer hospitals' : 'vaccination centers'} were found within 10 km. Try refreshing or a different area.
              </p>
              <button onClick={getLocation} className="btn-primary mx-auto">
                <Navigation className="w-4 h-4" /> Search Again
              </button>
            </div>
          )}

          {/* Results */}
          {!loading && places.length > 0 && (
            <>
              <p className="text-sm text-slate-500">{places.length} {type === 'hospital' ? 'cancer hospitals' : 'vaccination centers'} found near you</p>
              <div className="grid sm:grid-cols-2 gap-4">
                {places.map((place, i) => (
                  <div key={i} className="card hover:shadow-card-hover transition-all duration-200">
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center flex-shrink-0">
                        <Building2 className="w-5 h-5 text-primary-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-slate-900 leading-snug">{place.name}</p>
                        <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                          <MapPin className="w-3 h-3 flex-shrink-0" />
                          <span className="truncate">{place.address}</span>
                        </p>
                      </div>
                      {place.distance_km != null && (
                        <span className="text-xs font-medium text-primary-700 bg-primary-50 px-2 py-1 rounded-full flex-shrink-0">
                          {place.distance_km} km
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 mb-4">
                      {place.rating && (
                        <span className="flex items-center gap-1 text-sm text-amber-600">
                          <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                          <strong>{place.rating}</strong>
                        </span>
                      )}
                      <span className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium ${
                        place.open_now === true ? 'bg-green-50 text-green-700' :
                        place.open_now === false ? 'bg-red-50 text-red-700' : 'bg-slate-50 text-slate-500'
                      }`}>
                        <Clock className="w-3 h-3" />
                        {place.open_now === true ? 'Open Now' : place.open_now === false ? 'Closed' : 'Hours Unknown'}
                      </span>
                    </div>

                    <button onClick={() => openInMaps(place)}
                      className="btn-secondary w-full justify-center text-sm py-2">
                      <Navigation className="w-4 h-4" /> Get Directions
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Info card */}
          <div className="rounded-2xl bg-teal-50 border border-teal-100 p-5">
            <p className="font-semibold text-teal-900 mb-1">🗺️ Location Privacy</p>
            <p className="text-sm text-teal-700 leading-relaxed">
              Your location is only used to search for nearby facilities and is never stored on our servers.
              Results are provided by Google Maps Places API.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
