"""controllers/hospital_controller.py"""

import math
import os
import requests
from flask import request, jsonify
from utils.jwt_utils import token_required

PLACES_NEARBY_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'


def _haversine_km(lat1, lng1, lat2, lng2):
    r = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@token_required
def get_nearby_hospitals():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    query_type = request.args.get('type', 'hospital')  # hospital or vaccination

    if not lat or not lng:
        return jsonify({'error': 'lat and lng parameters required'}), 400

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key or api_key == 'your_google_maps_key_here':
        return jsonify({
            'error': 'Google Maps API key is not configured. Add GOOGLE_MAPS_API_KEY to backend/.env and restart the server.',
            'code': 'MAPS_KEY_MISSING',
        }), 503

    try:
        user_lat = float(lat)
        user_lng = float(lng)
    except ValueError:
        return jsonify({'error': 'lat and lng must be valid numbers'}), 400

    keyword = (
        'cancer hospital oncology'
        if query_type == 'hospital'
        else 'vaccination center immunization'
    )
    params = {
        'location': f'{lat},{lng}',
        'radius': 10000,
        'keyword': keyword,
        'key': api_key,
    }
    if query_type == 'hospital':
        params['type'] = 'hospital'

    try:
        resp = requests.get(PLACES_NEARBY_URL, params=params, timeout=10)
        data = resp.json()
        status = data.get('status')
        if status == 'ZERO_RESULTS':
            return jsonify({'places': []}), 200
        if status != 'OK':
            return jsonify({'error': data.get('error_message', 'Places API request failed')}), 502

        places = []
        for p in data.get('results', []):
            place_lat = p['geometry']['location']['lat']
            place_lng = p['geometry']['location']['lng']
            places.append({
                'name': p.get('name'),
                'address': p.get('vicinity'),
                'rating': p.get('rating'),
                'lat': place_lat,
                'lng': place_lng,
                'place_id': p.get('place_id'),
                'open_now': p.get('opening_hours', {}).get('open_now'),
                'distance_km': round(_haversine_km(user_lat, user_lng, place_lat, place_lng), 1),
            })

        places.sort(key=lambda x: x['distance_km'])
        return jsonify({'places': places[:10]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
