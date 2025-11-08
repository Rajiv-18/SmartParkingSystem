"""
Regional Gateway Server for Smart Parking System
Aggregates data from IoT sensors and forwards to central cloud
Implements edge computing with caching and fault tolerance
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import logging
from datetime import datetime
from collections import deque
import threading
import time
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegionalGateway:
    """Regional gateway for processing sensor data"""
    
    def __init__(self, gateway_id, parking_lot_id, cloud_url):
        self.gateway_id = gateway_id
        self.parking_lot_id = parking_lot_id
        self.cloud_url = cloud_url
        
        # Edge caching for fault tolerance
        self.cache = deque(maxlen=config.GATEWAY_CACHE_SIZE)
        self.pending_updates = []
        
        # Statistics
        self.total_received = 0
        self.total_forwarded = 0
        self.total_errors = 0
        
        self.running = True
        
    def validate_sensor_data(self, data):
        """Validate incoming sensor data"""
        required_fields = ['sensor_id', 'parking_lot_id', 'is_occupied', 'timestamp']
        return all(field in data for field in required_fields)
        
    def cache_data(self, data):
        """Cache sensor data locally"""
        data['cached_at'] = datetime.utcnow().isoformat()
        self.cache.append(data)
        logger.debug(f"Gateway {self.gateway_id}: Cached data for sensor {data['sensor_id']}")
        
    def forward_to_cloud(self, data):
        """
        Forward processed data to central cloud
        Implements retry logic for fault tolerance
        """
        try:
            response = requests.post(
                f"{self.cloud_url}/api/sensor-update",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                self.total_forwarded += 1
                logger.info(f"Gateway {self.gateway_id}: Forwarded data to cloud")
                return True
            else:
                logger.warning(f"Gateway {self.gateway_id}: Cloud returned {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Gateway {self.gateway_id}: Failed to reach cloud - {e}")
            self.total_errors += 1
            return False
            
    def process_sensor_data(self, data):
        """
        Process incoming sensor data
        - Validate data
        - Cache locally for fault tolerance
        - Forward to cloud asynchronously
        """
        self.total_received += 1
        
        # Validate
        if not self.validate_sensor_data(data):
            logger.warning(f"Gateway {self.gateway_id}: Invalid sensor data")
            return False
            
        # Cache locally
        self.cache_data(data)
        
        # Add to pending updates for batch processing
        self.pending_updates.append(data)
        
        return True
        
    def sync_with_cloud(self):
        """
        Periodically sync pending updates with cloud
        Implements publish-subscribe pattern
        """
        while self.running:
            if self.pending_updates:
                logger.info(f"Gateway {self.gateway_id}: Syncing {len(self.pending_updates)} updates to cloud")
                
                updates_to_send = self.pending_updates.copy()
                self.pending_updates.clear()
                
                for update in updates_to_send:
                    success = self.forward_to_cloud(update)
                    if not success:
                        # Re-add to pending if failed (fault tolerance)
                        self.pending_updates.append(update)
                        
            time.sleep(config.GATEWAY_SYNC_INTERVAL)
            
    def get_statistics(self):
        """Get gateway statistics"""
        return {
            'gateway_id': self.gateway_id,
            'parking_lot_id': self.parking_lot_id,
            'total_received': self.total_received,
            'total_forwarded': self.total_forwarded,
            'total_errors': self.total_errors,
            'cache_size': len(self.cache),
            'pending_updates': len(self.pending_updates)
        }
        
    def start_sync_thread(self):
        """Start background thread for cloud synchronization"""
        sync_thread = threading.Thread(target=self.sync_with_cloud, daemon=True)
        sync_thread.start()
        logger.info(f"Gateway {self.gateway_id}: Sync thread started")


# Create Flask app for gateway
app = Flask(__name__)
CORS(app)

# Dictionary to store gateway instances
gateways = {}


def get_gateway(lot_id):
    """Get or create gateway for parking lot"""
    if lot_id not in gateways:
        gateway_id = f"gateway_{lot_id}"
        cloud_url = f"http://{config.CLOUD_HOST}:{config.CLOUD_SERVER_PORT}"
        gateway = RegionalGateway(gateway_id, lot_id, cloud_url)
        gateway.start_sync_thread()
        gateways[lot_id] = gateway
        logger.info(f"Created gateway for parking lot {lot_id}")
    return gateways[lot_id]


@app.route('/gateway/<int:lot_id>/sensor-data', methods=['POST'])
def receive_sensor_data(lot_id):
    """Receive sensor data from IoT devices"""
    try:
        data = request.json
        gateway = get_gateway(lot_id)
        
        success = gateway.process_sensor_data(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Data received and cached',
                'gateway_id': gateway.gateway_id
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid sensor data'
            }), 400
            
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/gateway/<int:lot_id>/stats', methods=['GET'])
def get_gateway_stats(lot_id):
    """Get gateway statistics"""
    try:
        gateway = get_gateway(lot_id)
        stats = gateway.get_statistics()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"Error fetching gateway stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/gateway/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Regional Gateway Server',
        'active_gateways': len(gateways)
    })


def run_gateway_server():
    """Run the gateway server"""
    logger.info("Starting Regional Gateway Server...")
    app.run(host='0.0.0.0', port=config.GATEWAY_PORT, debug=config.DEBUG_MODE)

if __name__ == '__main__':
    run_gateway_server()
    
