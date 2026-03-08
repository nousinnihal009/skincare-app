"""
doctors.py — Dermatologist Finder API (robust location-based search)
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import math

router = APIRouter(prefix="/api/doctors", tags=["doctors"])

# Expanded Dermatologist database with coordinates
DOCTORS_DATABASE = [
    {
        "id": 1, "name": "Dr. Sarah Mitchell", "specialty": "Medical Dermatology", "subspecialty": "Skin Cancer & Melanoma",
        "rating": 4.9, "reviews": 312, "experience_years": 18, "hospital": "City Dermatology Center",
        "address": "123 Medical Plaza, Suite 400", "city": "New York", "state": "NY", "zipcode": "10001",
        "lat": 40.7501, "lon": -73.9996, "phone": "+1 (212) 555-0101", "email": "dr.mitchell@cityderm.com",
        "availability": "Mon-Fri: 9AM-5PM", "accepts_insurance": True, "telemedicine": True, "image": None,
        "bio": "Board-certified dermatologist specializing in skin cancer detection and Mohs surgery."
    },
    {
        "id": 2, "name": "Dr. James Chen", "specialty": "Cosmetic Dermatology", "subspecialty": "Acne & Scarring",
        "rating": 4.8, "reviews": 245, "experience_years": 14, "hospital": "Advanced Skin Clinic",
        "address": "456 Healthcare Blvd", "city": "Los Angeles", "state": "CA", "zipcode": "90001",
        "lat": 33.9731, "lon": -118.2479, "phone": "+1 (310) 555-0202", "email": "dr.chen@advancedskin.com",
        "availability": "Mon-Sat: 8AM-6PM", "accepts_insurance": True, "telemedicine": True, "image": None,
        "bio": "Expert in acne treatment and scar revision. Pioneered several laser protocols."
    },
    {
        "id": 3, "name": "Dr. Emily Rodriguez", "specialty": "Pediatric Dermatology", "subspecialty": "Eczema",
        "rating": 4.9, "reviews": 189, "experience_years": 12, "hospital": "Children's Skin Health",
        "address": "789 Pediatric Way", "city": "Chicago", "state": "IL", "zipcode": "60601",
        "lat": 41.8842, "lon": -87.6251, "phone": "+1 (312) 555-0303", "email": "dr.rodriguez@childrensskin.com",
        "availability": "Mon-Fri: 8AM-4PM", "accepts_insurance": True, "telemedicine": True, "image": None,
        "bio": "Specialist in childhood skin conditions, particularly eczema and atopic dermatitis."
    },
    {
        "id": 4, "name": "Dr. Michael Okafor", "specialty": "Dermatopathology", "subspecialty": "Pigmentation",
        "rating": 4.7, "reviews": 156, "experience_years": 20, "hospital": "University Dermatology",
        "address": "321 University Circle", "city": "Houston", "state": "TX", "zipcode": "77001",
        "lat": 29.7589, "lon": -95.3677, "phone": "+1 (713) 555-0404", "email": "dr.okafor@uniderm.com",
        "availability": "Tue-Sat: 9AM-5PM", "accepts_insurance": True, "telemedicine": False, "image": None,
        "bio": "Expert in skin of color dermatology and pigmentation disorders."
    },
    {
        "id": 5, "name": "Dr. Lisa Kim", "specialty": "Surgical Dermatology", "subspecialty": "Mohs Surgery",
        "rating": 4.9, "reviews": 278, "experience_years": 16, "hospital": "Pacific Dermatology Group",
        "address": "567 Bay Area Drive", "city": "San Francisco", "state": "CA", "zipcode": "94101",
        "lat": 37.7749, "lon": -122.4194, "phone": "+1 (415) 555-0505", "email": "dr.kim@pacificderm.com",
        "availability": "Mon-Fri: 7AM-4PM", "accepts_insurance": True, "telemedicine": True, "image": None,
        "bio": "Fellowship-trained Mohs surgeon with one of the highest cure rates in the region."
    },
    {
        "id": 6, "name": "Dr. Priya Sharma", "specialty": "Medical Dermatology", "subspecialty": "Psoriasis",
        "rating": 4.8, "reviews": 198, "experience_years": 11, "hospital": "Integrative Skin Center",
        "address": "890 Wellness Pkwy", "city": "Seattle", "state": "WA", "zipcode": "98101",
        "lat": 47.6062, "lon": -122.3321, "phone": "+1 (206) 555-0606", "email": "dr.sharma@integrativeskin.com",
        "availability": "Mon-Thu: 9AM-6PM", "accepts_insurance": True, "telemedicine": True, "image": None,
        "bio": "Specializes in autoimmune skin conditions with an integrative approach."
    },
    {
        "id": 7, "name": "Dr. David Klein", "specialty": "Medical Dermatology", "subspecialty": "Rosacea & Acne",
        "rating": 4.6, "reviews": 142, "experience_years": 9, "hospital": "Miami Skin Institute",
        "address": "12 Ocean Drive", "city": "Miami", "state": "FL", "zipcode": "33101",
        "lat": 25.7617, "lon": -80.1918, "phone": "+1 (305) 555-0707", "email": "dr.klein@miamisurfacemd.com",
        "availability": "Wed-Sun: 10AM-6PM", "accepts_insurance": False, "telemedicine": True, "image": None,
        "bio": "Focused on advanced treatments for persistent rosacea and adult acne."
    },
    {
        "id": 8, "name": "Dr. Rachel Green", "specialty": "General Dermatology", "subspecialty": "Skin Cancer Screenings",
        "rating": 4.9, "reviews": 410, "experience_years": 22, "hospital": "Boston Dermatology Assoc",
        "address": "45 Newbury St", "city": "Boston", "state": "MA", "zipcode": "02116",
        "lat": 42.3524, "lon": -71.0746, "phone": "+1 (617) 555-0808", "email": "r.green@bostonderm.com",
        "availability": "Mon-Fri: 8AM-5PM", "accepts_insurance": True, "telemedicine": False, "image": None,
        "bio": "Over two decades of experience in comprehensive skin cancer screenings and mole mapping."
    },
]

# Simple geocoding lookup for major cities
CITY_COORDS = {
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "houston": (29.7604, -95.3698),
    "san francisco": (37.7749, -122.4194),
    "seattle": (47.6062, -122.3321),
    "miami": (25.7617, -80.1918),
    "boston": (42.3601, -71.0589),
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in miles between two points on the earth."""
    # Earth radius in miles
    R = 3959.0
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

@router.get("/search")
async def search_doctors(
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    radius: Optional[int] = 50,  # miles
    telemedicine: Optional[bool] = None,
):
    """
    Search for dermatologists. 
    If a city is provided and matches our database, it returns doctors within the radius based on coordinates.
    Otherwise, it falls back to text matching.
    """
    results = DOCTORS_DATABASE.copy()

    # Apply specialty filter
    if specialty:
        spec_lower = specialty.lower()
        results = [
            d for d in results
            if spec_lower in d["specialty"].lower()
            or spec_lower in d["subspecialty"].lower()
            or spec_lower in d["bio"].lower()
        ]

    # Apply location mapping (radius search) if available
    target_coords = None
    if city:
        city_lower = city.lower().strip()
        if city_lower in CITY_COORDS:
            target_coords = CITY_COORDS[city_lower]
        
        # If we have coordinates, use Haversine distance
        if target_coords:
            nearby = []
            for d in results:
                dist = haversine_distance(target_coords[0], target_coords[1], d["lat"], d["lon"])
                d["distance_miles"] = round(dist, 1)
                if dist <= radius:
                    nearby.append(d)
            results = nearby
            results.sort(key=lambda x: x["distance_miles"])
        else:
            # Fallback to text matching
            results = [d for d in results if city_lower in d["city"].lower() or city_lower in d["state"].lower() or city_lower in d["zipcode"]]

    # Apply telemedicine flag
    if telemedicine is not None:
        results = [d for d in results if d["telemedicine"] == telemedicine]

    return {
        "doctors": results,
        "total": len(results),
        "search_type": "radius" if target_coords else "text",
        "disclaimer": "This is a curated directory for demonstration purposes."
    }

@router.get("/{doctor_id}")
async def get_doctor(doctor_id: int):
    """Get a specific doctor's details."""
    for doctor in DOCTORS_DATABASE:
        if doctor["id"] == doctor_id:
            return doctor
    raise HTTPException(status_code=404, detail="Doctor not found")
