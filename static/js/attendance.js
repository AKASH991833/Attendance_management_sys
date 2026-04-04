/*
 * EduTrack Pro - Attendance JavaScript
 */

// Toggle Select All checkboxes
function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll('.student-checkbox');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = source.checked;
        checkbox.value = source.checked ? 'present' : 'absent';
    });
}

// Mark all students with specific status
function markAll(status) {
    const checkboxes = document.querySelectorAll('.student-checkbox');
    const selects = document.querySelectorAll('.status-select');
    
    checkboxes.forEach(function(checkbox, index) {
        checkbox.checked = status === 'present';
    });
    
    selects.forEach(function(select) {
        select.value = status;
    });
}

// Save attendance
function saveAttendance() {
    const form = document.getElementById('attendanceForm');
    if (!form) return;
    
    const date = form.querySelector('[name="date"]').value;
    const batchId = form.querySelector('[name="batch_id"]').value;
    const slotId = document.getElementById('id_slot')?.value || null;
    
    if (!date || !batchId) {
        showToast('Please select date and batch', 'error');
        return;
    }
    
    const students = [];
    const rows = document.querySelectorAll('#attendanceList tr');
    
    rows.forEach(function(row) {
        const studentId = row.dataset.studentId;
        const checkbox = row.querySelector('.student-checkbox');
        const statusSelect = row.querySelector('.status-select');
        const notesInput = row.querySelector('[name^="notes_"]');
        
        students.push({
            student_id: parseInt(studentId),
            status: statusSelect ? statusSelect.value : (checkbox.checked ? 'present' : 'absent'),
            notes: notesInput ? notesInput.value : ''
        });
    });
    
    const saveStatus = document.getElementById('saveStatus');
    if (saveStatus) {
        saveStatus.textContent = 'Saving...';
        saveStatus.className = 'save-status saving';
    }
    
    fetch('/api/attendance/save/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            date: date,
            batch_id: parseInt(batchId),
            slot_id: slotId ? parseInt(slotId) : null,
            students: students
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (saveStatus) {
                saveStatus.textContent = data.message;
                saveStatus.className = 'save-status success';
            }
            showToast(data.message, 'success');
            
            // Store saved data for edit mode
            window.savedAttendance = {
                date: date,
                batchId: batchId,
                students: students
            };
        } else {
            if (saveStatus) {
                saveStatus.textContent = data.error;
                saveStatus.className = 'save-status error';
            }
            showToast(data.error || 'Failed to save attendance', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving attendance:', error);
        if (saveStatus) {
            saveStatus.textContent = 'Error saving attendance';
            saveStatus.className = 'save-status error';
        }
        showToast('Failed to save attendance', 'error');
    });
}

// Load existing attendance records if in edit mode
function loadExistingAttendance() {
    if (typeof existingRecords === 'undefined' || !existingRecords) return;
    
    Object.keys(existingRecords).forEach(function(studentId) {
        const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
        if (!row) return;
        
        const record = existingRecords[studentId];
        const statusSelect = row.querySelector('.status-select');
        const notesInput = row.querySelector('[name^="notes_"]');
        const checkbox = row.querySelector('.student-checkbox');
        
        if (statusSelect) {
            statusSelect.value = record.status;
        }
        
        if (notesInput && record.notes) {
            notesInput.value = record.notes;
        }
        
        if (checkbox) {
            checkbox.checked = record.status === 'present';
        }
    });
}

// Load timetable slots when batch is selected
function loadTimetableSlots() {
    const batchSelect = document.getElementById('id_batch');
    const slotSelect = document.getElementById('id_slot');
    const dateInput = document.getElementById('id_date');
    
    if (!batchSelect || !slotSelect || !dateInput) return;
    
    batchSelect.addEventListener('change', function() {
        const batchId = this.value;
        const date = dateInput.value;
        
        if (!batchId || !date) {
            slotSelect.innerHTML = '<option value="">Select Slot</option>';
            return;
        }
        
        // Get day of week from date
        const dateObj = new Date(date);
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = days[dateObj.getDay()];
        
        // Fetch slots for this batch and day
        // This would need a backend endpoint to fetch slots
        // For now, we'll just clear the slots
        slotSelect.innerHTML = '<option value="">Select Slot</option>';
    });
    
    dateInput.addEventListener('change', function() {
        // Trigger batch change to reload slots
        batchSelect.dispatchEvent(new Event('change'));
    });
}

// Check if attendance already exists
function checkAttendanceExists() {
    const date = document.getElementById('id_date')?.value;
    const batchId = document.getElementById('id_batch')?.value;
    const slotId = document.getElementById('id_slot')?.value;
    
    if (!date || !batchId) return;
    
    const url = `/api/attendance/check/?date=${date}&batch_id=${batchId}${slotId ? '&slot_id=' + slotId : ''}`;
    
    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.exists) {
            showToast('Attendance already marked for this date. Loading in edit mode.', 'info');
        }
    })
    .catch(error => console.error('Error checking attendance:', error));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadExistingAttendance();
    loadTimetableSlots();
    
    // Check for existing attendance on page load
    const dateInput = document.getElementById('id_date');
    if (dateInput) {
        dateInput.addEventListener('change', checkAttendanceExists);
    }
});
