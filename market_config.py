#!/usr/bin/env python3
"""
Market Configuration
Centralized market center ZIPs and city lists for search optimization
"""

# Market center ZIP codes (from market search radius.csv)
MARKET_CENTER_ZIPS = {
    'Dallas': '75060',
    'Houston': '77007',
    'Phoenix': '85009',
    'Denver': '80218',
    'Las Vegas': '89107',
    'Stockton': '95205',
    'Bay Area': '94501',
    'Inland Empire': '92324',
    'Trenton': '07017',
    'Newark': '08638',
    'Sacramento': '95814',
    'Rochester': '14604',
    'Des Moines': '50309'
}

# Market radii in miles
MARKET_RADII = {
    'Dallas': 75,
    'Houston': 75,
    'Phoenix': 75,
    'Denver': 75,
    'Las Vegas': 75,
    'Stockton': 75,
    'Bay Area': 75,
    'Inland Empire': 75,
    'Trenton': 50,  # Smaller radius
    'Newark': 75,
    'Sacramento': 75,
    'Rochester': 75,
    'Des Moines': 75
}

# Cities within 75 miles of each market center (for Google searches)
# Generated from location_markets table - cities that map to each market
MARKET_CITIES = {
    'Dallas': [
        'Dallas, TX',
        'Fort Worth, TX',
        'Arlington, TX',
        'Plano, TX',
        'Irving, TX',
        'Garland, TX',
        'Frisco, TX',
        'McKinney, TX',
        'Carrollton, TX',
        'Denton, TX',
        'Richardson, TX',
        'Lewisville, TX',
        'Mesquite, TX',
        'Grand Prairie, TX',
        'Allen, TX'
    ],
    'Houston': [
        'Houston, TX',
        'Pasadena, TX',
        'Pearland, TX',
        'Sugar Land, TX',
        'The Woodlands, TX',
        'Conroe, TX',
        'League City, TX',
        'Missouri City, TX',
        'Katy, TX',
        'Cypress, TX',
        'Spring, TX',
        'Humble, TX',
        'Baytown, TX',
        'Galveston, TX'
    ],
    'Phoenix': [
        'Phoenix, AZ',
        'Mesa, AZ',
        'Chandler, AZ',
        'Scottsdale, AZ',
        'Glendale, AZ',
        'Gilbert, AZ',
        'Tempe, AZ',
        'Peoria, AZ',
        'Surprise, AZ',
        'Goodyear, AZ',
        'Avondale, AZ',
        'Buckeye, AZ',
        'Casa Grande, AZ'
    ],
    'Denver': [
        'Denver, CO',
        'Aurora, CO',
        'Lakewood, CO',
        'Thornton, CO',
        'Arvada, CO',
        'Westminster, CO',
        'Centennial, CO',
        'Boulder, CO',
        'Longmont, CO',
        'Broomfield, CO',
        'Commerce City, CO',
        'Brighton, CO',
        'Fort Collins, CO',
        'Greeley, CO'
    ],
    'Las Vegas': [
        'Las Vegas, NV',
        'Henderson, NV',
        'North Las Vegas, NV',
        'Boulder City, NV',
        'Mesquite, NV',
        'Pahrump, NV'
    ],
    'Stockton': [
        'Stockton, CA',
        'Tracy, CA',
        'Manteca, CA',
        'Lodi, CA',
        'Modesto, CA',
        'Turlock, CA',
        'Merced, CA',
        'Livermore, CA',
        'Pleasanton, CA',
        'Dublin, CA'
    ],
    'Bay Area': [
        'Oakland, CA',
        'San Francisco, CA',
        'San Jose, CA',
        'Fremont, CA',
        'Hayward, CA',
        'Sunnyvale, CA',
        'Berkeley, CA',
        'Richmond, CA',
        'Concord, CA',
        'Antioch, CA',
        'Vallejo, CA',
        'Fairfield, CA',
        'Santa Rosa, CA',
        'San Rafael, CA',
        'Palo Alto, CA',
        'Mountain View, CA',
        'Santa Clara, CA',
        'Alameda, CA',
        'San Leandro, CA',
        'Walnut Creek, CA',
        'San Mateo, CA',
        'Redwood City, CA'
    ],
    'Inland Empire': [
        'Riverside, CA',
        'San Bernardino, CA',
        'Ontario, CA',
        'Rancho Cucamonga, CA',
        'Fontana, CA',
        'Moreno Valley, CA',
        'Corona, CA',
        'Murrieta, CA',
        'Temecula, CA',
        'Victorville, CA',
        'Hesperia, CA',
        'Chino, CA',
        'Chino Hills, CA',
        'Redlands, CA',
        'Perris, CA',
        'Hemet, CA',
        'Lake Elsinore, CA',
        'Indio, CA',
        'Palm Springs, CA',
        'Palm Desert, CA'
    ],
    'Trenton': [
        'Trenton, NJ',
        'Princeton, NJ',
        'Ewing, NJ',
        'Hamilton, NJ',
        'Lawrence, NJ',
        'Hopewell, NJ',
        'Pennington, NJ'
    ],
    'Newark': [
        'Newark, NJ',
        'Jersey City, NJ',
        'Elizabeth, NJ',
        'Paterson, NJ',
        'Clifton, NJ',
        'Passaic, NJ',
        'Union City, NJ',
        'Bayonne, NJ',
        'East Orange, NJ',
        'Irvington, NJ',
        'Hackensack, NJ',
        'Plainfield, NJ',
        'New Brunswick, NJ',
        'Perth Amboy, NJ',
        'Orange, NJ',
        'Fort Lee, NJ',
        'Englewood, NJ',
        'Kearny, NJ',
        'Linden, NJ',
        'Rahway, NJ'
    ],
    'Sacramento': [
        'Sacramento, CA',
        'Elk Grove, CA',
        'Roseville, CA',
        'Folsom, CA',
        'Citrus Heights, CA',
        'Rocklin, CA',
        'Davis, CA',
        'Woodland, CA',
        'West Sacramento, CA',
        'Rancho Cordova, CA',
        'Auburn, CA',
        'Yuba City, CA',
        'Marysville, CA'
    ],
    'Rochester': [
        'Rochester, NY',
        'Greece, NY',
        'Irondequoit, NY',
        'Brighton, NY',
        'Henrietta, NY',
        'Webster, NY',
        'Penfield, NY',
        'Pittsford, NY',
        'Brockport, NY',
        'Batavia, NY',
        'Geneva, NY',
        'Canandaigua, NY'
    ],
    'Des Moines': [
        'Des Moines, IA',
        'West Des Moines, IA',
        'Ankeny, IA',
        'Urbandale, IA',
        'Ames, IA',
        'Johnston, IA',
        'Clive, IA',
        'Waukee, IA',
        'Altoona, IA',
        'Pleasant Hill, IA',
        'Indianola, IA',
        'Marshalltown, IA',
        'Newton, IA'
    ]
}


def get_market_center_zip(market: str) -> str:
    """Get the center ZIP code for a market"""
    return MARKET_CENTER_ZIPS.get(market, '')


def get_market_radius(market: str) -> int:
    """Get the radius in miles for a market"""
    return MARKET_RADII.get(market, 75)


def get_market_cities(market: str) -> list:
    """Get list of cities within market radius"""
    return MARKET_CITIES.get(market, [])


def get_all_markets() -> list:
    """Get list of all market names"""
    return list(MARKET_CENTER_ZIPS.keys())
