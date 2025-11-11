"""
Sensor Simulator - Manages multiple IoT sensors
"""

import threading
import config
import logging
from sensors.iot_sensor import IoTSensor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensorSimulator:
    """Manages multiple IoT sensor simulations"""
    
    def __init__(self, num_lots, slots_per_lot):
        self.num_lots = num_lots
        self.slots_per_lot = slots_per_lot
        self.sensors = []
        self.threads = []
        
    def create_sensors(self):
        """Create sensor instances for all parking slots"""
        logger.info(f"Creating {self.num_lots * self.slots_per_lot} sensors...")
        
        for lot_num in range(1, self.num_lots + 1):
            gateway_url = f"http://{config.GATEWAY_HOST}:{config.GATEWAY_PORT}/gateway/{lot_num}"
            
            for slot_num in range(1, self.slots_per_lot + 1):
                sensor_id = f"sensor_{lot_num}_{slot_num:03d}"
                sensor = IoTSensor(
                    sensor_id=sensor_id,
                    parking_lot_id=lot_num,
                    gateway_url=gateway_url
                )
                self.sensors.append(sensor)
                
        logger.info(f"Created {len(self.sensors)} sensors")
        
    def start_all_sensors(self, interval=5):
        """Start all sensors in separate threads"""
        logger.info("Starting all sensors...")
        
        for sensor in self.sensors:
            thread = threading.Thread(
                target=sensor.run,
                args=(interval,),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            
        logger.info(f"Started {len(self.threads)} sensor threads")
        
    def stop_all_sensors(self):
        """Stop all sensor threads"""
        logger.info("Stopping all sensors...")
        # Threads will stop on KeyboardInterrupt
        
    def run(self, interval=5):
        """Run the sensor simulator"""
        self.create_sensors()
        self.start_all_sensors(interval)
        
        try:
            # Keep main thread alive
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Sensor simulator stopped")


def run_simulator():
    """Run the sensor simulator"""
    simulator = SensorSimulator(
        num_lots=config.NUM_PARKING_LOTS,
        slots_per_lot=config.SLOTS_PER_LOT
    )
    simulator.run(interval=config.SENSOR_UPDATE_INTERVAL)


if __name__ == '__main__':
    run_simulator()