// Smart Parking System - JavaScript

// Utility Functions
const formatCurrency = (amount) => {
    return `$${parseFloat(amount).toFixed(2)}`;
};

const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
};

const formatDuration = (hours) => {
    return `${hours} hour${hours !== 1 ? 's' : ''}`;
};

// API Helper Functions
const API_BASE_URL = '';

const apiCall = async (endpoint, options = {}) => {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

// Auto-refresh functionality
let autoRefreshInterval = null;

const startAutoRefresh = (callback, interval = 10000) => {
    stopAutoRefresh();
    autoRefreshInterval = setInterval(callback, interval);
};

const stopAutoRefresh = () => {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
};

// Toast Notifications
const showToast = (message, type = 'info') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 3000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
};

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Parking Lot Functions
const loadParkingLots = async () => {
    try {
        const data = await apiCall('/api/parking-lots');
        return data.data;
    } catch (error) {
        showToast('Failed to load parking lots', 'error');
        return [];
    }
};

const loadAvailableSlots = async (lotId = null) => {
    try {
        const endpoint = lotId ? `/api/available-slots?lot_id=${lotId}` : '/api/available-slots';
        const data = await apiCall(endpoint);
        return data.data;
    } catch (error) {
        showToast('Failed to load available slots', 'error');
        return [];
    }
};

const loadPricing = async () => {
    try {
        const data = await apiCall('/api/pricing');
        return data.data;
    } catch (error) {
        showToast('Failed to load pricing', 'error');
        return [];
    }
};

const loadSystemStats = async () => {
    try {
        const data = await apiCall('/api/stats');
        return data.data;
    } catch (error) {
        showToast('Failed to load system stats', 'error');
        return null;
    }
};

// Booking Functions
const createBooking = async (userId, slotId, durationHours) => {
    try {
        const data = await apiCall('/api/bookings', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                slot_id: slotId,
                duration_hours: durationHours
            })
        });
        showToast('Booking created successfully!', 'success');
        return data.data;
    } catch (error) {
        showToast(error.message || 'Failed to create booking', 'error');
        throw error;
    }
};

const getBooking = async (bookingId) => {
    try {
        const data = await apiCall(`/api/bookings/${bookingId}`);
        return data.data;
    } catch (error) {
        showToast('Failed to load booking', 'error');
        return null;
    }
};

const completeBooking = async (bookingId) => {
    try {
        const data = await apiCall(`/api/bookings/${bookingId}/complete`, {
            method: 'POST'
        });
        showToast('Booking completed!', 'success');
        return data.data;
    } catch (error) {
        showToast(error.message || 'Failed to complete booking', 'error');
        throw error;
    }
};

const cancelBooking = async (bookingId) => {
    try {
        const data = await apiCall(`/api/bookings/${bookingId}/cancel`, {
            method: 'POST'
        });
        showToast('Booking cancelled', 'success');
        return data.data;
    } catch (error) {
        showToast(error.message || 'Failed to cancel booking', 'error');
        throw error;
    }
};

const getUserBookings = async (userId, status = null) => {
    try {
        const endpoint = status 
            ? `/api/users/${userId}/bookings?status=${status}`
            : `/api/users/${userId}/bookings`;
        const data = await apiCall(endpoint);
        return data.data;
    } catch (error) {
        showToast('Failed to load bookings', 'error');
        return [];
    }
};

// Export functions for use in pages
window.parkingAPI = {
    loadParkingLots,
    loadAvailableSlots,
    loadPricing,
    loadSystemStats,
    createBooking,
    getBooking,
    completeBooking,
    cancelBooking,
    getUserBookings,
    startAutoRefresh,
    stopAutoRefresh,
    showToast
};

console.log('Smart Parking System - JavaScript loaded');