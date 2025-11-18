"""
    Database Initialization Script
    Populates the database with sample data for testing
"""

import random
from datetime import datetime
from cloud.database import db_manager
from cloud.models import ParkingLot, ParkingSlot, User, Booking
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_database():
    logger.info("=" * 60)
    logger.info("INITIALIZING DATABASE WITH TEST DATA")
    logger.info("=" * 60)
    
    # Drop existing tables and recreate
    logger.info("Dropping existing tables...")
    db_manager.drop_tables()
    
    logger.info("Creating new tables...")
    db_manager.create_tables()
    
    # Initialize parking lots and slots
    logger.info("Creating parking lots and slots...")
    db_manager.initialize_parking_lots()
    
    # Initialize users
    logger.info("Creating test users...")
    create_users()
    
    # Create some fake physical occupancy (Sensors detecting cars)
    # We keep this so the dashboard isn't 100% empty/boring on start
    logger.info("Simulating parking occupancy...")
    simulate_occupancy()
    
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZED SUCCESSFULLY!")
    logger.info("=" * 60)
    
    # Show summary
    show_summary()


def create_users():
    # Create test users with our group members
    users_data = [
        {
            'username': 'Faisal Akbar',
            'email': 'faisal.akbar@ontariotechu.net',
            'phone': '100846786'
        },
        {
            'username': 'Fahad Hussain',
            'email': 'fahad.hussain@ontariotechu.net',
            'phone': '100816265'
        },
        {
            'username': 'Rajiv Lomada',
            'email': 'rajiv.lomada@ontariotechu.net',
            'phone': '100823689'
        },
        {
            'username': 'Saieashan Sathivel',
            'email': 'saieashan.sathivel@ontariotechu.net',
            'phone': '100818528'
        },
        {
            'username': 'Rishab Singh',
            'email': 'rishab.singh@ontariotechu.net',
            'phone': '100787473'
        }
    ]

    with db_manager.session_scope() as session:
        for user_data in users_data:
            # Check if user exists to avoid duplicates on re-runs
            existing = session.query(User).filter_by(email=user_data['email']).first()
            if not existing:
                user = User(**user_data)
                session.add(user)

    logger.info(f"✓ Created {len(users_data)} Group 12 users")


def simulate_occupancy():
    # Simulate realistic parking occupancy with random rates
    with db_manager.session_scope() as session:
        all_slots = session.query(ParkingSlot).all()

        # Randomly occupy slots in each lot with varying occupancy rates
        for lot_num in range(1, config.NUM_PARKING_LOTS + 1):
            lot_slots = [s for s in all_slots if s.parking_lot_id == lot_num]

            # Random occupancy rate between 20% and 60% (want room to book)
            occupancy_rate = random.uniform(0.20, 0.60)

            num_to_occupy = int(len(lot_slots) * occupancy_rate)
            slots_to_occupy = random.sample(lot_slots, num_to_occupy)

            for slot in slots_to_occupy:
                slot.is_occupied = True
                slot.last_updated = datetime.utcnow()

            # Update parking lot available slots
            parking_lot = session.query(ParkingLot).filter(
                ParkingLot.id == lot_num
            ).first()
            parking_lot.available_slots = len(lot_slots) - num_to_occupy

            logger.info(f"✓ Lot {lot_num}: {num_to_occupy}/{len(lot_slots)} slots occupied ({int(occupancy_rate*100)}%)")


def show_summary():
    with db_manager.session_scope() as session:
        num_lots = session.query(ParkingLot).count()
        num_slots = session.query(ParkingSlot).count()
        num_users = session.query(User).count()
        num_bookings = session.query(Booking).count()
        num_occupied = session.query(ParkingSlot).filter(
            ParkingSlot.is_occupied == True
        ).count()
        
        logger.info("\n" + "=" * 60)
        logger.info("DATABASE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Parking Lots:      {num_lots}")
        logger.info(f"Parking Slots:     {num_slots}")
        logger.info(f"Occupied Slots:    {num_occupied} ({int(num_occupied/num_slots*100)}%)")
        logger.info(f"Available Slots:   {num_slots - num_occupied}")
        logger.info(f"Users:             {num_users}")
        logger.info(f"Total Bookings:    {num_bookings}")
        logger.info("=" * 60)
        
        # Show parking lot details
        logger.info("\nPARKING LOT DETAILS:")
        logger.info("-" * 60)
        lots = session.query(ParkingLot).all()
        for lot in lots:
            occupancy = ((lot.total_slots - lot.available_slots) / lot.total_slots) * 100
            logger.info(f"{lot.name:15} | Available: {lot.available_slots:2}/{lot.total_slots:2} | Occupancy: {occupancy:.1f}%")
        logger.info("=" * 60 + "\n")


if __name__ == '__main__':
    initialize_database()