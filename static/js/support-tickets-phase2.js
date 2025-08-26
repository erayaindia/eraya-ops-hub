/**
 * Support Tickets Phase 2 - Enhanced Functionality
 * Features: Drag & Drop, Notifications, Enhanced Interactions
 */

class SupportTicketsPhase2 {
  constructor() {
    this.notifications = [];
    this.draggedTicket = null;
    this.init();
  }

  init() {
    this.setupNotifications();
    this.setupDragAndDrop();
    this.setupEnhancedInteractions();
    this.setupMobileOptimizations();
  }

  // ===== PHASE 2: NOTIFICATION SYSTEM =====
  setupNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notificationContainer')) {
      const container = document.createElement('div');
      container.id = 'notificationContainer';
      container.className = 'notification-container';
      document.body.appendChild(container);
    }
  }

  showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const id = Date.now().toString();
    notification.id = `notification-${id}`;
    
    notification.innerHTML = `
      <div class="notification-header">
        <span class="notification-title">${this.getNotificationTitle(type)}</span>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
      <div class="notification-message">${message}</div>
      <div class="notification-progress"></div>
    `;

    const container = document.getElementById('notificationContainer');
    container.appendChild(notification);

    // Auto-remove after duration
    setTimeout(() => {
      if (notification.parentElement) {
        notification.classList.add('removing');
        setTimeout(() => notification.remove(), 300);
      }
    }, duration);

    // Store reference
    this.notifications.push({ id, element: notification });

    return id;
  }

  getNotificationTitle(type) {
    const titles = {
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
      info: 'Information'
    };
    return titles[type] || 'Information';
  }

  removeNotification(id) {
    const notification = this.notifications.find(n => n.id === id);
    if (notification) {
      notification.element.classList.add('removing');
      setTimeout(() => {
        notification.element.remove();
        this.notifications = this.notifications.filter(n => n.id !== id);
      }, 300);
    }
  }

  // ===== PHASE 2: DRAG & DROP FUNCTIONALITY =====
  setupDragAndDrop() {
    // Make ticket rows draggable
    document.addEventListener('DOMContentLoaded', () => {
      this.makeTicketsDraggable();
      this.setupDropZones();
    });
  }

  makeTicketsDraggable() {
    const ticketRows = document.querySelectorAll('#body tr');
    ticketRows.forEach(row => {
      row.setAttribute('draggable', 'true');
      row.classList.add('interactive');
      
      row.addEventListener('dragstart', (e) => this.handleDragStart(e, row));
      row.addEventListener('dragend', (e) => this.handleDragEnd(e, row));
    });
  }

  setupDropZones() {
    // Create drop zones for different statuses
    const statuses = ['new', 'open', 'waiting', 'closed'];
    const tableBody = document.querySelector('#body');
    
    if (tableBody) {
      // Add drop zone indicators
      statuses.forEach(status => {
        const dropZone = document.createElement('div');
        dropZone.className = 'status-drop-zone';
        dropZone.dataset.status = status;
        dropZone.innerHTML = `Drop tickets with ${status} status here`;
        
        // Insert after the table
        tableBody.parentElement.appendChild(dropZone);
      });
    }
  }

  handleDragStart(e, row) {
    this.draggedTicket = row;
    row.classList.add('dragging');
    
    // Create drag preview
    const preview = row.cloneNode(true);
    preview.classList.add('drag-preview');
    preview.style.position = 'fixed';
    preview.style.top = '-1000px';
    document.body.appendChild(preview);
    
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', row.outerHTML);
  }

  handleDragEnd(e, row) {
    row.classList.remove('dragging');
    this.draggedTicket = null;
    
    // Remove preview
    const preview = document.querySelector('.drag-preview');
    if (preview) preview.remove();
  }

  handleDrop(e, targetElement) {
    e.preventDefault();
    
    if (this.draggedTicket && targetElement.dataset.status) {
      const newStatus = targetElement.dataset.status;
      const ticketId = this.draggedTicket.dataset.ticketId;
      
      // Update ticket status
      this.updateTicketStatus(ticketId, newStatus);
      
      // Show notification
      this.showNotification(
        `Ticket ${ticketId} status updated to ${newStatus}`,
        'success'
      );
    }
  }

  updateTicketStatus(ticketId, newStatus) {
    // Here you would typically make an API call to update the status
    console.log(`Updating ticket ${ticketId} to status: ${newStatus}`);
    
    // For demo purposes, update the UI
    const ticketRow = document.querySelector(`[data-ticket-id="${ticketId}"]`);
    if (ticketRow) {
      const statusCell = ticketRow.querySelector('.status-pill');
      if (statusCell) {
        statusCell.className = `status-pill ${newStatus}`;
        statusCell.textContent = newStatus.toUpperCase();
      }
    }
  }

  // ===== PHASE 2: ENHANCED INTERACTIONS =====
  setupEnhancedInteractions() {
    // Enhanced row clicks
    document.addEventListener('click', (e) => {
      const row = e.target.closest('#body tr');
      if (row) {
        this.handleTicketClick(row);
      }
    });

    // Enhanced keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        const focusedRow = document.querySelector('#body tr:focus');
        if (focusedRow) {
          e.preventDefault();
          this.handleTicketClick(focusedRow);
        }
      }
    });
  }

  handleTicketClick(row) {
    // Add visual feedback
    row.classList.add('clicked');
    setTimeout(() => row.classList.remove('clicked'), 200);
    
    // Show ticket details
    this.showTicketDetails(row);
  }

  showTicketDetails(row) {
    // Extract ticket data from row
    const ticketData = this.extractTicketData(row);
    
    // Populate details sheet
    this.populateDetailsSheet(ticketData);
    
    // Show the sheet
    this.showDetailsSheet();
    
    // Show notification
    this.showNotification(
      `Viewing details for ticket ${ticketData.id}`,
      'info',
      3000
    );
  }

  extractTicketData(row) {
    // Extract data from table row
    const cells = row.querySelectorAll('td');
    return {
      id: cells[0]?.textContent || 'N/A',
      customer: cells[1]?.textContent || 'N/A',
      summary: cells[2]?.textContent || 'N/A',
      status: cells[3]?.textContent || 'N/A',
      priority: cells[4]?.textContent || 'N/A',
      channel: cells[5]?.textContent || 'N/A',
      created: cells[6]?.textContent || 'N/A'
    };
  }

  populateDetailsSheet(data) {
    // Populate the details sheet with ticket data
    const elements = {
      'sheetTitle': `Ticket #${data.id}`,
      'sheetSub': `Customer: ${data.customer}`,
      'd_status': `<span class="status-pill ${data.status.toLowerCase()}">${data.status}</span>`,
      'd_priority': `<span class="priority-pill ${data.priority.toLowerCase()}">${data.priority}</span>`,
      'd_channel': data.channel,
      'd_issue': 'General Inquiry',
      'd_name': data.customer,
      'd_contact': 'customer@example.com',
      'd_summary': data.summary,
      'd_description': 'Detailed description of the issue...',
      'd_order': 'ORD-12345',
      'd_tz': 'UTC+0',
      'd_created': data.created,
      'd_updated': data.created
    };

    Object.entries(elements).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) {
        element.innerHTML = value;
      }
    });
  }

  showDetailsSheet() {
    const sheetRoot = document.getElementById('sheetRoot');
    const sheet = document.getElementById('sheet');
    const overlay = document.getElementById('sheetOverlay');
    
    if (sheetRoot && sheet && overlay) {
      sheetRoot.classList.remove('hidden');
      
      // Animate overlay
      setTimeout(() => {
        overlay.style.opacity = '1';
      }, 10);
      
      // Animate sheet
      setTimeout(() => {
        sheet.style.transform = 'translateX(0)';
      }, 50);
    }
  }

  // ===== PHASE 2: MOBILE OPTIMIZATIONS =====
  setupMobileOptimizations() {
    // Touch-friendly interactions
    if ('ontouchstart' in window) {
      this.setupTouchInteractions();
    }
    
    // Responsive behavior
    this.setupResponsiveBehavior();
  }

  setupTouchInteractions() {
    // Add touch-specific event handlers
    document.addEventListener('touchstart', (e) => {
      const row = e.target.closest('#body tr');
      if (row) {
        row.classList.add('touch-active');
      }
    });

    document.addEventListener('touchend', (e) => {
      const row = e.target.closest('#body tr');
      if (row) {
        row.classList.remove('touch-active');
      }
    });
  }

  setupResponsiveBehavior() {
    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        this.adjustForScreenSize();
      }, 250);
    });
    
    // Initial adjustment
    this.adjustForScreenSize();
  }

  adjustForScreenSize() {
    const isMobile = window.innerWidth <= 768;
    const sheet = document.getElementById('sheet');
    
    if (sheet) {
      if (isMobile) {
        sheet.style.maxWidth = '100%';
        sheet.style.borderLeft = 'none';
        sheet.style.borderTop = '1px solid rgba(255, 255, 255, 0.15)';
      } else {
        sheet.style.maxWidth = '42rem';
        sheet.style.borderLeft = '1px solid rgba(255, 255, 255, 0.15)';
        sheet.style.borderTop = 'none';
      }
    }
  }

  // ===== PHASE 2: UTILITY FUNCTIONS =====
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // ===== PHASE 2: PUBLIC API =====
  showSuccess(message, duration = 5000) {
    return this.showNotification(message, 'success', duration);
  }

  showError(message, duration = 8000) {
    return this.showNotification(message, 'error', duration);
  }

  showWarning(message, duration = 6000) {
    return this.showNotification(message, 'warning', duration);
  }

  showInfo(message, duration = 5000) {
    return this.showNotification(message, 'info', duration);
  }

  // Update ticket status with drag & drop
  updateStatus(ticketId, newStatus) {
    return this.updateTicketStatus(ticketId, newStatus);
  }

  // Refresh the interface
  refresh() {
    this.showNotification('Refreshing support tickets...', 'info', 2000);
    // Add your refresh logic here
  }
}

// Initialize Phase 2 functionality when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.supportTicketsPhase2 = new SupportTicketsPhase2();
  
  // Show welcome notification
  setTimeout(() => {
    window.supportTicketsPhase2.showSuccess(
      'Phase 2 features loaded! Try drag & drop and enhanced interactions.',
      4000
    );
  }, 1000);
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SupportTicketsPhase2;
}
