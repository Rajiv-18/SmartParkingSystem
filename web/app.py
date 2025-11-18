"""
Web Application for Smart Parking System
Provides user interface for viewing and booking parking spaces
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Cloud server URL
CLOUD_API = f"http://{config.CLOUD_HOST}:{config.CLOUD_SERVER_PORT}/api"


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Dashboard page showing parking availability"""
    return render_template('dashboard.html')


@app.route('/booking')
def booking():
    """Booking page for reserving parking spots"""
    return render_template('booking.html', max_price=config.MAX_DAILY_PRICE)


# Proxy API endpoints to cloud server
@app.route('/api/parking-lots', methods=['GET'])
def get_parking_lots():
    """Proxy request to cloud server"""
    try:
        response = requests.get(f"{CLOUD_API}/parking-lots", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error fetching parking lots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    """Proxy request to cloud server"""
    try:
        lot_id = request.args.get('lot_id')
        url = f"{CLOUD_API}/available-slots"
        if lot_id:
            url += f"?lot_id={lot_id}"
        response = requests.get(url, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error fetching available slots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pricing', methods=['GET'])
def get_pricing():
    """Proxy request to cloud server"""
    try:
        response = requests.get(f"{CLOUD_API}/pricing", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error fetching pricing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Proxy request to cloud server"""
    try:
        response = requests.get(f"{CLOUD_API}/stats", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """Proxy request to cloud server"""
    try:
        response = requests.get(f"{CLOUD_API}/users", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Proxy booking request to cloud server"""
    try:
        data = request.json
        response = requests.post(f"{CLOUD_API}/bookings", json=data, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/my-bookings')
def my_bookings():
    """My Bookings page for managing reservations"""
    return render_template('my_bookings.html')

@app.route('/api/users/<int:user_id>/bookings', methods=['GET'])
def get_user_bookings(user_id):
    """Proxy request to cloud server"""
    try:
        status = request.args.get('status')
        url = f"{CLOUD_API}/users/{user_id}/bookings"
        if status:
            url += f"?status={status}"
            
        response = requests.get(url, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error fetching user bookings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    """Proxy request to cloud server"""
    try:
        response = requests.post(f"{CLOUD_API}/bookings/{booking_id}/cancel", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def run_web_app():
    """Run the web application"""
    logger.info("Starting Web Application...")
    app.run(host='0.0.0.0', port=8081, debug=config.DEBUG_MODE)

if __name__ == '__main__':
    run_web_app()