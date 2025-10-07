// JavaScript principal para el Gestor de Inversiones

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar componentes de Bootstrap
    initBootstrapComponents();
    
    // Inicializar funcionalidades principales
    initFormValidation();
    initNumberFormatting();
    initToggleActions();
    initCharts();
    initStarRating();
    initChat();
    initSidebar();
    
    // Auto-dismiss alerts
    autoHideAlerts();
});

// ==========================================
// BOOTSTRAP COMPONENTS
// ==========================================

function initBootstrapComponents() {
    // Inicializar tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

function autoHideAlerts() {
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}

// ==========================================
// SIDEBAR MOBILE
// ==========================================

function initSidebar() {
    const sidebarToggle = document.querySelector('#sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Cerrar sidebar al hacer click fuera en móvil
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }
}

// ==========================================
// FORM VALIDATION
// ==========================================

function initFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

function initNumberFormatting() {
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !isNaN(this.value)) {
                if (this.step === '0.01') {
                    this.value = parseFloat(this.value).toFixed(2);
                }
            }
        });
    });
}

// ==========================================
// TOGGLE ACTIONS (ENABLE/DISABLE)
// ==========================================

function initToggleActions() {
    // Toggle inversiones
    const investmentToggleBtns = document.querySelectorAll('.toggle-investment');
    investmentToggleBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const investmentId = this.dataset.investmentId;
            toggleInvestment(investmentId, this);
        });
    });
    
    // Toggle organismos
    const organismToggleBtns = document.querySelectorAll('.toggle-organism');
    organismToggleBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const organismId = this.dataset.organismId;
            toggleOrganism(organismId, this);
        });
    });
}

function toggleInvestment(investmentId, button) {
    if (!confirm('¿Estás seguro de que deseas cambiar el estado de esta inversión?')) {
        return;
    }
    
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Procesando...';
    
    fetch(`/toggle_investment/${investmentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            
            // Actualizar UI
            const card = button.closest('.card');
            if (data.enabled) {
                card.classList.remove('disabled-investment');
                button.textContent = 'Deshabilitar';
                button.classList.remove('btn-success');
                button.classList.add('btn-warning');
            } else {
                card.classList.add('disabled-investment');
                button.textContent = 'Habilitar';
                button.classList.remove('btn-warning');
                button.classList.add('btn-success');
            }
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al procesar la solicitud', 'danger');
    })
    .finally(() => {
        button.disabled = false;
    });
}

function toggleOrganism(organismId, button) {
    if (!confirm('¿Estás seguro de que deseas cambiar el estado de este organismo?')) {
        return;
    }
    
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Procesando...';
    
    fetch(`/toggle_organism/${organismId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            
            // Actualizar UI
            const card = button.closest('.card');
            if (data.enabled) {
                card.classList.remove('disabled-organism');
                button.textContent = 'Deshabilitar';
                button.classList.remove('btn-success');
                button.classList.add('btn-warning');
            } else {
                card.classList.add('disabled-organism');
                button.textContent = 'Habilitar';
                button.classList.remove('btn-warning');
                button.classList.add('btn-success');
            }
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al procesar la solicitud', 'danger');
    })
    .finally(() => {
        button.disabled = false;
    });
}

// ==========================================
// STAR RATING
// ==========================================

function initStarRating() {
    const ratingForms = document.querySelectorAll('.rating-form');
    ratingForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitRating(form);
        });
        
        // Inicializar estrellas interactivas
        const starInputs = form.querySelectorAll('.star-rating input');
        starInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                updateStarDisplay(this);
            });
        });
    });
}

function updateStarDisplay(input) {
    const ratingContainer = input.closest('.star-rating');
    const value = parseFloat(input.value);
    const labels = ratingContainer.querySelectorAll('label');
    
    labels.forEach(function(label, index) {
        const labelValue = parseFloat(label.dataset.value || (5 - index));
        if (labelValue <= value) {
            label.style.color = '#ffc107';
        } else {
            label.style.color = '#ddd';
        }
    });
}

function submitRating(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            // Recargar calificaciones promedio si existe el contenedor
            const organismId = form.dataset.organismId;
            if (organismId) {
                loadAverageRatings(organismId);
            }
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al guardar la calificación', 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Guardar Calificación';
    });
}

function loadAverageRatings(organismId) {
    // Esta función se puede usar para recargar las calificaciones promedio
    // Implementar si se necesita actualización en tiempo real
}

// ==========================================
// CHAT FUNCTIONALITY
// ==========================================

function initChat() {
    // Chat de inversiones
    const investmentChatForms = document.querySelectorAll('.investment-chat-form');
    investmentChatForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            sendInvestmentMessage(form);
        });
    });
    
    // Chat de organismos
    const organismChatForms = document.querySelectorAll('.organism-chat-form');
    organismChatForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            sendOrganismMessage(form);
        });
    });
    
    // Auto-scroll en chats
    const chatContainers = document.querySelectorAll('.chat-messages');
    chatContainers.forEach(function(container) {
        container.scrollTop = container.scrollHeight;
    });
}

function sendInvestmentMessage(form) {
    const formData = new FormData(form);
    const messageInput = form.querySelector('input[name="message"]');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (!messageInput.value.trim()) {
        showAlert('El mensaje no puede estar vacío', 'warning');
        return;
    }
    
    submitBtn.disabled = true;
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageInput.value = '';
            addMessageToChat(data.data, 'investment');
            scrollChatToBottom(form.closest('.chat-container'));
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al enviar el mensaje', 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
    });
}

function sendOrganismMessage(form) {
    const formData = new FormData(form);
    const messageInput = form.querySelector('input[name="message"]');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (!messageInput.value.trim()) {
        showAlert('El mensaje no puede estar vacío', 'warning');
        return;
    }
    
    submitBtn.disabled = true;
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageInput.value = '';
            addMessageToChat(data.data, 'organism');
            scrollChatToBottom(form.closest('.chat-container'));
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al enviar el mensaje', 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
    });
}

function addMessageToChat(messageData, type) {
    const chatContainer = document.querySelector(`.${type}-chat-messages`);
    if (!chatContainer) return;
    
    const messageElement = createMessageElement(messageData);
    chatContainer.appendChild(messageElement);
    
    // Remover mensaje "no hay mensajes" si existe
    const noMessages = chatContainer.querySelector('.no-messages');
    if (noMessages) {
        noMessages.remove();
    }
}

function createMessageElement(messageData) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message fade-in';
    
    const timestamp = new Date(messageData.created_at).toLocaleString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    messageDiv.innerHTML = `
        <div class="chat-message-author">Tú</div>
        <div class="chat-message-time">${timestamp}</div>
        <div class="chat-message-content">${escapeHtml(messageData.message)}</div>
    `;
    
    return messageDiv;
}

function scrollChatToBottom(chatContainer) {
    const messagesContainer = chatContainer.querySelector('.chat-messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// ==========================================
// CHARTS
// ==========================================

function initCharts() {
    // Inicializar gráficos de portafolio
    initPortfolioCharts();
    
    // Inicializar gráficos de distribución de moneda
    initCurrencyDistributionCharts();
    
    // Inicializar gráficos del dashboard
    initDashboardCharts();
}

function initPortfolioCharts() {
    // Gráfico de portafolio USD
    const usdChartCanvas = document.getElementById('portfolioUSDChart');
    if (usdChartCanvas) {
        const usdData = JSON.parse(usdChartCanvas.dataset.chartData || '[]');
        createPieChart(usdChartCanvas, usdData, 'Portafolio USD');
    }
    
    // Gráfico de portafolio ARS
    const arsChartCanvas = document.getElementById('portfolioARSChart');
    if (arsChartCanvas) {
        const arsData = JSON.parse(arsChartCanvas.dataset.chartData || '[]');
        createPieChart(arsChartCanvas, arsData, 'Portafolio ARS');
    }
}

function initCurrencyDistributionCharts() {
    const currencyChartCanvas = document.getElementById('currencyDistributionChart');
    if (currencyChartCanvas) {
        const data = JSON.parse(currencyChartCanvas.dataset.chartData || '{}');
        createCurrencyDistributionChart(currencyChartCanvas, data);
    }
}

function initDashboardCharts() {
    const dashboardChartCanvas = document.getElementById('dashboardChart');
    if (dashboardChartCanvas) {
        const data = JSON.parse(dashboardChartCanvas.dataset.chartData || '{}');
        createDashboardChart(dashboardChartCanvas, data);
    }
}

function createPieChart(canvas, data, title) {
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.label),
            datasets: [{
                data: data.map(item => item.value),
                backgroundColor: [
                    '#007bff',
                    '#28a745',
                    '#ffc107',
                    '#dc3545',
                    '#6c757d',
                    '#17a2b8',
                    '#fd7e14'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        }
    });
}

function createCurrencyDistributionChart(canvas, data) {
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: ['#007bff', '#28a745'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Distribución por Moneda (Activas)',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        }
    });
}

function createDashboardChart(canvas, data) {
    // Implementar gráfico específico del dashboard según los datos disponibles
    console.log('Dashboard chart data:', data);
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container') || document.querySelector('main');
    if (!alertContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertAdjacentElement('afterbegin', alertDiv);
    
    // Auto-hide después de 5 segundos
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('es-AR').format(number);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ==========================================
// LOADING STATES
// ==========================================

function showLoading(element) {
    element.classList.add('loading');
    
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="spinner-border text-primary"></div>';
    
    element.style.position = 'relative';
    element.appendChild(overlay);
}

function hideLoading(element) {
    element.classList.remove('loading');
    const overlay = element.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// ==========================================
// GLOBAL ERROR HANDLING
// ==========================================

window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    // Opcionalmente mostrar un mensaje de error al usuario
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled Promise Rejection:', e.reason);
    // Opcionalmente mostrar un mensaje de error al usuario
});