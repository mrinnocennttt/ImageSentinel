import math

# Curated offline reference dataset of major global cities, capitals, and administrative hubs
# Used strictly for offline reference estimation without making any external API calls.
OFFLINE_CITIES = [
    # North America
    {"city": "New York", "region": "New York", "country": "United States", "lat": 40.7128, "lon": -74.0060},
    {"city": "Los Angeles", "region": "California", "country": "United States", "lat": 34.0522, "lon": -118.2437},
    {"city": "Chicago", "region": "Illinois", "country": "United States", "lat": 41.8781, "lon": -87.6298},
    {"city": "Houston", "region": "Texas", "country": "United States", "lat": 29.7604, "lon": -95.3698},
    {"city": "San Francisco", "region": "California", "country": "United States", "lat": 37.7749, "lon": -122.4194},
    {"city": "Seattle", "region": "Washington", "country": "United States", "lat": 47.6062, "lon": -122.3321},
    {"city": "Washington, D.C.", "region": "District of Columbia", "country": "United States", "lat": 38.9072, "lon": -77.0369},
    {"city": "Miami", "region": "Florida", "country": "United States", "lat": 25.7617, "lon": -80.1918},
    {"city": "Boston", "region": "Massachusetts", "country": "United States", "lat": 42.3601, "lon": -71.0589},
    {"city": "Atlanta", "region": "Georgia", "country": "United States", "lat": 33.7490, "lon": -84.3880},
    {"city": "Dallas", "region": "Texas", "country": "United States", "lat": 32.7767, "lon": -96.7970},
    {"city": "Denver", "region": "Colorado", "country": "United States", "lat": 39.7392, "lon": -104.9903},
    {"city": "Toronto", "region": "Ontario", "country": "Canada", "lat": 43.6532, "lon": -79.3832},
    {"city": "Montreal", "region": "Quebec", "country": "Canada", "lat": 45.5017, "lon": -73.5673},
    {"city": "Vancouver", "region": "British Columbia", "country": "Canada", "lat": 49.2827, "lon": -123.1207},
    {"city": "Mexico City", "region": "CDMX", "country": "Mexico", "lat": 19.4326, "lon": -99.1332},
    {"city": "Guadalajara", "region": "Jalisco", "country": "Mexico", "lat": 20.6597, "lon": -103.3496},
    
    # Europe
    {"city": "London", "region": "England", "country": "United Kingdom", "lat": 51.5074, "lon": -0.1278},
    {"city": "Paris", "region": "Île-de-France", "country": "France", "lat": 48.8566, "lon": 2.3522},
    {"city": "Berlin", "region": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050},
    {"city": "Madrid", "region": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038},
    {"city": "Rome", "region": "Lazio", "country": "Italy", "lat": 41.9028, "lon": 12.4964},
    {"city": "Amsterdam", "region": "North Holland", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041},
    {"city": "Brussels", "region": "Brussels", "country": "Belgium", "lat": 50.8503, "lon": 4.3517},
    {"city": "Vienna", "region": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738},
    {"city": "Bern", "region": "Bern", "country": "Switzerland", "lat": 46.9480, "lon": 7.4474},
    {"city": "Zurich", "region": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417},
    {"city": "Stockholm", "region": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686},
    {"city": "Oslo", "region": "Oslo", "country": "Norway", "lat": 59.9139, "lon": 10.7522},
    {"city": "Copenhagen", "region": "Capital Region", "country": "Denmark", "lat": 55.6761, "lon": 12.5683},
    {"city": "Helsinki", "region": "Uusimaa", "country": "Finland", "lat": 60.1699, "lon": 24.9384},
    {"city": "Warsaw", "region": "Mazovia", "country": "Poland", "lat": 52.2297, "lon": 21.0122},
    {"city": "Prague", "region": "Prague", "country": "Czech Republic", "lat": 50.0755, "lon": 14.4378},
    {"city": "Budapest", "region": "Budapest", "country": "Hungary", "lat": 47.4979, "lon": 19.0402},
    {"city": "Athens", "region": "Attica", "country": "Greece", "lat": 37.9838, "lon": 23.7275},
    {"city": "Lisbon", "region": "Lisbon", "country": "Portugal", "lat": 38.7223, "lon": -9.1393},
    {"city": "Dublin", "region": "Leinster", "country": "Ireland", "lat": 53.3498, "lon": -6.2603},
    {"city": "Kyiv", "region": "Kyiv", "country": "Ukraine", "lat": 50.4501, "lon": 30.5234},
    {"city": "Moscow", "region": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173},

    # Asia & Middle East
    {"city": "New Delhi", "region": "Delhi", "country": "India", "lat": 28.6139, "lon": 77.2090},
    {"city": "Mumbai", "region": "Maharashtra", "country": "India", "lat": 19.0760, "lon": 72.8777},
    {"city": "Bengaluru", "region": "Karnataka", "country": "India", "lat": 12.9716, "lon": 77.5946},
    {"city": "Chennai", "region": "Tamil Nadu", "country": "India", "lat": 13.0827, "lon": 80.2707},
    {"city": "Kolkata", "region": "West Bengal", "country": "India", "lat": 22.5726, "lon": 88.3639},
    {"city": "Hyderabad", "region": "Telangana", "country": "India", "lat": 17.3850, "lon": 78.4867},
    {"city": "Ahmedabad", "region": "Gujarat", "country": "India", "lat": 23.0225, "lon": 72.5714},
    {"city": "Pune", "region": "Maharashtra", "country": "India", "lat": 18.5204, "lon": 73.8567},
    {"city": "Tokyo", "region": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503},
    {"city": "Osaka", "region": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023},
    {"city": "Beijing", "region": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074},
    {"city": "Shanghai", "region": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737},
    {"city": "Hong Kong", "region": "Hong Kong", "country": "China", "lat": 22.3193, "lon": 114.1694},
    {"city": "Seoul", "region": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780},
    {"city": "Singapore", "region": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198},
    {"city": "Bangkok", "region": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018},
    {"city": "Kuala Lumpur", "region": "Federal Territory", "country": "Malaysia", "lat": 3.1390, "lon": 101.6869},
    {"city": "Jakarta", "region": "Jakarta", "country": "Indonesia", "lat": -6.2088, "lon": 106.8456},
    {"city": "Manila", "region": "Metro Manila", "country": "Philippines", "lat": 14.5995, "lon": 120.9842},
    {"city": "Hanoi", "region": "Hanoi", "country": "Vietnam", "lat": 21.0285, "lon": 105.8542},
    {"city": "Dubai", "region": "Dubai", "country": "United Arab Emirates", "lat": 25.2048, "lon": 55.2708},
    {"city": "Abu Dhabi", "region": "Abu Dhabi", "country": "United Arab Emirates", "lat": 24.4539, "lon": 54.3773},
    {"city": "Riyadh", "region": "Riyadh", "country": "Saudi Arabia", "lat": 24.7136, "lon": 46.6753},
    {"city": "Doha", "region": "Doha", "country": "Qatar", "lat": 25.2854, "lon": 51.5310},
    {"city": "Tel Aviv", "region": "Tel Aviv", "country": "Israel", "lat": 32.0853, "lon": 34.7818},
    {"city": "Istanbul", "region": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784},

    # Oceania
    {"city": "Sydney", "region": "New South Wales", "country": "Australia", "lat": -33.8688, "lon": 151.2093},
    {"city": "Melbourne", "region": "Victoria", "country": "Australia", "lat": -37.8136, "lon": 144.9631},
    {"city": "Brisbane", "region": "Queensland", "country": "Australia", "lat": -27.4698, "lon": 153.0251},
    {"city": "Perth", "region": "Western Australia", "country": "Australia", "lat": -31.9505, "lon": 115.8605},
    {"city": "Auckland", "region": "Auckland", "country": "New Zealand", "lat": -36.8485, "lon": 174.7633},

    # South America
    {"city": "São Paulo", "region": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333},
    {"city": "Rio de Janeiro", "region": "Rio de Janeiro", "country": "Brazil", "lat": -22.9068, "lon": -43.1729},
    {"city": "Buenos Aires", "region": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816},
    {"city": "Santiago", "region": "Santiago", "country": "Chile", "lat": -33.4489, "lon": -70.6693},
    {"city": "Bogotá", "region": "Bogotá D.C.", "country": "Colombia", "lat": 4.7110, "lon": -74.0721},
    {"city": "Lima", "region": "Lima", "country": "Peru", "lat": -12.0464, "lon": -77.0428},

    # Africa
    {"city": "Cairo", "region": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357},
    {"city": "Johannesburg", "region": "Gauteng", "country": "South Africa", "lat": -26.2041, "lon": 28.0473},
    {"city": "Cape Town", "region": "Western Cape", "country": "South Africa", "lat": -33.9249, "lon": 18.4241},
    {"city": "Nairobi", "region": "Nairobi", "country": "Kenya", "lat": -1.2921, "lon": 36.8219},
    {"city": "Lagos", "region": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792},
    {"city": "Casablanca", "region": "Casablanca-Settat", "country": "Morocco", "lat": 33.5731, "lon": -7.5898},
]


class GeoIntel:
    """Provides local, offline geolocation intelligence and precision analysis for GPS metadata."""

    @staticmethod
    def haversine_distance_km(lat1, lon1, lat2, lon2):
        """Calculate great-circle distance between two points on the Earth in kilometers."""
        r = 6371.0  # Earth's radius in kilometers
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @staticmethod
    def calculate_precision(lat, lon, raw_gps=None):
        """Calculate approximate location precision based on coordinate resolution and EXIF precision tags."""
        if lat is None or lon is None:
            return "Precision undetermined"

        # Check for explicit EXIF positioning error or DOP if present
        raw_gps = raw_gps or {}
        h_err = raw_gps.get("GPSHPositioningError")
        if h_err:
            try:
                err_val = float(h_err)
                return f"+/- {err_val:.1f} meters (EXIF GPSHPositioningError)"
            except (ValueError, TypeError):
                pass

        dop = raw_gps.get("GPSDOP")
        if dop:
            try:
                dop_val = float(dop)
                return f"DOP: {dop_val:.1f} (~ +/- {dop_val * 5:.1f} meters estimated)"
            except (ValueError, TypeError):
                pass

        # Calculate decimal resolution
        lat_str = f"{lat:.8f}".rstrip('0')
        lon_str = f"{lon:.8f}".rstrip('0')
        lat_dec = len(lat_str.split('.')[1]) if '.' in lat_str else 0
        lon_dec = len(lon_str.split('.')[1]) if '.' in lon_str else 0
        min_dec = min(lat_dec, lon_dec)

        if min_dec >= 6:
            return "+/- 0.11 m (Pinpoint Sub-Meter Precision - 6+ decimals)"
        elif min_dec == 5:
            return "+/- 1.1 m (High Building/Street Precision - 5 decimals)"
        elif min_dec == 4:
            return "+/- 11 m (Neighborhood/Street Precision - 4 decimals)"
        elif min_dec == 3:
            return "+/- 110 m (District Precision - 3 decimals)"
        elif min_dec == 2:
            return "+/- 1.1 km (City/Town Precision - 2 decimals)"
        elif min_dec == 1:
            return "+/- 11 km (Regional Precision - 1 decimal)"
        else:
            return "+/- 110 km (Rough Regional / Country Precision)"

    @classmethod
    def find_nearest_reference(cls, lat, lon):
        """Find the nearest reference city using purely local offline dataset."""
        if lat is None or lon is None:
            return None

        best_match = None
        min_dist = float('inf')

        for item in OFFLINE_CITIES:
            dist = cls.haversine_distance_km(lat, lon, item["lat"], item["lon"])
            if dist < min_dist:
                min_dist = dist
                best_match = item

        if not best_match:
            return None

        city = best_match["city"]
        region = best_match["region"]
        country = best_match["country"]

        if min_dist <= 25.0:
            desc = f"Near {city}, {region}, {country} (approx. {min_dist:.1f} km away - offline reference)"
        elif min_dist <= 80.0:
            desc = f"Vicinity of {city}, {country} (approx. {min_dist:.1f} km away - offline reference)"
        elif min_dist <= 200.0:
            desc = f"Region of {city}, {country} (approx. {min_dist:.1f} km away - offline reference)"
        else:
            desc = f"Approx. {min_dist:.0f} km from {city}, {country} (Nearest offline major hub)"

        return {
            "nearest_city": city,
            "region": region,
            "country": country,
            "distance_km": round(min_dist, 1),
            "readable_location": desc,
            "offline_only": True
        }

    @staticmethod
    def get_map_links(lat, lon):
        """Generate web mapping links without transmitting image data."""
        if lat is None or lon is None:
            return {}
        return {
            "google_maps": f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}",
            "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat:.6f}&mlon={lon:.6f}#map=15/{lat:.6f}/{lon:.6f}"
        }
