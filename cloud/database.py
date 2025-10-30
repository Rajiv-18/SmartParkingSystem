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
            
    def initialize_parking_lots(self):
        """Initialize parking lots with slots"""
        with self.session_scope() as session:
            # Check if already initialized
            existing = session.query(ParkingLot).first()
            if existing:
                logger.info("Parking lots already initialized")
                return

            # CHANGED: Specific Ontario Tech Locations
            founders_lots = [
                {"name": "Founders 1", "location": "Ontario Tech North Oshawa Campus"},
                {"name": "Founders 2", "location": "Ontario Tech North Oshawa Campus"},
                {"name": "Founders 3", "location": "Ontario Tech North Oshawa Campus"},
                {"name": "Founders 4", "location": "Ontario Tech North Oshawa Campus"},
                {"name": "Founders 5", "location": "Ontario Tech North Oshawa Campus"}
            ]

            # Create parking lots
            for i, lot_data in enumerate(founders_lots):
                lot_num = i + 1
                parking_lot = ParkingLot(
                    name=lot_data["name"],
                    location=lot_data["location"],
                    total_slots=config.SLOTS_PER_LOT,
                    available_slots=config.SLOTS_PER_LOT,
                    gateway_id=f"gateway_{lot_num}"
                )
                session.add(parking_lot)
                session.flush()

                # Create parking slots for each lot
                for slot_num in range(1, config.SLOTS_PER_LOT + 1):
                    # CHANGED: Format F<Lot>-<Slot> (e.g., F1-01)
                    slot_label = f"F{lot_num}-{slot_num:02d}"
                    
                    slot = ParkingSlot(
                        slot_number=slot_label,
                        parking_lot_id=parking_lot.id,
                        is_occupied=False,
                        sensor_id=f"sensor_{lot_num}_{slot_num:03d}"
                    )
                    session.add(slot)

            logger.info(f"Initialized {len(founders_lots)} Founders parking lots")

    def initialize_test_users(self):
        """Create test users for the system"""
        with self.session_scope() as session:
            # Check if users exist
            existing = session.query(User).first()
            if existing:
                logger.info("Test users already exist")
                return
                
            test_users = [
                User(username="john_doe", email="john@example.com", phone="555-0101"),
                User(username="jane_smith", email="jane@example.com", phone="555-0102"),
                User(username="bob_wilson", email="bob@example.com", phone="555-0103"),
            ]
            
            for user in test_users:
                session.add(user)
                
            logger.info(f"Created {len(test_users)} test users")
            
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
                slot.last_updated = datetime.now() # CHANGED: utcnow -> now
                
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
# Optimized session handling

# Optimized session handling

# Optimized session handling
