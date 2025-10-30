"""Database models for Smart Parking System"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class ParkingLot(Base):
    """Represents a parking lot in the system"""
    __tablename__ = 'parking_lots'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=False)
    total_slots = Column(Integer, nullable=False)
    available_slots = Column(Integer, nullable=False)
    gateway_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    slots = relationship('ParkingSlot', back_populates='parking_lot', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ParkingLot(id={self.id}, name='{self.name}', available={self.available_slots}/{self.total_slots})>"


class ParkingSlot(Base):
    """Represents an individual parking slot"""
    __tablename__ = 'parking_slots'
    
    id = Column(Integer, primary_key=True)
    slot_number = Column(String(20), nullable=False)
    parking_lot_id = Column(Integer, ForeignKey('parking_lots.id'), nullable=False)
    is_occupied = Column(Boolean, default=False)
    sensor_id = Column(String(50), unique=True, nullable=False)
    last_updated = Column(DateTime, default=datetime.now)
    
    parking_lot = relationship('ParkingLot', back_populates='slots')
    bookings = relationship('Booking', back_populates='slot')
    
    def __repr__(self):
        return f"<ParkingSlot(id={self.id}, slot_number='{self.slot_number}', occupied={self.is_occupied})>"


class User(Base):
    """Represents a system user"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    
    bookings = relationship('Booking', back_populates='user')
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Booking(Base):
    """Represents a parking slot booking"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    slot_id = Column(Integer, ForeignKey('parking_slots.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    price_per_hour = Column(Float, nullable=False)
    total_price = Column(Float)
    status = Column(String(20), default='active')  # active, completed, cancelled
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='bookings')
    slot = relationship('ParkingSlot', back_populates='bookings')
    
    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, slot_id={self.slot_id}, status='{self.status}')>"


class PricingLog(Base):
    """Logs pricing changes for analytics"""
    __tablename__ = 'pricing_logs'
    
    id = Column(Integer, primary_key=True)
    parking_lot_id = Column(Integer, ForeignKey('parking_lots.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    occupancy_rate = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)
    adjusted_price = Column(Float, nullable=False)
    is_peak_hour = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<PricingLog(lot_id={self.parking_lot_id}, price={self.adjusted_price}, time={self.timestamp})>"


class SensorLog(Base):
    """Logs sensor data for monitoring and analytics"""
    __tablename__ = 'sensor_logs'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    is_occupied = Column(Boolean, nullable=False)
    gateway_id = Column(String(50), nullable=False)
    
    def __repr__(self):
        return f"<SensorLog(sensor_id='{self.sensor_id}', occupied={self.is_occupied}, time={self.timestamp})>"