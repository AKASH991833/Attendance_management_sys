/*
 * EduTrack Pro - Calendar JavaScript
 */

// Open holiday modal for a specific date
function openHolidayModal(date, day) {
    const modal = document.getElementById('holidayModal');
    if (!modal) return;
    
    const dateInput = document.getElementById('holidayDate');
    const dateDisplay = document.getElementById('selectedDateDisplay');
    
    if (dateInput) {
        dateInput.value = date;
    }
    
    if (dateDisplay) {
        dateDisplay.textContent = new Date(date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    
    // Check if holiday exists for this date
    checkExistingHoliday(date);
    
    modal.classList.add('show');
}

// Close holiday modal
function closeHolidayModal() {
    const modal = document.getElementById('holidayModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Check if holiday exists for date
function checkExistingHoliday(date) {
    fetch(`/api/calendar/holidays/?month=${new Date(date).getMonth() + 1}&year=${new Date(date).getFullYear()}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const holiday = data.holidays.find(h => h.date === date);
        const holidayInfo = document.getElementById('existingHolidayInfo');
        const holidayForm = document.getElementById('holidayForm');
        
        if (holiday) {
            if (holidayInfo) {
                holidayInfo.innerHTML = `
                    <div class="holiday-detail">
                        <h4>${holiday.icon} ${holiday.title}</h4>
                        <span class="badge badge-${holiday.type}">${holiday.type}</span>
                    </div>
                `;
                holidayInfo.style.display = 'block';
            }
            if (holidayForm) {
                holidayForm.style.display = 'none';
            }
        } else {
            if (holidayInfo) {
                holidayInfo.style.display = 'none';
            }
            if (holidayForm) {
                holidayForm.style.display = 'block';
            }
        }
    })
    .catch(error => console.error('Error checking holiday:', error));
}

// Save holiday
function saveHoliday() {
    const date = document.getElementById('holidayDate')?.value;
    const title = document.getElementById('holidayTitle')?.value;
    const type = document.getElementById('holidayType')?.value;
    const description = document.getElementById('holidayDescription')?.value;
    
    if (!date || !title) {
        showToast('Please fill in required fields', 'error');
        return;
    }
    
    fetch('/api/calendar/holiday/add/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            date: date,
            title: title,
            type: type || 'holiday',
            description: description || ''
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Holiday added successfully', 'success');
            closeHolidayModal();
            // Reload page to show new holiday
            setTimeout(() => location.reload(), 500);
        } else {
            showToast(data.error || 'Failed to add holiday', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving holiday:', error);
        showToast('Failed to add holiday', 'error');
    });
}

// Delete holiday
function deleteHoliday(holidayId) {
    if (!confirm('Are you sure you want to delete this holiday?')) return;
    
    fetch(`/api/calendar/holiday/${holidayId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Holiday deleted successfully', 'success');
            closeHolidayModal();
            setTimeout(() => location.reload(), 500);
        } else {
            showToast(data.error || 'Failed to delete holiday', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting holiday:', error);
        showToast('Failed to delete holiday', 'error');
    });
}

// Navigate calendar
function navigateCalendar(month, year) {
    window.location.href = `/calendar/?month=${month}&year=${year}`;
}

// Initialize calendar interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers to calendar days
    const calendarDays = document.querySelectorAll('.calendar-day.has-attendance, .calendar-day.has-holiday');
    calendarDays.forEach(function(day) {
        day.addEventListener('click', function() {
            const date = this.dataset.date;
            const dayNum = this.dataset.day;
            if (date) {
                openHolidayModal(date, dayNum);
            }
        });
    });
    
    // Modal close handlers
    const modalClose = document.querySelector('.modal-close');
    const modalOverlay = document.querySelector('.modal-overlay');
    
    if (modalClose) {
        modalClose.addEventListener('click', closeHolidayModal);
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', closeHolidayModal);
    }
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeHolidayModal();
        }
    });
});
