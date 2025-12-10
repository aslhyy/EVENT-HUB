// ============================================
// CLIENTE API - EVENTHUB
// ============================================

class APIClient {
    constructor() {
        this.baseUrl = API_CONFIG.BASE_URL;
        this.timeout = API_CONFIG.TIMEOUT;
    }

    // Método genérico para hacer peticiones
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...API_CONFIG.getHeaders(options.auth !== false),
                ...options.headers
            }
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            // Si el token expiró, intentar refrescar
            if (response.status === 401 && options.retry !== false) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    return this.request(endpoint, { ...options, retry: false });
                }
            }

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.detail || data.error || `Error ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            if (error.name === 'AbortError') {
                throw new Error('La petición tardó demasiado tiempo');
            }
            throw error;
        }
    }

    // Métodos HTTP
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // === AUTENTICACIÓN ===
    
    async login(username, password) {
        try {
            const data = await this.post(API_CONFIG.ENDPOINTS.LOGIN, {
                username,
                password
            });
            
            if (data.access) {
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);
                return { success: true, data };
            }
            
            return { success: false, error: 'No se recibió token' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async register(userData) {
        try {
            const data = await this.post(API_CONFIG.ENDPOINTS.REGISTER, userData);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async refreshToken() {
        try {
            const refresh = localStorage.getItem('refresh_token');
            if (!refresh) return false;

            const data = await this.post(API_CONFIG.ENDPOINTS.REFRESH, {
                refresh
            });

            if (data.access) {
                localStorage.setItem('access_token', data.access);
                return true;
            }
            return false;
        } catch (error) {
            this.logout();
            return false;
        }
    }

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/pages/login.html';
    }

    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    }

    async getCurrentUser() {
        try {
            return await this.get(API_CONFIG.ENDPOINTS.ME);
        } catch (error) {
            console.error('Error getting current user:', error);
            return null;
        }
    }

    // === EVENTOS ===
    
    async getEvents(params = {}) {
        return this.get(API_CONFIG.ENDPOINTS.EVENTS, params);
    }

    async getEvent(id) {
        return this.get(`${API_CONFIG.ENDPOINTS.EVENTS}${id}/`);
    }

    async createEvent(eventData) {
        return this.post(API_CONFIG.ENDPOINTS.EVENTS, eventData);
    }

    async updateEvent(id, eventData) {
        return this.patch(`${API_CONFIG.ENDPOINTS.EVENTS}${id}/`, eventData);
    }

    async deleteEvent(id) {
        return this.delete(`${API_CONFIG.ENDPOINTS.EVENTS}${id}/`);
    }

    async getEventStats(id) {
        return this.get(`${API_CONFIG.ENDPOINTS.EVENTS}${id}/stats/`);
    }

    // === CATEGORÍAS ===
    
    async getCategories() {
        return this.get(API_CONFIG.ENDPOINTS.CATEGORIES);
    }

    // === VENUES ===
    
    async getVenues() {
        return this.get(API_CONFIG.ENDPOINTS.VENUES);
    }

    // === TICKETS ===
    
    async getTicketTypes(eventId) {
        return this.get(API_CONFIG.ENDPOINTS.TICKET_TYPES, { event: eventId });
    }

    async getMyTickets() {
        return this.get(`${API_CONFIG.ENDPOINTS.TICKETS}my_tickets/`);
    }

    async purchaseTicket(ticketData) {
        return this.post(`${API_CONFIG.ENDPOINTS.TICKETS}purchase/`, ticketData);
    }

    async validateDiscountCode(code, eventId) {
        return this.post(`${API_CONFIG.ENDPOINTS.DISCOUNT_CODES}validate/`, {
            code,
            event: eventId
        });
    }

    // === ASISTENTES ===
    
    async registerAttendee(attendeeData) {
        return this.post(API_CONFIG.ENDPOINTS.ATTENDEES, attendeeData);
    }

    async checkIn(ticketId) {
        return this.post(`${API_CONFIG.ENDPOINTS.CHECKIN}check_in/`, {
            ticket: ticketId
        });
    }

    // === PATROCINADORES ===
    
    async getSponsors(params = {}) {
        return this.get(API_CONFIG.ENDPOINTS.SPONSORS, params);
    }

    async getSponsorTiers() {
        return this.get(API_CONFIG.ENDPOINTS.SPONSOR_TIERS);
    }

    async createSponsorship(sponsorshipData) {
        return this.post(API_CONFIG.ENDPOINTS.SPONSORSHIPS, sponsorshipData);
    }

    // === HEALTH CHECK ===
    
    async healthCheck() {
        try {
            return await this.get(API_CONFIG.ENDPOINTS.HEALTH);
        } catch (error) {
            return { status: 'error', message: error.message };
        }
    }
}

// Instancia global
const api = new APIClient();