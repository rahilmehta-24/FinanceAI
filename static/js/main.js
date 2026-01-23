// FinanceAI - Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function () {
            if (this.value && !isNaN(this.value)) {
                // Keep the raw value but format display if needed
            }
        });
    });

    // Uppercase stock symbol inputs
    const symbolInputs = document.querySelectorAll('input[name="symbol"]');
    symbolInputs.forEach(input => {
        input.addEventListener('input', function () {
            this.value = this.value.toUpperCase();
        });
    });

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            // Skip loading state for delete forms (they redirect immediately)
            if (form.action && form.action.includes('/delete/')) {
                return;
            }

            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="loading">Loading...</span>';
            }
        });
    });
});

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Utility function to format percentage
function formatPercent(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .loading {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .loading::after {
        content: '';
        width: 1rem;
        height: 1rem;
        border: 2px solid transparent;
        border-top-color: currentColor;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
