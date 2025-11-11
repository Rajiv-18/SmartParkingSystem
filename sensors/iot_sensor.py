"""
IoT Sensor Simulation for Smart Parking System
Simulates ultrasonic/infrared sensors detecting vehicle presence
"""

import random
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IoTSensor:
    """Simulates an IoT parking sensor"""
    
    def __init__(self, sensor_id, parking_lot_id, gateway_url):
        self.sensor_id = sensor_id
        self.parking_lot_id = parking_lot_id
        self.gateway_url = gateway_url
        self.is_occupied = False
        self.last_update = None
        
    def detect_vehicle(self):
        """
        Simulate vehicle detection
        Returns True if vehicle is detected, False otherwise
        """
        # Simulate random occupancy changes
        if random.random() < 0.1:  # 10% chance of state change
            self.is_occupied = not self.is_occupied
            return True  # State changed
        return False  # No change
        
    def send_data(self):
        """Send sensor data to the regional gateway"""
        try:
            payload = {
                'sensor_id': self.sensor_id,
                'parking_lot_id': self.parking_lot_id,
                'is_occupied': self.is_occupied,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                f"{self.gateway_url}/sensor-data",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Sensor {self.sensor_id}: Data sent successfully (occupied={self.is_occupied})")
                self.last_update = datetime.utcnow()
                return True
            else:
                logger.warning(f"Sensor {self.sensor_id}: Failed to send data - {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Sensor {self.sensor_id}: Connection error - {e}")
            return False
            
    def run(self, interval=5):
        """
        Run sensor in continuous monitoring mode
        
        Args:
            interval: Update interval in seconds
        """
        logger.info(f"Sensor {self.sensor_id} started monitoring")
        
        while True:
            try:
                # Detect vehicle presence
                state_changed = self.detect_vehicle()
                
                # Send data to gateway (send on every interval or when state changes)
                if state_changed or random.random() < 0.3:  # Send updates periodically
                    self.send_data()
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info(f"Sensor {self.sensor_id} stopped")
                break
            except Exception as e:
                logger.error(f"Sensor {self.sensor_id} error: {e}")
                time.sleep(interval)