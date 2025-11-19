# Smart Parking System - SOFE4790U Distributed Systems

A distributed IoT-enabled parking management system designed for the Ontario Tech North Oshawa Campus. This system utilizes edge computing, cloud synchronization, and dynamic pricing to optimize parking resource allocation.

## Project Overview

This project demonstrates core distributed systems principles by simulating a complete Smart Parking infrastructure:
* **IoT Sensor Layer:** Simulates physical sensors (ultrasonic/infrared) detecting vehicle presence.
* **Edge Computing:** Regional gateways aggregate sensor data, cache it for fault tolerance, and efficiently sync with the cloud.
* **Central Cloud:** Manages global state, dynamic pricing logic, and user bookings.
* **User Interface:** A real-time dashboard and booking portal for students and faculty.

## Key Features

### Distributed & Fault Tolerant
* **Edge Caching:** Gateways buffer sensor data if the cloud goes offline, ensuring no data loss during network partitions.
* **Asynchronous Sync:** Gateways upload data in batches to reduce network overhead.
* **Concurrency:** Multithreaded sensor simulation handles 50+ concurrent sensor nodes.

### Smart Logic
* **Dynamic Pricing:** Parking rates adjust automatically based on real-time occupancy and time of day (Peak vs. Off-Peak).
* **Price Locking:** When a user books a slot, the price is locked to prevent changes during the transaction.
* **Daily Cap:** Pricing logic includes a safety cap to prevent excessive charges.

### Campus Specifics
* **Locations:** Configured for Founders 1, Founders 2, Founders 3, Founders 4, and Founders 5.
* **Users:** Pre-loaded profiles for Group 12 members.

## Installation & Setup

### Prerequisites
* Python 3.8+
* pip

### 1. Install Dependencies
    pip install -r requirements.txt

### 2. Initialize Database
This script wipes the database and populates it with the Founders lots and group member profiles.
`python init_database.py`

### 3. Run the System
To demonstrate the distributed nature of the system, run each component in a separate terminal window:

Terminal 1: Central Cloud Server
`python -m cloud.central_server`

Terminal 2: Regional Gateway
`python -m gateway.regional_gateway`

Terminal 3: IoT Sensor Simulator
`python -m sensors.sensor_simulator`

Terminal 4: Web Application
`python -m web.app`

## Usage

### Live Dashboard
Visit http://localhost:8081 to see the real-time status of all Founders lots.
* **Visual Indicators:** Slots flash Green when a car leaves and Red when a car arrives.
* **Auto-Refresh:** The dashboard updates every 2 seconds via AJAX polling.

### Booking a Spot
1. Navigate to Book Now.
2. Select your profile (e.g., Fahad Hussain).
3. Choose a Lot (e.g., Founders 3).
4. Select a specific slot (e.g., F3-04).
5. Enter duration to see the calculated price.
6. Confirm: You will be redirected to the My Bookings portal.

### My Bookings
Visit http://localhost:8081/my-bookings to view your active reservations. You can Cancel a booking here, which immediately frees up the slot on the live dashboard.

## Team Members (Group 12)

* **Faisal Akbar** - Report and Presentation Lead
* **Fahad Hussain** - Backend & Gateway Architecture
* **Rajiv Lomada** - Database & Pricing Engine
* **Saieashan Sathivel** - Frontend & UI/UX
* **Rishab Singh** - Testing & Integration