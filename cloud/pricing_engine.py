"""
Dynamic pricing engine for Smart Parking System
"""

from datetime import datetime
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PricingEngine:
    """Manages dynamic pricing based on demand and time"""
    
    def __init__(self):
        self.base_price = config.BASE_PRICE_PER_HOUR
        self.peak_multiplier = config.PEAK_HOUR_MULTIPLIER
        self.off_peak_multiplier = config.OFF_PEAK_MULTIPLIER
        self.peak_hours = config.PEAK_HOURS
        
    def is_peak_hour(self, time=None):
        """Check if current time is peak hour"""
        if time is None:
            time = datetime.now()
            
        current_hour = time.hour
        
        for start_hour, end_hour in self.peak_hours:
            if start_hour <= current_hour < end_hour:
                return True
        return False
        
    def calculate_demand_multiplier(self, occupancy_rate):
        """
        Calculate pricing multiplier based on occupancy rate
        - High occupancy (>80%): 1.3x
        - Medium occupancy (50-80%): 1.0x
        - Low occupancy (<50%): 0.8x
        """
        if occupancy_rate >= 80:
            return 1.3
        elif occupancy_rate >= 50:
            return 1.0
        else:
            return 0.8
            
    def calculate_price(self, occupancy_rate, time=None):
        """
        Calculate dynamic price based on occupancy and time
        
        Args:
            occupancy_rate: Current occupancy rate (0-100)
            time: Datetime object (default: current time)
            
        Returns:
            Calculated price per hour
        """
        if time is None:
            time = datetime.now()
            
        # Start with base price
        price = self.base_price
        
        # Apply peak hour multiplier
        is_peak = self.is_peak_hour(time)
        if is_peak:
            price *= self.peak_multiplier
        else:
            # Apply off-peak discount
            if occupancy_rate < 50:
                price *= self.off_peak_multiplier
                
        # Apply demand-based multiplier
        demand_multiplier = self.calculate_demand_multiplier(occupancy_rate)
        price *= demand_multiplier
        
        # Round to 2 decimal places
        final_price = round(price, 2)
        
        logger.info(f"Calculated price: ${final_price}/hr (occupancy: {occupancy_rate}%, peak: {is_peak})")
        
        return final_price, is_peak
        
    def get_pricing_info(self, parking_lot_stats):
        """
        Get pricing information for all parking lots
        
        Args:
            parking_lot_stats: List of parking lot statistics
            
        Returns:
            Dictionary with pricing information for each lot
        """
        pricing_info = {}
        
        for lot in parking_lot_stats:
            occupancy_rate = lot['occupancy_rate']
            price, is_peak = self.calculate_price(occupancy_rate)
            
            pricing_info[lot['id']] = {
                'parking_lot_id': lot['id'],
                'parking_lot_name': lot['name'],
                'location': lot['location'],
                'current_price': price,
                'base_price': self.base_price,
                'occupancy_rate': occupancy_rate,
                'is_peak_hour': is_peak,
                'available_slots': lot['available_slots'],
                'total_slots': lot['total_slots']
            }
            
        return pricing_info


# Global pricing engine instance
pricing_engine = PricingEngine()