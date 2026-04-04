/*
 * EduTrack Pro - Service Worker Registration
 * PWA Install Prompt Handler
 */

let deferredPrompt;
const installButton = document.getElementById('installButton');

// Register Service Worker (DISABLED - causes 500 error)
// Service worker functionality temporarily disabled
if ('serviceWorker' in navigator) {
    console.log('Service Worker support detected (disabled)');
    // navigator.serviceWorker.register('/service-worker.js')
    //     .then(function(registration) {
    //         console.log('ServiceWorker registration successful with scope: ', registration.scope);
    //     })
    //     .catch(function(error) {
    //         console.log('ServiceWorker registration failed: ', error);
    //     });
}

// Handle Install Prompt
window.addEventListener('beforeinstallprompt', function(e) {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show install button if it exists
    if (installButton) {
        installButton.style.display = 'flex';
    }
    
    // Log for debugging
    console.log('Install prompt available');
});

// Handle Install Button Click
if (installButton) {
    installButton.addEventListener('click', function() {
        if (deferredPrompt) {
            // Show the install prompt
            deferredPrompt.prompt();
            
            // Wait for the user's response
            deferredPrompt.userChoice.then(function(choiceResult) {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                    showToast('App installed successfully!', 'success');
                } else {
                    console.log('User dismissed the install prompt');
                }
                
                // Clear the deferred prompt
                deferredPrompt = null;
                
                // Hide the install button
                installButton.style.display = 'none';
            });
        }
    });
}

// Handle App Installed Event
window.addEventListener('appinstalled', function() {
    console.log('PWA installed successfully');
    showToast('EduTrack Pro installed!', 'success');
    
    // Hide install button
    if (installButton) {
        installButton.style.display = 'none';
    }
    
    // Clear deferred prompt
    deferredPrompt = null;
});

// Check if app is running as standalone (installed)
function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
}

// Log PWA status
if (isStandalone()) {
    console.log('Running as installed PWA');
} else {
    console.log('Running in browser');
}

// Handle online/offline status
window.addEventListener('online', function() {
    console.log('Back online');
    showToast('Back online', 'success');
    
    // Sync any pending attendance data
    if ('serviceWorker' in navigator && 'sync' in window.registration) {
        navigator.serviceWorker.ready.then(function(registration) {
            registration.sync.register('sync-attendance');
        });
    }
});

window.addEventListener('offline', function() {
    console.log('Gone offline');
    showToast('You are offline. Some features may be limited.', 'warning');
});

// Initial online/offline check
if (!navigator.onLine) {
    showToast('You are offline. Some features may be limited.', 'warning');
}

// Export for use in other scripts
window.isStandalone = isStandalone;
