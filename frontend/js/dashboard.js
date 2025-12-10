// ============================================
// DASHBOARD - FUNCIONALIDAD
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Verificar autenticación
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }
    
    initDashboard();
});

// ============================================
// INICIALIZACIÓN
// ============================================

async function initDashboard() {
    loadUserInfo();
    await loadDashboardData();
    initEventListeners();
}

function loadUserInfo() {
    const userJson = localStorage.getItem(STORAGE_KEYS.USER);
    
    if (userJson) {
        try {
            const user = JSON.parse(userJson);
            document.getElementById('userName').textContent = user.username || 'Usuario';
            document.getElementById('userGreeting').textContent = user.first_name || user.username || 'Usuario';
        } catch (e) {
            console.error('Error parseando usuario:', e);
        }
    }
}

async function loadDashboardData() {
    try {
        await Promise.all([
            loadMyEvents(),
            loadMyTickets(),
            loadStats()
        ]);
    } catch (error) {
        console.error('Error cargando datos del dashboard:', error);
        showNotification('Error cargando datos', 'error');
    }
}

// ============================================
// CARGAR DATOS
// ============================================

async function loadMyEvents() {
    try {
        const events = await EventsService.getAll({ organizer: 'me' });
        const eventsCount = events.count || events.length || 0;
        
        document.getElementById('totalMyEvents').textContent = eventsCount;
        
        // Renderizar eventos recientes
        renderRecentEvents(events.results || events);
    } catch (error) {
        console.error('Error cargando eventos:', error);
        document.getElementById('totalMyEvents').textContent = '0';
    }
}

async function loadMyTickets() {
    try {
        const tickets = await TicketsService.getMyTickets();
        const ticketsCount = tickets.length || 0;
        
        document.getElementById('totalMyTickets').textContent = ticketsCount;
        
        // Renderizar tickets
        renderMyTickets(tickets);
    } catch (error) {
        console.error('Error cargando tickets:', error);
        document.getElementById('totalMyTickets').textContent = '0';
    }
}

async function loadStats() {
    try {
        // Aquí puedes cargar estadísticas adicionales
        document.getElementById('totalAttendees').textContent = '0';
        document.getElementById('totalRevenue').textContent = '$0';
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// ============================================
// RENDERIZADO
// ============================================

function renderRecentEvents(events) {
    const container = document.getElementById('recentEvents');
    
    if (!events || events.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-calendar"></i>
                <p>No tienes eventos creados</p>
                <button class="btn-primary" onclick="createEvent()">Crear Evento</button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = events.slice(0, 5).map(event => `
        <div class="event-item">
            <div class="event-info">
                <h4>${event.title}</h4>
                <p class="event-date">
                    <i class="fas fa-calendar"></i>
                    ${formatDate(event.start_date)}
                </p>
            </div>
            <div class="event-actions">
                <button class="btn-secondary btn-sm" onclick="viewEvent(${event.id})">
                    Ver
                </button>
            </div>
        </div>
    `).join('');
}

function renderMyTickets(tickets) {
    const container = document.getElementById('myTickets');
    
    if (!tickets || tickets.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-ticket-alt"></i>
                <p>No tienes tickets próximos</p>
                <button class="btn-primary" onclick="goToEvents()">Explorar Eventos</button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tickets.slice(0, 5).map(ticket => `
        <div class="ticket-item">
            <div class="ticket-info">
                <h4>${ticket.event_title || 'Evento'}</h4>
                <p class="ticket-code">
                    <i class="fas fa-qrcode"></i>
                    ${ticket.ticket_code}
                </p>
            </div>
            <span class="ticket-status ${ticket.status}">${ticket.status}</span>
        </div>
    `).join('');
}

// ============================================
// ACCIONES
// ============================================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
}

function createEvent() {
    showNotification('Función en desarrollo', 'info');
    // Aquí puedes redirigir a una página de creación de eventos
}

function viewTickets() {
    showNotification('Función en desarrollo', 'info');
    // Redirigir a vista de tickets
}

function viewAnalytics() {
    showNotification('Función en desarrollo', 'info');
    // Redirigir a analytics
}

function goToEvents() {
    window.location.href = '../index.html#events';
}

function viewEvent(eventId) {
    window.location.href = `../index.html?event=${eventId}`;
}

function logout() {
    if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
        AuthService.logout();
    }
}

// ============================================
// EVENT LISTENERS
// ============================================

function initEventListeners() {
    // Nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            
            // Add active to clicked
            item.classList.add('active');
            
            // Handle navigation
            const href = item.getAttribute('href');
            handleNavigation(href);
        });
    });
}

function handleNavigation(href) {
    // Aquí puedes manejar la navegación entre secciones
    console.log('Navegando a:', href);
    showNotification('Función en desarrollo', 'info');
}