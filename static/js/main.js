/*
 * EduTrack Pro - Main JavaScript
 */

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initDropdowns();
    initAlerts();
    initNotificationBadge();
});

// Sidebar Toggle
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileOverlay = document.getElementById('mobileOverlay');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.add('open');
            mobileOverlay.classList.add('show');
        });
    }
    
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            mobileOverlay.classList.remove('show');
        });
    }
}

// Dropdown Menus
function initDropdowns() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');
    const userBtn = document.getElementById('userBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    // Notification dropdown
    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationDropdown.classList.toggle('show');
            userDropdown.classList.remove('show');
            loadNotifications();
        });
        
        document.addEventListener('click', function() {
            notificationDropdown.classList.remove('show');
        });
    }
    
    // User dropdown
    if (userBtn && userDropdown) {
        userBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
            notificationDropdown.classList.remove('show');
        });
        
        document.addEventListener('click', function() {
            userDropdown.classList.remove('show');
        });
    }
    
    // Mark all read
    const markAllRead = document.getElementById('markAllRead');
    if (markAllRead) {
        markAllRead.addEventListener('click', function(e) {
            e.preventDefault();
            markAllNotificationsRead();
        });
    }
}

// Auto-dismiss alerts
function initAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    
    alerts.forEach(function(alert) {
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                alert.classList.remove('show');
                setTimeout(function() {
                    alert.remove();
                }, 150);
            });
        }
        
        // Auto dismiss after 4 seconds
        setTimeout(function() {
            alert.classList.remove('show');
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 150);
        }, 4000);
    });
}

// Notification Badge Update
function initNotificationBadge() {
    updateNotificationBadge();
    // Update every 60 seconds
    setInterval(updateNotificationBadge, 60000);
}

function updateNotificationBadge() {
    fetch('/api/notifications/unread-count/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const badge = document.getElementById('topbarNotificationBadge');
        if (badge) {
            badge.textContent = data.unread_count;
            if (data.unread_count > 0) {
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    })
    .catch(error => console.error('Error fetching notification count:', error));
}

function loadNotifications() {
    const notificationList = document.getElementById('notificationList');
    if (!notificationList) return;
    
    fetch('/api/notifications/unread-count/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.unread_count > 0) {
            // In a real implementation, fetch full notifications
            notificationList.innerHTML = '<p class="empty-text">You have ' + data.unread_count + ' unread notifications</p>';
        } else {
            notificationList.innerHTML = '<p class="empty-text">No new notifications</p>';
        }
    })
    .catch(error => {
        notificationList.innerHTML = '<p class="empty-text">Unable to load notifications</p>';
    });
}

function markAllNotificationsRead() {
    fetch('/api/notifications/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateNotificationBadge();
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking notifications as read:', error));
}

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toast notification
function showToast(message, type = 'info') {
    const container = document.querySelector('.messages-container') || createMessagesContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        <span>${message}</span>
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    container.appendChild(alert);
    
    setTimeout(function() {
        alert.classList.remove('show');
        setTimeout(function() {
            alert.remove();
        }, 150);
    }, 4000);
}

function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    return isValid;
}

// Export functions
window.getCookie = getCookie;
window.showToast = showToast;
window.validateForm = validateForm;
