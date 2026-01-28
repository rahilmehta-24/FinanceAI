// Portfolio CRUD Operations
class PortfolioManager {
    constructor() {
        this.editingRow = null;
        this.originalData = {};
        this.init();
    }

    init() {
        // Attach event listeners to all edit and delete buttons
        document.querySelectorAll('.btn-edit').forEach(btn => {
            btn.addEventListener('click', (e) => this.enableEdit(e.target.closest('tr')));
        });

        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => this.deleteHolding(e.target.closest('tr')));
        });
    }

    enableEdit(row) {
        // Prevent multiple rows from being edited
        if (this.editingRow && this.editingRow !== row) {
            this.showMessage('Please save or cancel the current edit first', 'warning');
            return;
        }

        const id = row.dataset.holdingId;
        this.editingRow = row;

        // Store original values
        this.originalData[id] = {
            quantity: row.querySelector('.quantity').textContent,
            buy_price: row.querySelector('.buy-price').textContent.replace('₹', ''),
            buy_date: row.querySelector('.buy-date').dataset.date,
            sector: row.querySelector('.sector').textContent
        };

        // Switch to edit mode
        row.classList.add('editing');

        // Replace text with inputs
        const quantity = this.originalData[id].quantity;
        const buyPrice = this.originalData[id].buy_price;
        const buyDate = this.originalData[id].buy_date;
        const sector = this.originalData[id].sector;

        row.querySelector('.quantity').innerHTML = `
            <input type="number" class="edit-input" value="${quantity}" min="0.01" step="0.01" required>
        `;

        row.querySelector('.buy-price').innerHTML = `
            <input type="number" class="edit-input" value="${buyPrice}" min="0.01" step="0.01" required>
        `;

        row.querySelector('.buy-date').innerHTML = `
            <input type="date" class="edit-input" value="${buyDate}" required>
        `;

        row.querySelector('.sector').innerHTML = `
            <input type="text" class="edit-input" value="${sector}" maxlength="50">
        `;

        // Replace action buttons
        row.querySelector('.actions').innerHTML = `
            <button class="btn btn-success btn-sm btn-save" title="Save">✅</button>
            <button class="btn btn-ghost btn-sm btn-cancel" title="Cancel">❌</button>
        `;

        // Attach save/cancel listeners
        row.querySelector('.btn-save').addEventListener('click', () => this.saveEdit(row));
        row.querySelector('.btn-cancel').addEventListener('click', () => this.cancelEdit(row));
    }

    async saveEdit(row) {
        const id = row.dataset.holdingId;

        // Get values from inputs
        const quantity = parseFloat(row.querySelector('.quantity input').value);
        const buyPrice = parseFloat(row.querySelector('.buy-price input').value);
        const buyDate = row.querySelector('.buy-date input').value;
        const sector = row.querySelector('.sector input').value.trim();

        // Validate
        if (!quantity || quantity <= 0) {
            this.showMessage('Quantity must be greater than 0', 'error');
            return;
        }

        if (!buyPrice || buyPrice <= 0) {
            this.showMessage('Buy price must be greater than 0', 'error');
            return;
        }

        if (!buyDate) {
            this.showMessage('Buy date is required', 'error');
            return;
        }

        // Show loading state
        row.classList.add('loading');
        const saveBtn = row.querySelector('.btn-save');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '⏳';

        try {
            const response = await fetch(`/portfolio/api/holdings/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quantity: quantity,
                    buy_price: buyPrice,
                    buy_date: buyDate,
                    sector: sector
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update row with new data
                this.updateRowData(row, data.holding);
                this.exitEditMode(row);
                this.showMessage(data.message, 'success');

                // Refresh portfolio totals
                this.refreshPortfolioTotals();
            } else {
                this.showMessage(data.error || 'Failed to update holding', 'error');
                saveBtn.disabled = false;
                saveBtn.innerHTML = '✅';
            }
        } catch (error) {
            console.error('Error updating holding:', error);
            this.showMessage('Network error. Please try again.', 'error');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '✅';
        } finally {
            row.classList.remove('loading');
        }
    }

    cancelEdit(row) {
        const id = row.dataset.holdingId;
        const original = this.originalData[id];

        // Restore original values
        row.querySelector('.quantity').textContent = original.quantity;
        row.querySelector('.buy-price').textContent = `₹${parseFloat(original.buy_price).toFixed(2)}`;
        row.querySelector('.buy-date').innerHTML = `
            <span data-date="${original.buy_date}">${this.formatDate(original.buy_date)}</span>
        `;
        row.querySelector('.sector').textContent = original.sector || 'N/A';

        this.exitEditMode(row);
    }

    exitEditMode(row) {
        row.classList.remove('editing');

        // Restore action buttons
        row.querySelector('.actions').innerHTML = `
            <button class="btn btn-ghost btn-sm btn-edit" title="Edit">📝</button>
            <button class="btn btn-ghost btn-sm btn-delete text-danger" title="Delete">🗑️</button>
        `;

        // Re-attach listeners
        row.querySelector('.btn-edit').addEventListener('click', (e) => this.enableEdit(e.target.closest('tr')));
        row.querySelector('.btn-delete').addEventListener('click', (e) => this.deleteHolding(e.target.closest('tr')));

        this.editingRow = null;
    }

    updateRowData(row, holding) {
        // Update all cells with new data
        row.querySelector('.quantity').textContent = holding.quantity;
        row.querySelector('.buy-price').textContent = `₹${parseFloat(holding.buy_price).toFixed(2)}`;
        row.querySelector('.current-price').textContent = `₹${parseFloat(holding.current_price).toFixed(2)}`;
        row.querySelector('.current-value').textContent = `₹${parseFloat(holding.current_value).toFixed(2)}`;

        const gainLossCell = row.querySelector('.gain-loss');
        const gainLoss = holding.gain_loss;
        const gainLossPct = holding.gain_loss_pct;

        gainLossCell.className = 'gain-loss ' + (gainLoss >= 0 ? 'text-success' : 'text-danger');
        gainLossCell.innerHTML = `
            ${gainLoss >= 0 ? '+' : ''}₹${parseFloat(gainLoss).toFixed(2)}
            <small>(${parseFloat(gainLossPct).toFixed(2)}%)</small>
        `;

        row.querySelector('.buy-date').innerHTML = `
            <span data-date="${holding.buy_date}">${this.formatDate(holding.buy_date)}</span>
        `;
        row.querySelector('.sector').textContent = holding.sector || 'N/A';

        // Add success animation
        row.classList.add('row-updated');
        setTimeout(() => row.classList.remove('row-updated'), 1000);
    }

    async deleteHolding(row) {
        const id = row.dataset.holdingId;
        const symbol = row.querySelector('.symbol').textContent;

        // Get all holding IDs for this consolidated row
        let holdingIds = [id];
        try {
            const idsAttr = row.dataset.holdingIds;
            if (idsAttr) {
                holdingIds = JSON.parse(idsAttr);
            }
        } catch (e) {
            // Fallback to single ID if parsing fails
            console.log('Using single ID fallback');
        }

        const lotCount = holdingIds.length;
        const confirmMessage = lotCount > 1
            ? `Are you sure you want to remove all ${lotCount} lots of ${symbol} from your portfolio?`
            : `Are you sure you want to remove ${symbol} from your portfolio?`;

        // Show confirmation
        if (!confirm(confirmMessage)) {
            return;
        }

        // Show loading state
        row.classList.add('deleting');

        try {
            // Delete all lots for this holding
            let deleteSuccess = true;
            let lastMessage = '';

            for (const holdingId of holdingIds) {
                const response = await fetch(`/portfolio/api/holdings/${holdingId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (!data.success) {
                    deleteSuccess = false;
                    lastMessage = data.error || 'Failed to delete holding';
                    break;
                }
                lastMessage = data.message;
            }

            if (deleteSuccess) {
                // Fade out and remove row
                row.style.opacity = '0';
                row.style.transform = 'translateX(-20px)';

                setTimeout(() => {
                    row.remove();
                    const message = lotCount > 1
                        ? `All ${lotCount} lots of ${symbol} removed from your portfolio`
                        : lastMessage;
                    this.showMessage(message, 'success');
                    this.refreshPortfolioTotals();

                    // Check if portfolio is empty
                    const remainingRows = document.querySelectorAll('tbody tr[data-holding-id]');
                    if (remainingRows.length === 0) {
                        location.reload(); // Reload to show empty state
                    }
                }, 300);
            } else {
                this.showMessage(lastMessage, 'error');
                row.classList.remove('deleting');
            }
        } catch (error) {
            console.error('Error deleting holding:', error);
            this.showMessage('Network error. Please try again.', 'error');
            row.classList.remove('deleting');
        }
    }

    async refreshPortfolioTotals() {
        // Recalculate totals from visible rows
        let totalInvested = 0;
        let totalCurrentValue = 0;

        document.querySelectorAll('tbody tr[data-holding-id]').forEach(row => {
            const quantity = parseFloat(row.querySelector('.quantity').textContent);
            const buyPrice = parseFloat(row.querySelector('.buy-price').textContent.replace('₹', ''));
            const currentValue = parseFloat(row.querySelector('.current-value').textContent.replace('₹', ''));

            totalInvested += quantity * buyPrice;
            totalCurrentValue += currentValue;
        });

        const totalGainLoss = totalCurrentValue - totalInvested;

        // Update summary cards
        const investedCard = document.querySelector('.stat-card:nth-child(1) .stat-value');
        const currentCard = document.querySelector('.stat-card:nth-child(2) .stat-value');
        const gainLossCard = document.querySelector('.stat-card:nth-child(3) .stat-value');

        if (investedCard) investedCard.textContent = `₹${totalInvested.toFixed(2)}`;
        if (currentCard) currentCard.textContent = `₹${totalCurrentValue.toFixed(2)}`;
        if (gainLossCard) {
            gainLossCard.textContent = `${totalGainLoss >= 0 ? '+' : ''}₹${totalGainLoss.toFixed(2)}`;
            gainLossCard.parentElement.className = 'stat-card ' + (totalGainLoss >= 0 ? 'positive' : 'negative');
        }
    }

    showMessage(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.portfolio-table')) {
        window.portfolioManager = new PortfolioManager();
    }
});
