// ============================================
// AUTENTICACIÓN - LOGIN Y REGISTRO
// ============================================

// Inicializar cuando cargue la página
document.addEventListener('DOMContentLoaded', () => {
    initAuthForms();
    checkAuthStatus();
});

// ============================================
// INICIALIZACIÓN
// ============================================

function initAuthForms() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        
        // Password strength indicator
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.addEventListener('input', updatePasswordStrength);
        }
    }
}

// ============================================
// LOGIN
// ============================================

async function handleLogin(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const remember = document.getElementById('remember').checked;
    
    // Validaciones básicas
    if (!username || !password) {
        showNotification('Por favor completa todos los campos', 'error');
        return;
    }
    
    // Loading state
    form.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        // Llamar al servicio de autenticación
        const response = await AuthService.login(username, password);
        
        // Guardar tokens
        saveToken(response.access, response.refresh);
        
        // Guardar info del usuario si viene
        if (response.user) {
            localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.user));
        }
        
        // Mostrar mensaje de éxito
        showNotification('¡Bienvenido de vuelta!', 'success');
        
        // Redirigir al dashboard o página principal
        setTimeout(() => {
            window.location.href = '../index.html';
        }, 1000);
        
    } catch (error) {
        console.error('Error en login:', error);
        showNotification(error.message || 'Error al iniciar sesión', 'error');
        
        form.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

// ============================================
// REGISTRO
// ============================================

async function handleRegister(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Obtener datos del formulario
    const data = {
        username: document.getElementById('username').value.trim(),
        email: document.getElementById('email').value.trim(),
        password: document.getElementById('password').value,
        first_name: document.getElementById('firstName').value.trim(),
        last_name: document.getElementById('lastName').value.trim(),
    };
    
    const confirmPassword = document.getElementById('confirmPassword').value;
    const termsAccepted = document.getElementById('terms').checked;
    
    // Validaciones
    if (!validateRegisterForm(data, confirmPassword, termsAccepted)) {
        return;
    }
    
    // Loading state
    form.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        // Nota: Necesitarás crear un endpoint de registro en tu API
        // Por ahora simularemos el registro
        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error?.message || 'Error al registrarse');
        }
        
        const result = await response.json();
        
        // Mostrar mensaje de éxito
        showNotification('¡Registro exitoso! Redirigiendo al login...', 'success');
        
        // Redirigir al login
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
        
    } catch (error) {
        console.error('Error en registro:', error);
        showNotification(error.message || 'Error al crear la cuenta', 'error');
        
        form.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

// ============================================
// VALIDACIONES
// ============================================

function validateRegisterForm(data, confirmPassword, termsAccepted) {
    // Validar campos vacíos
    if (!data.username || !data.email || !data.password || !data.first_name || !data.last_name) {
        showNotification('Por favor completa todos los campos', 'error');
        return false;
    }
    
    // Validar email
    if (!isValidEmail(data.email)) {
        showNotification('Por favor ingresa un email válido', 'error');
        return false;
    }
    
    // Validar username
    if (data.username.length < 3) {
        showNotification('El usuario debe tener al menos 3 caracteres', 'error');
        return false;
    }
    
    // Validar contraseña
    if (data.password.length < 8) {
        showNotification('La contraseña debe tener al menos 8 caracteres', 'error');
        return false;
    }
    
    // Validar confirmación de contraseña
    if (data.password !== confirmPassword) {
        showNotification('Las contraseñas no coinciden', 'error');
        return false;
    }
    
    // Validar términos
    if (!termsAccepted) {
        showNotification('Debes aceptar los términos y condiciones', 'error');
        return false;
    }
    
    return true;
}

// ============================================
// UTILIDADES
// ============================================

function togglePassword(fieldId = 'password') {
    const input = document.getElementById(fieldId);
    const icon = input.parentElement.querySelector('.toggle-password i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

function updatePasswordStrength() {
    const password = document.getElementById('password').value;
    const strengthIndicator = document.getElementById('passwordStrength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    
    // Calcular fortaleza
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    
    // Aplicar clase
    strengthIndicator.className = 'password-strength';
    
    if (strength <= 2) {
        strengthIndicator.classList.add('weak');
    } else if (strength <= 4) {
        strengthIndicator.classList.add('medium');
    } else {
        strengthIndicator.classList.add('strong');
    }
}

function checkAuthStatus() {
    // Si ya está autenticado, redirigir
    if (isAuthenticated() && !window.location.pathname.includes('dashboard')) {
        const currentPage = window.location.pathname;
        if (currentPage.includes('login') || currentPage.includes('register')) {
            window.location.href = '../index.html';
        }
    }
}

// ============================================
// LOGOUT
// ============================================

function logout() {
    AuthService.logout();
    showNotification('Sesión cerrada exitosamente', 'success');
}