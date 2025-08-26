// Exact sidebar JavaScript from /hub
let sidebarCollapsed = false;

// Logout function
async function logout() {
    const logoutBtn = document.getElementById('logoutBtn');
    
    try {
        // Show loading state
        if (logoutBtn) {
            logoutBtn.style.opacity = '0.6';
            logoutBtn.style.pointerEvents = 'none';
            const iconElement = logoutBtn.querySelector('.sidebar-icon');
            const textElement = logoutBtn.querySelector('.sidebar-text');
            if (iconElement) iconElement.textContent = '⏳';
            if (textElement) textElement.textContent = 'Logging out...';
        }
        
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (response.ok) {
            // Clear any stored session data
            localStorage.removeItem('session_id');
            sessionStorage.clear();
            
            // Show success state briefly
            if (logoutBtn) {
                const iconElement = logoutBtn.querySelector('.sidebar-icon');
                const textElement = logoutBtn.querySelector('.sidebar-text');
                if (iconElement) iconElement.textContent = '✓';
                if (textElement) textElement.textContent = 'Success!';
            }
            
            // Show logout message
            console.log('Logout successful');
            
            // Redirect to login page after brief delay
            setTimeout(() => {
                window.location.href = '/login';
            }, 500);
        } else {
            console.error('Logout failed');
            // Still redirect to login page even if logout API fails
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Still redirect to login page even if there's an error
        window.location.href = '/login';
    }
}

function toggleSidebar() {
    if (window.innerWidth >= 768) {
        // Desktop behavior
        sidebarCollapsed = !sidebarCollapsed;
        if (sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            sidebarToggle.innerHTML = '<span class="text-lg">⟩</span>';
        } else {
            sidebar.classList.remove('collapsed');
            sidebarToggle.innerHTML = '<span class="text-lg">⟨</span>';
        }
        localStorage.setItem('sidebarCollapsed', sidebarCollapsed.toString());
        document.querySelector('.main-content').style.marginLeft = sidebarCollapsed ? '80px' : '280px';
    } else {
        // Mobile behavior
        sidebar.classList.toggle('mobile-open');
    }
}

// Initialize sidebar
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mainContent = document.querySelector('.main-content');

    // Restore sidebar collapsed state
    const savedCollapsed = localStorage.getItem('sidebarCollapsed');
    if (savedCollapsed === 'true' && window.innerWidth >= 768) {
        sidebarCollapsed = true;
        sidebar.classList.add('collapsed');
        mainContent.style.marginLeft = '80px';
        sidebarToggle.innerHTML = '<span class="text-lg">⟩</span>';
    }

    // Wire up toggle button
    sidebarToggle.addEventListener('click', toggleSidebar);

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768) {
            sidebar.classList.remove('mobile-open');
            mainContent.style.marginLeft = sidebarCollapsed ? '80px' : '280px';
        } else {
            mainContent.style.marginLeft = '0';
        }
    });

    // Close mobile sidebar when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 768 && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
            sidebar.classList.remove('mobile-open');
        }
    });
});