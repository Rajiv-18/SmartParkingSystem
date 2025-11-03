"""
Central Cloud Server for Smart Parking System
RESTful API for managing parking operations
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import config
from cloud.database import db_manager
from cloud.pricing_engine import pricing_engine
from cloud.models import Booking, User, ParkingSlot, ParkingLot, PricingLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Central Cloud Server'
    })


@app.route('/api/parking-lots', methods=['GET'])
def get_parking_lots():
    """Get all parking lots with current status"""
    try:
        stats = db_manager.get_parking_lot_stats()
        return jsonify({
            'success': True,
            'data': stats,
            'count': len(stats)
        })
    except Exception as e:
        logger.error(f"Error fetching parking lots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/parking-lots/<int:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    """Get specific parking lot details"""
    try:
        stats = db_manager.get_parking_lot_stats()
        lot = next((l for l in stats if l['id'] == lot_id), None)
        
        if lot:
            return jsonify({'success': True, 'data': lot})
        else:
            return jsonify({'success': False, 'error': 'Parking lot not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching parking lot {lot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    """Get all available parking slots"""
    try:
        lot_id = request.args.get('lot_id', type=int)
        slots_data = db_manager.get_available_slots(lot_id)

        return jsonify({
            'success': True,
            'data': slots_data,
            'count': len(slots_data)
        })
    except Exception as e:
        logger.error(f"Error fetching available slots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pricing', methods=['GET'])
def get_pricing():
    """Get current pricing for all parking lots"""
    try:
        stats = db_manager.get_parking_lot_stats()
        pricing_info = pricing_engine.get_pricing_info(stats)
        
        # Log pricing to database
        with db_manager.session_scope() as session:
            for lot_id, pricing in pricing_info.items():
                pricing_log = PricingLog(
                    parking_lot_id=lot_id,
                    occupancy_rate=pricing['occupancy_rate'],
                    base_price=pricing['base_price'],
                    adjusted_price=pricing['current_price'],
                    is_peak_hour=pricing['is_peak_hour']
                )
                session.add(pricing_log)
        
        return jsonify({
            'success': True,
            'data': list(pricing_info.values()),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error calculating pricing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sensor-update', methods=['POST'])
def update_sensor():
    """
    Receive sensor updates from regional gateways
    This endpoint is called by gateway servers to update slot occupancy
    """
    try:
        data = request.json
        
        sensor_id = data.get('sensor_id')
        is_occupied = data.get('is_occupied')
        
        if sensor_id is None or is_occupied is None:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: sensor_id and is_occupied'
            }), 400
            
        # Update slot occupancy in database
        success = db_manager.update_slot_occupancy(sensor_id, is_occupied)
        
        if success:
            logger.info(f"Sensor update processed: {sensor_id} -> occupied={is_occupied}")
            return jsonify({
                'success': True,
                'message': 'Sensor data updated successfully'
            }), 200
        else:
            logger.warning(f"Sensor not found: {sensor_id}")
            return jsonify({
                'success': False,
                'error': 'Sensor not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating sensor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create a new parking booking"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['user_id', 'slot_id', 'duration_hours']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: user_id, slot_id, duration_hours'
            }), 400
            
        user_id = data['user_id']
        slot_id = data['slot_id']
        duration_hours = data['duration_hours']
        
        # Validate duration
        if duration_hours < 1 or duration_hours > 24:
            return jsonify({
                'success': False,
                'error': 'Duration must be between 1 and 24 hours'
            }), 400
        
        # Get current pricing/stats BEFORE opening the transaction session
        lot_stats = db_manager.get_parking_lot_stats()

        with db_manager.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            slot = session.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
            if not slot:
                return jsonify({'success': False, 'error': 'Slot not found'}), 404
                
            if slot.is_occupied:
                return jsonify({'success': False, 'error': 'Slot is already occupied'}), 400
                
            lot_stat = next((l for l in lot_stats if l['id'] == slot.parking_lot_id), None)
            if not lot_stat:
                return jsonify({'success': False, 'error': 'Parking lot not found'}), 404

            # CHANGED: Price Locking Logic
            # If frontend sent a price, use it (Price Lock). Otherwise, calculate it.
            if 'price_per_hour' in data:
                price_per_hour = float(data['price_per_hour'])
                _, is_peak = pricing_engine.calculate_price(lot_stat['occupancy_rate'])
            else:
                price_per_hour, is_peak = pricing_engine.calculate_price(lot_stat['occupancy_rate'])
            
            # NEW: Calculate Total and Apply Cap
            raw_total = price_per_hour * duration_hours
            total_price = min(raw_total, config.MAX_DAILY_PRICE) # Cap at $25
            
            # CHANGED: Use local time (EST) instead of utcnow
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
            
            booking = Booking(
                user_id=user_id,
                slot_id=slot_id,
                start_time=start_time,
                end_time=end_time,
                price_per_hour=price_per_hour,
                total_price=total_price,
                status='active'
            )
            session.add(booking)
            
            slot.is_occupied = True
            slot.last_updated = datetime.utcnow()
            
            parking_lot = slot.parking_lot
            parking_lot.available_slots -= 1
            parking_lot.updated_at = datetime.utcnow()
            
            session.flush()
            
            logger.info(f"Booking created: ID={booking.id}, Price Locked=${price_per_hour}/hr")
            
            return jsonify({
                'success': True,
                'data': {
                    'booking_id': booking.id,
                    'slot_number': slot.slot_number,
                    'parking_lot_name': parking_lot.name,
                    'start_time': booking.start_time.isoformat(),
                    'end_time': booking.end_time.isoformat(),
                    'price_per_hour': price_per_hour,
                    'total_price': total_price,
                    'duration_hours': duration_hours,
                    'is_peak_hour': is_peak
                }
            }), 201
            
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get booking details"""
    try:
        with db_manager.session_scope() as session:
            booking = session.query(Booking).filter(Booking.id == booking_id).first()
            
            if not booking:
                return jsonify({'success': False, 'error': 'Booking not found'}), 404
                
            return jsonify({
                'success': True,
                'data': {
                    'id': booking.id,
                    'user_id': booking.user_id,
                    'username': booking.user.username,
                    'slot_id': booking.slot_id,
                    'slot_number': booking.slot.slot_number,
                    'parking_lot_name': booking.slot.parking_lot.name,
                    'start_time': booking.start_time.isoformat(),
                    'end_time': booking.end_time.isoformat() if booking.end_time else None,
                    'price_per_hour': booking.price_per_hour,
                    'total_price': booking.total_price,
                    'status': booking.status,
                    'created_at': booking.created_at.isoformat()
                }
            })
    except Exception as e:
        logger.error(f"Error fetching booking {booking_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bookings/<int:booking_id>/complete', methods=['POST'])
def complete_booking(booking_id):
    """Complete a booking and free the slot"""
    try:
        with db_manager.session_scope() as session:
            booking = session.query(Booking).filter(Booking.id == booking_id).first()
            
            if not booking:
                return jsonify({'success': False, 'error': 'Booking not found'}), 404
                
            if booking.status != 'active':
                return jsonify({'success': False, 'error': 'Booking is not active'}), 400
                
            # Complete booking
            booking.status = 'completed'
            actual_end_time = datetime.now() # CHANGED: Local time
            
            # Calculate actual duration and price
            # Note: total_seconds returns seconds, divide by 3600 for hours
            actual_duration = (actual_end_time - booking.start_time).total_seconds() / 3600
            
            # Calculate and Cap Price
            raw_price = booking.price_per_hour * actual_duration
            actual_price = min(raw_price, config.MAX_DAILY_PRICE) # Cap at $25
            
            booking.total_price = actual_price
            booking.end_time = actual_end_time
            
            # Free the slot
            slot = booking.slot
            slot.is_occupied = False
            slot.last_updated = datetime.now() # CHANGED: Local time
            
            # Update parking lot available slots
            parking_lot = slot.parking_lot
            parking_lot.available_slots += 1
            parking_lot.updated_at = datetime.utcnow()
            
            logger.info(f"Booking completed: ID={booking_id}, Actual price=${actual_price:.2f}")
            
            return jsonify({
                'success': True,
                'message': 'Booking completed successfully',
                'data': {
                    'booking_id': booking.id,
                    'actual_duration_hours': round(actual_duration, 2),
                    'total_price': round(actual_price, 2),
                    'completed_at': actual_end_time.isoformat()
                }
            })
    except Exception as e:
        logger.error(f"Error completing booking {booking_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    """Cancel an active booking"""
    try:
        with db_manager.session_scope() as session:
            booking = session.query(Booking).filter(Booking.id == booking_id).first()
            
            if not booking:
                return jsonify({'success': False, 'error': 'Booking not found'}), 404
                
            if booking.status != 'active':
                return jsonify({'success': False, 'error': 'Booking is not active'}), 400
                
            # Cancel booking
            booking.status = 'cancelled'
            
            # Free the slot
            slot = booking.slot
            slot.is_occupied = False
            slot.last_updated = datetime.utcnow()
            
            # Update parking lot available slots
            parking_lot = slot.parking_lot
            parking_lot.available_slots += 1
            parking_lot.updated_at = datetime.utcnow()
            
            logger.info(f"Booking cancelled: ID={booking_id}")
            
            return jsonify({
                'success': True,
                'message': 'Booking cancelled successfully',
                'data': {
                    'booking_id': booking.id,
                    'status': booking.status
                }
            })
    except Exception as e:
        logger.error(f"Error cancelling booking {booking_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/<int:user_id>/bookings', methods=['GET'])
def get_user_bookings(user_id):
    """Get all bookings for a user"""
    try:
        status_filter = request.args.get('status')  # Optional: filter by status
        
        with db_manager.session_scope() as session:
            query = session.query(Booking).filter(Booking.user_id == user_id)
            
            if status_filter:
                query = query.filter(Booking.status == status_filter)
            
            bookings = query.order_by(Booking.created_at.desc()).all()
            
            bookings_data = [{
                'id': booking.id,
                'slot_number': booking.slot.slot_number,
                'parking_lot_name': booking.slot.parking_lot.name,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat() if booking.end_time else None,
                'price_per_hour': booking.price_per_hour,
                'total_price': booking.total_price,
                'status': booking.status,
                'created_at': booking.created_at.isoformat()
            } for booking in bookings]
            
            return jsonify({
                'success': True,
                'data': bookings_data,
                'count': len(bookings_data)
            })
    except Exception as e:
        logger.error(f"Error fetching user bookings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_system_stats():
    """Get overall system statistics"""
    try:
        stats = db_manager.get_parking_lot_stats()
        
        total_slots = sum(lot['total_slots'] for lot in stats)
        total_available = sum(lot['available_slots'] for lot in stats)
        total_occupied = total_slots - total_available
        overall_occupancy = (total_occupied / total_slots) * 100 if total_slots > 0 else 0
        
        with db_manager.session_scope() as session:
            # Get booking statistics
            total_bookings = session.query(Booking).count()
            active_bookings = session.query(Booking).filter(Booking.status == 'active').count()
            completed_bookings = session.query(Booking).filter(Booking.status == 'completed').count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_parking_lots': len(stats),
                'total_slots': total_slots,
                'available_slots': total_available,
                'occupied_slots': total_occupied,
                'overall_occupancy_rate': round(overall_occupancy, 2),
                'total_bookings': total_bookings,
                'active_bookings': active_bookings,
                'completed_bookings': completed_bookings,
                'parking_lots': stats
            }
        })
    except Exception as e:
        logger.error(f"Error fetching system stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        with db_manager.session_scope() as session:
            users = session.query(User).all()
            
            users_data = [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'created_at': user.created_at.isoformat()
            } for user in users]
            
            return jsonify({
                'success': True,
                'data': users_data,
                'count': len(users_data)
            })
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def initialize_server():
    """Initialize the cloud server"""
    logger.info("=" * 60)
    logger.info("Initializing Central Cloud Server...")
    logger.info("=" * 60)
    
    try:
        # Create database tables (only creates if they don't exist)
        db_manager.create_tables()
        logger.info("✓ Database tables ready")
        
        # Check if already initialized
        with db_manager.session_scope() as session:
            from cloud.models import ParkingLot
            lot_count = session.query(ParkingLot).count()
            
            if lot_count == 0:
                # Initialize parking lots and users
                db_manager.initialize_parking_lots()
                logger.info(f"✓ Initialized {config.NUM_PARKING_LOTS} parking lots")
                
                db_manager.initialize_test_users()
                logger.info("✓ Test users initialized")
            else:
                logger.info(f"✓ Database already initialized with {lot_count} parking lots")
        
        logger.info("=" * 60)
        logger.info("Central Cloud Server initialized successfully!")
        logger.info(f"Server running on http://{config.CLOUD_HOST}:{config.CLOUD_SERVER_PORT}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise

def run_server():
    """Run the Flask server"""
    initialize_server()
    app.run(
        host='0.0.0.0',
        port=config.CLOUD_SERVER_PORT,
        debug=config.DEBUG_MODE,
        threaded=True
    )


if __name__ == '__main__':
    run_server()