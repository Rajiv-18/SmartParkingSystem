"""
Database manager for Smart Parking System
"""

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import config
from cloud.models import Base, ParkingLot, ParkingSlot, User, Booking, PricingLog, SensorLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=config.DEBUG_MODE)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")
        
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(self.engine)
        logger.info("Database tables dropped successfully")
        
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
            
    def get_available_slots(self, parking_lot_id=None):
        """Get all available parking slots"""
        with self.session_scope() as session:
            query = session.query(ParkingSlot).filter(ParkingSlot.is_occupied == False)
            if parking_lot_id:
                query = query.filter(ParkingSlot.parking_lot_id == parking_lot_id)
            slots = query.all()

            # Convert to dictionaries within session scope
            slots_data = [{
                'id': slot.id,
                'slot_number': slot.slot_number,
                'parking_lot_id': slot.parking_lot_id,
                'sensor_id': slot.sensor_id
            } for slot in slots]

            return slots_data
            
    def update_slot_occupancy(self, sensor_id, is_occupied):
        """Update slot occupancy status"""
        with self.session_scope() as session:
            slot = session.query(ParkingSlot).filter(ParkingSlot.sensor_id == sensor_id).first()
            if slot:
                old_status = slot.is_occupied
                slot.is_occupied = is_occupied
                slot.last_updated = datetime.now()
                
                # Update parking lot available slots
                parking_lot = slot.parking_lot
                if old_status != is_occupied:
                    if is_occupied:
                        parking_lot.available_slots -= 1
                    else:
                        parking_lot.available_slots += 1
                        
                # Log sensor data
                log = SensorLog(
                    sensor_id=sensor_id,
                    is_occupied=is_occupied,
                    gateway_id=parking_lot.gateway_id
                )
                session.add(log)
                
                logger.info(f"Updated slot {slot.slot_number}: occupied={is_occupied}")
                return True
            return False
            
    def get_parking_lot_stats(self):
        """Get statistics for all parking lots"""
        with self.session_scope() as session:
            lots = session.query(ParkingLot).all()
            stats = []
            for lot in lots:
                occupancy_rate = ((lot.total_slots - lot.available_slots) / lot.total_slots) * 100
                stats.append({
                    'id': lot.id,
                    'name': lot.name,
                    'location': lot.location,
                    'total_slots': lot.total_slots,
                    'available_slots': lot.available_slots,
                    'occupied_slots': lot.total_slots - lot.available_slots,
                    'occupancy_rate': round(occupancy_rate, 2),
                    'gateway_id': lot.gateway_id
                })
            return stats


# Global database manager instance
db_manager = DatabaseManager()