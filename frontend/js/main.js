// ============================================
// EVENTHUB - JAVASCRIPT PRINCIPAL COMPLETO
// ============================================

// Estado global
const state = {
    events: [],
    categories: [],
    currentPage: 1,
    totalPages: 1,
    filters: {
        search: '',
        category: '',
        status: '',
        ordering: '-start_date'
    },
    selectedEvent: null
};

// ============================================
// INICIALIZACIÓN
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    // Verificar conexión con el backend
    await checkBackendConnection();
    
    // Cargar categorías
    await loadCategories();
    
    // Cargar eventos
    await loadEvents();
    
    // Event listeners
    setupEventListeners();
    
    // Verificar autenticación
    updateAuthUI();
});

// ============================================
// VERIFICACIÓN DE BACKEND
// ============================================

async function checkBackendConnection() {
    try {
        const health = await api.healthCheck();
        
        if (health.status === 'healthy') {
            console.log('✅ Conexión con backend establecida');
            showNotification('Conexión establecida con el servidor', 'success');
        } else {
            throw new Error('Backend no responde correctamente');
        }
    } catch (error) {
        console.error('❌ Error de conexión:', error);
        showNotification(
            'No se puede conectar con el servidor. Verifica que el backend esté corriendo en ' + API_CONFIG.BASE_URL,
            'error',
            10000
        );
    }
}

// ============================================
// CARGA DE DATOS
// ============================================

async function loadCategories() {
    try {
        const response = await api.getCategories();
        state.categories = response.results || response;
        renderCategories();
    } catch (error) {
        console.error('Error cargando categorías:', error);
        showNotification('Error cargando categorías', 'error');
    }
}

async function loadEvents() {
    try {
        showLoading();
        
        const params = {
            page: state.currentPage,
            search: state.filters.search || undefined,
            category: state.filters.category || undefined,
            status: state.filters.status || undefined,
            ordering: state.filters.ordering
        };
        
        // Limpiar parámetros undefined
        Object.keys(params).forEach(key => 
            params[key] === undefined && delete params[key]
        );
        
        const response = await api.getEvents(params);
        
        state.events = response.results || [];
        state.totalPages = Math.ceil((response.count || 0) / 12);
        
        renderEvents();
        renderPagination();
        
    } catch (error) {
        console.error('Error cargando eventos:', error);
        showNotification('Error cargando eventos: ' + error.message, 'error');
        state.events = [];
        renderEvents();
    } finally {
        hideLoading();
    }
}

// ============================================
// RENDERIZADO
// ============================================

function renderCategories() {
    const container = document.getElementById('categoriesContainer');
    if (!container) return;
    
    container.innerHTML = state.categories.map(category => `
        <button 
            class="category-btn ${state.filters.category == category.id ? 'active' : ''}"
            onclick="filterByCategory(${category.id})"
        >
            <i class="fas fa-${getCategoryIcon(category.name)}"></i>
            ${category.name}
        </button>
    `).join('');
}

function renderEvents() {
    const container = document.getElementById('eventsGrid');
    if (!container) return;
    
    if (state.events.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-calendar-times"></i>
                <h3>No se encontraron eventos</h3>
                <p>Intenta ajustar los filtros de búsqueda</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = state.events.map(event => createEventCard(event)).join('');
}

function createEventCard(event) {
    const imageUrl = event.image || 'https://via.placeholder.com/400x250?text=EventHub';
    const startDate = new Date(event.start_date);
    const formattedDate = formatDate(startDate);
    const venue = event.venue_name || 'Por confirmar';
    
    // Calcular disponibilidad
    const availability = event.total_capacity > 0 
        ? Math.round((event.available_capacity / event.total_capacity) * 100)
        : 0;
    
    let availabilityClass = 'high';
    if (availability < 20) availabilityClass = 'low';
    else if (availability < 50) availabilityClass = 'medium';
    
    return `
        <div class="event-card" onclick="openEventModal(${event.id})">
            <div class="event-image">
                <img src="${imageUrl}" alt="${event.title}" 
                     onerror="this.src='https://via.placeholder.com/400x250?text=EventHub'">
                <span class="event-status status-${event.status}">${getStatusText(event.status)}</span>
                ${event.is_featured ? '<span class="featured-badge"><i class="fas fa-star"></i> Destacado</span>' : ''}
            </div>
            <div class="event-content">
                <div class="event-category">
                    <i class="fas fa-${getCategoryIcon(event.category_name)}"></i>
                    ${event.category_name}
                </div>
                <h3 class="event-title">${event.title}</h3>
                <div class="event-info">
                    <div class="info-item">
                        <i class="fas fa-calendar"></i>
                        ${formattedDate}
                    </div>
                    <div class="info-item">
                        <i class="fas fa-map-marker-alt"></i>
                        ${venue}
                    </div>
                    <div class="info-item">
                        <i class="fas fa-users"></i>
                        ${event.available_capacity} / ${event.total_capacity} disponibles
                    </div>
                </div>
                <div class="event-availability">
                    <div class="availability-bar">
                        <div class="availability-fill availability-${availabilityClass}" 
                             style="width: ${availability}%"></div>
                    </div>
                    <span class="availability-text">${availability}% disponible</span>
                </div>
                <button class="btn btn-primary" onclick="event.stopPropagation(); openEventModal(${event.id})">
                    Ver Detalles
                    <i class="fas fa-arrow-right"></i>
                </button>
            </div>
        </div>
    `;
}

function renderPagination() {
    const container = document.getElementById('pagination');
    if (!container) return;
    
    if (state.totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <button 
            class="page-btn" 
            onclick="changePage(${state.currentPage - 1})"
            ${state.currentPage === 1 ? 'disabled' : ''}
        >
            <i class="fas fa-chevron-left"></i>
        </button>
    `;
    
    // Páginas
    for (let i = 1; i <= state.totalPages; i++) {
        if (
            i === 1 || 
            i === state.totalPages || 
            (i >= state.currentPage - 1 && i <= state.currentPage + 1)
        ) {
            html += `
                <button 
                    class="page-btn ${i === state.currentPage ? 'active' : ''}" 
                    onclick="changePage(${i})"
                >
                    ${i}
                </button>
            `;
        } else if (i === state.currentPage - 2 || i === state.currentPage + 2) {
            html += '<span class="page-dots">...</span>';
        }
    }
    
    // Botón siguiente
    html += `
        <button 
            class="page-btn" 
            onclick="changePage(${state.currentPage + 1})"
            ${state.currentPage === state.totalPages ? 'disabled' : ''}
        >
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    container.innerHTML = html;
}

// ============================================
// MODAL DE EVENTO
// ============================================

async function openEventModal(eventId) {
    try {
        showLoading();
        
        const event = await api.getEvent(eventId);
        state.selectedEvent = event;
        
        // Obtener tipos de tickets
        const ticketTypes = await api.getTicketTypes(eventId);
        
        renderEventModal(event, ticketTypes);
        
        const modal = document.getElementById('eventModal');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
    } catch (error) {
        console.error('Error cargando evento:', error);
        showNotification('Error cargando detalles del evento', 'error');
    } finally {
        hideLoading();
    }
}

function renderEventModal(event, ticketTypes) {
    const modalContent = document.getElementById('eventModalContent');
    if (!modalContent) return;
    
    const imageUrl = event.image || 'https://via.placeholder.com/800x400?text=EventHub';
    const startDate = new Date(event.start_date);
    const endDate = new Date(event.end_date);
    
    modalContent.innerHTML = `
        <button class="modal-close" onclick="closeEventModal()">
            <i class="fas fa-times"></i>
        </button>
        
        <div class="modal-image">
            <img src="${imageUrl}" alt="${event.title}" 
                 onerror="this.src='https://via.placeholder.com/800x400?text=EventHub'">
            ${event.is_featured ? '<span class="featured-badge"><i class="fas fa-star"></i> Destacado</span>' : ''}
        </div>
        
        <div class="modal-body">
            <div class="modal-header">
                <span class="event-category">
                    <i class="fas fa-${getCategoryIcon(event.category_name)}"></i>
                    ${event.category_name}
                </span>
                <span class="event-status status-${event.status}">${getStatusText(event.status)}</span>
            </div>
            
            <h2 class="modal-title">${event.title}</h2>
            
            <div class="modal-info-grid">
                <div class="info-card">
                    <i class="fas fa-calendar"></i>
                    <div>
                        <strong>Inicio</strong>
                        <p>${formatDate(startDate)}</p>
                    </div>
                </div>
                <div class="info-card">
                    <i class="fas fa-calendar-check"></i>
                    <div>
                        <strong>Fin</strong>
                        <p>${formatDate(endDate)}</p>
                    </div>
                </div>
                <div class="info-card">
                    <i class="fas fa-map-marker-alt"></i>
                    <div>
                        <strong>Ubicación</strong>
                        <p>${event.venue_name}</p>
                    </div>
                </div>
                <div class="info-card">
                    <i class="fas fa-users"></i>
                    <div>
                        <strong>Capacidad</strong>
                        <p>${event.available_capacity} / ${event.total_capacity}</p>
                    </div>
                </div>
            </div>
            
            <div class="modal-description">
                <h3>Descripción</h3>
                <p>${event.description || 'Sin descripción disponible.'}</p>
            </div>
            
            ${ticketTypes.results && ticketTypes.results.length > 0 ? `
                <div class="modal-tickets">
                    <h3>Tipos de Tickets</h3>
                    <div class="tickets-grid">
                        ${ticketTypes.results.map(ticket => `
                            <div class="ticket-card">
                                <h4>${ticket.name}</h4>
                                <p class="ticket-description">${ticket.description || ''}</p>
                                <div class="ticket-info">
                                    <span class="ticket-price">$${ticket.price}</span>
                                    <span class="ticket-available">${ticket.available_quantity} disponibles</span>
                                </div>
                                ${api.isAuthenticated() ? `
                                    <button class="btn btn-primary btn-sm" 
                                            onclick="purchaseTicket(${event.id}, ${ticket.id})"
                                            ${ticket.available_quantity === 0 ? 'disabled' : ''}>
                                        ${ticket.available_quantity === 0 ? 'Agotado' : 'Comprar'}
                                    </button>
                                ` : `
                                    <button class="btn btn-secondary btn-sm" 
                                            onclick="redirectToLogin()">
                                        Inicia sesión para comprar
                                    </button>
                                `}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

function closeEventModal() {
    const modal = document.getElementById('eventModal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
    state.selectedEvent = null;
}

// ============================================
// COMPRA DE TICKETS
// ============================================

async function purchaseTicket(eventId, ticketTypeId) {
    if (!api.isAuthenticated()) {
        redirectToLogin();
        return;
    }
    
    try {
        showLoading();
        
        const result = await api.purchaseTicket({
            ticket_type: ticketTypeId,
            quantity: 1
        });
        
        showNotification(
            '¡Ticket comprado exitosamente! Revisa tu email para la confirmación.',
            'success'
        );
        
        // Cerrar modal y recargar eventos
        closeEventModal();
        await loadEvents();
        
    } catch (error) {
        console.error('Error comprando ticket:', error);
        showNotification('Error al comprar ticket: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// FILTROS Y BÚSQUEDA
// ============================================

function setupEventListeners() {
    // Búsqueda
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                state.filters.search = e.target.value;
                state.currentPage = 1;
                loadEvents();
            }, 500);
        });
    }
    
    // Filtro de estado
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            state.filters.status = e.target.value;
            state.currentPage = 1;
            loadEvents();
        });
    }
    
    // Ordenamiento
    const sortFilter = document.getElementById('sortFilter');
    if (sortFilter) {
        sortFilter.addEventListener('change', (e) => {
            state.filters.ordering = e.target.value;
            state.currentPage = 1;
            loadEvents();
        });
    }
    
    // Cerrar modal al hacer click fuera
    const modal = document.getElementById('eventModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeEventModal();
            }
        });
    }
}

function filterByCategory(categoryId) {
    if (state.filters.category == categoryId) {
        state.filters.category = '';
    } else {
        state.filters.category = categoryId;
    }
    state.currentPage = 1;
    loadEvents();
}

function changePage(page) {
    if (page < 1 || page > state.totalPages) return;
    state.currentPage = page;
    loadEvents();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================
// UI DE AUTENTICACIÓN
// ============================================

function updateAuthUI() {
    const authButtons = document.querySelector('.auth-buttons');
    if (!authButtons) return;
    
    if (api.isAuthenticated()) {
        authButtons.innerHTML = `
            <a href="/pages/dashboard.html" class="btn btn-secondary">
                <i class="fas fa-th-large"></i>
                Dashboard
            </a>
            <button onclick="logout()" class="btn btn-outline">
                <i class="fas fa-sign-out-alt"></i>
                Cerrar Sesión
            </button>
        `;
    } else {
        authButtons.innerHTML = `
            <a href="/pages/login.html" class="btn btn-outline">
                <i class="fas fa-sign-in-alt"></i>
                Iniciar Sesión
            </a>
            <a href="/pages/register.html" class="btn btn-primary">
                <i class="fas fa-user-plus"></i>
                Registrarse
            </a>
        `;
    }
}

function logout() {
    if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
        api.logout();
    }
}

function redirectToLogin() {
    window.location.href = '/pages/login.html?redirect=' + encodeURIComponent(window.location.pathname);
}

// ============================================
// UTILIDADES
// ============================================

function getCategoryIcon(categoryName) {
    const icons = {
        'Música': 'music',
        'Deportes': 'futbol',
        'Tecnología': 'laptop-code',
        'Arte': 'palette',
        'Comida': 'utensils',
        'Negocios': 'briefcase',
        'Educación': 'graduation-cap',
        'default': 'calendar'
    };
    return icons[categoryName] || icons.default;
}

function getStatusText(status) {
    const texts = {
        'draft': 'Borrador',
        'published': 'Publicado',
        'ongoing': 'En curso',
        'completed': 'Finalizado',
        'cancelled': 'Cancelado'
    };
    return texts[status] || status;
}

function formatDate(date) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('es-ES', options);
}

function showLoading() {
    let loader = document.getElementById('globalLoader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'globalLoader';
        loader.className = 'global-loader';
        loader.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(loader);
    }
    loader.style.display = 'flex';
}

function hideLoading() {
    const loader = document.getElementById('globalLoader');
    if (loader) {
        loader.style.display = 'none';
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    notification.innerHTML = `
        <i class="fas fa-${icons[type] || icons.info}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}