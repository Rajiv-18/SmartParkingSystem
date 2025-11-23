import os

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///parking_system.db')

# Server Configuration
GATEWAY_PORT = 5001
CLOUD_SERVER_PORT = 5000
GATEWAY_HOST = 'localhost'
CLOUD_HOST = 'localhost'

# Parking Lot Configuration
NUM_PARKING_LOTS = 5
SLOTS_PER_LOT = 6
TOTAL_SLOTS = NUM_PARKING_LOTS * SLOTS_PER_LOT

# Dynamic Pricing Configuration
BASE_PRICE_PER_HOUR = 5.0
PEAK_HOUR_MULTIPLIER = 1.5
OFF_PEAK_MULTIPLIER = 0.75
PEAK_HOURS = [(7, 10), (16, 19)] 
MAX_DAILY_PRICE = 25.0  # Maximum price cap per booking

# Sensor Simulation Configuration
SENSOR_UPDATE_INTERVAL = 3  
OCCUPANCY_CHANGE_PROBABILITY = 0.2

# Gateway Configuration
GATEWAY_CACHE_SIZE = 100
GATEWAY_SYNC_INTERVAL = 4  # seconds

# System Configuration
DEBUG_MODE = True
LOG_LEVEL = 'INFO'