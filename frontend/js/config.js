// ============================================
// CONFIGURACIÓN DE LA API - EVENTHUB
// ============================================

const API_CONFIG = {
    // URL base de la API
    BASE_URL: 'http://localhost:8000/api',
    
    // Timeout para peticiones
    TIMEOUT: 30000,
    
    // Endpoints
    ENDPOINTS: {
        // Autenticación
        LOGIN: '/token/',
        REFRESH: '/token/refresh/',
        REGISTER: '/auth/register/',
        
        // Eventos
        EVENTS: '/events/events/',
        CATEGORIES: '/events/categories/',
        VENUES: '/events/venues/',
        
        // Tickets
        TICKET_TYPES: '/tickets/ticket-types/',
        TICKETS: '/tickets/tickets/',
        DISCOUNT_CODES: '/tickets/discount-codes/',
        
        // Asistentes
        ATTENDEES: '/attendees/attendees/',
        CHECKIN: '/attendees/checkin-logs/',
        SURVEYS: '/attendees/surveys/',
        
        // Patrocinadores
        SPONSORS: '/sponsors/sponsors/',
        SPONSORSHIPS: '/sponsors/sponsorships/',
        SPONSOR_TIERS: '/sponsors/sponsor-tiers/',
        
        // Usuario
        ME: '/auth/me/',
        
        // Health
        HEALTH: '/health/'
    },
    
    // Headers por defecto
    getHeaders: function(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (includeAuth) {
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        
        return headers;
    }
};

// Exportar para uso global
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}