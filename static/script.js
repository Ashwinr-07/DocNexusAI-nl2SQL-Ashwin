/**
 * Healthcare Data Search - NLP to SQL Interface
 * Frontend JavaScript for handling user interactions and API communication
 */

class HealthcareSearchInterface {
    constructor() {
        this.currentQuery = '';
        this.currentSQL = '';
        this.initializeElements();
        this.bindEventListeners();
    }

    initializeElements() {
        // Input elements
        this.nlpQueryInput = document.getElementById('nlpQuery');
        
        // Buttons
        this.generateSqlBtn = document.getElementById('generateSqlBtn');
        this.retryBtn = document.getElementById('retryBtn');
        this.executeBtn = document.getElementById('executeBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.insightsBtn = document.getElementById('insightsBtn');
        
        // Display elements
        this.sqlCard = document.querySelector('.sql-card');
        this.sqlOutput = document.getElementById('sqlOutput');
        this.resultsCard = document.querySelector('.results-card');
        this.resultsTable = document.getElementById('resultsTable');
        this.resultsTableHead = document.getElementById('resultsTableHead');
        this.resultsTableBody = document.getElementById('resultsTableBody');
        this.resultCount = document.getElementById('resultCount');
        this.insightsCard = document.querySelector('.insights-card');
        this.insightsContent = document.getElementById('insightsContent');
        
        // Utility elements
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.errorAlert = document.getElementById('errorAlert');
        this.errorMessage = document.getElementById('errorMessage');
    }

    bindEventListeners() {
        // Generate SQL button
        this.generateSqlBtn.addEventListener('click', () => this.handleGenerateSQL());
        
        // Retry button
        this.retryBtn.addEventListener('click', () => this.handleRetry());
        
        // Execute button
        this.executeBtn.addEventListener('click', () => this.handleExecuteSQL());
        
        // Copy button
        this.copyBtn.addEventListener('click', () => this.handleCopySQL());
        
        // Insights button
        this.insightsBtn.addEventListener('click', () => this.handleGenerateInsights());
        
        // Enter key support for query input
        this.nlpQueryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                this.handleGenerateSQL();
            }
        });
        
        // Input validation
        this.nlpQueryInput.addEventListener('input', () => this.validateInput());
    }

    validateInput() {
        const query = this.nlpQueryInput.value.trim();
        const isValid = query.length > 0;
        
        this.generateSqlBtn.disabled = !isValid;
        
        if (isValid) {
            this.generateSqlBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Generate SQL';
        } else {
            this.generateSqlBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Enter query to continue';
        }
    }

    async handleGenerateSQL() {
        const query = this.nlpQueryInput.value.trim();
        
        if (!query) {
            this.showError('Please enter a query to generate SQL.');
            return;
        }

        this.currentQuery = query;
        this.showLoading(true);
        this.hideError();
        this.hideResults();

        try {
            const response = await fetch('http://localhost:5001/generate_sql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate SQL');
            }

            this.currentSQL = data.sql;
            this.displaySQL(data.sql);
            this.enableRetry();

        } catch (error) {
            console.error('Error generating SQL:', error);
            this.showError(`Failed to generate SQL: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    async handleExecuteSQL() {
        if (!this.currentSQL) {
            this.showError('No SQL query to execute. Please generate SQL first.');
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            const response = await fetch('http://localhost:5001/execute_sql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sql: this.currentSQL })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to execute SQL');
            }

            this.displayResults(data.results, data.row_count);

        } catch (error) {
            console.error('Error executing SQL:', error);
            this.showError(`Failed to execute SQL: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    handleRetry() {
        // Clear current SQL and regenerate
        this.currentSQL = '';
        this.hideSQL();
        this.hideResults();
        this.hideInsights();
        this.handleGenerateSQL();
    }

    handleCopySQL() {
        if (!this.currentSQL) {
            this.showError('No SQL to copy.');
            return;
        }

        navigator.clipboard.writeText(this.currentSQL).then(() => {
            // Visual feedback for successful copy
            const originalContent = this.copyBtn.innerHTML;
            this.copyBtn.innerHTML = '<i class="fas fa-check"></i>';
            this.copyBtn.classList.add('btn-success');
            this.copyBtn.classList.remove('btn-outline-light');
            
            setTimeout(() => {
                this.copyBtn.innerHTML = originalContent;
                this.copyBtn.classList.remove('btn-success');
                this.copyBtn.classList.add('btn-outline-light');
            }, 2000);
        }).catch(() => {
            this.showError('Failed to copy SQL to clipboard.');
        });
    }

    displaySQL(sql) {
        this.sqlOutput.textContent = sql;
        this.sqlCard.style.display = 'block';
        this.sqlCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    displayResults(results, rowCount) {
        if (!results || !results.columns || !results.data) {
            this.showError('Invalid results format received.');
            return;
        }

        // Clear previous results
        this.resultsTableHead.innerHTML = '';
        this.resultsTableBody.innerHTML = '';

        // Create table headers
        const headerRow = document.createElement('tr');
        results.columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = this.formatColumnName(column);
            th.scope = 'col';
            headerRow.appendChild(th);
        });
        this.resultsTableHead.appendChild(headerRow);

        // Create table body
        results.data.forEach((row, index) => {
            const tr = document.createElement('tr');
            row.forEach((cell, cellIndex) => {
                const td = document.createElement('td');
                td.textContent = this.formatCellValue(cell);
                
                // Add special styling for certain data types
                if (typeof cell === 'number' && cellIndex === results.columns.length - 2) {
                    // Assuming rating column is second to last
                    td.classList.add('text-warning');
                    td.innerHTML = `<i class="fas fa-star me-1"></i>${cell}`;
                }
                
                tr.appendChild(td);
            });
            this.resultsTableBody.appendChild(tr);
        });

        // Update result count
        this.resultCount.textContent = `${rowCount} result${rowCount !== 1 ? 's' : ''}`;

        // Show results
        this.resultsCard.style.display = 'block';
        this.resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    formatColumnName(column) {
        return column.replace(/_/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatCellValue(value) {
        if (value === null || value === undefined) {
            return 'N/A';
        }
        
        if (typeof value === 'number') {
            // Format numbers with appropriate decimal places
            return value % 1 === 0 ? value.toString() : value.toFixed(1);
        }
        
        return value.toString();
    }

    enableRetry() {
        this.retryBtn.disabled = false;
    }

    showLoading(show) {
        this.loadingSpinner.style.display = show ? 'block' : 'none';
        
        // Disable buttons during loading
        this.generateSqlBtn.disabled = show;
        this.retryBtn.disabled = show;
        this.executeBtn.disabled = show;
    }

    hideSQL() {
        this.sqlCard.style.display = 'none';
    }

    hideResults() {
        this.resultsCard.style.display = 'none';
    }

    async handleGenerateInsights() {
        if (!this.currentSQL) {
            this.showError('No SQL query available. Please generate and execute SQL first.');
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            const response = await fetch('http://localhost:5001/generate_insights', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    sql: this.currentSQL,
                    query: this.currentQuery 
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate insights');
            }

            this.displayInsights(data.insights);

        } catch (error) {
            console.error('Error generating insights:', error);
            this.showError(`Failed to generate insights: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    displayInsights(insights) {
        this.insightsContent.innerHTML = '';

        insights.forEach(insight => {
            const insightDiv = document.createElement('div');
            insightDiv.className = 'insight-item';
            
            insightDiv.innerHTML = `
                <div class="insight-title">
                    <i class="${insight.icon} me-2"></i>
                    ${insight.title}
                </div>
                <div class="insight-value">${insight.value}</div>
                <div class="insight-description">${insight.description}</div>
            `;
            
            this.insightsContent.appendChild(insightDiv);
        });

        this.insightsCard.style.display = 'block';
        this.insightsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    hideInsights() {
        this.insightsCard.style.display = 'none';
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorAlert.style.display = 'block';
        this.errorAlert.classList.add('show');
        
        // Auto-hide error after 10 seconds
        setTimeout(() => {
            this.hideError();
        }, 10000);
        
        // Scroll to error
        this.errorAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    hideError() {
        this.errorAlert.style.display = 'none';
        this.errorAlert.classList.remove('show');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Healthcare Data Search Interface initialized');
    new HealthcareSearchInterface();
});

// Add some helpful console messages for developers
console.log('%cHealthcare Data Search Interface', 'color: #2ea043; font-size: 16px; font-weight: bold;');
console.log('%cIntegration Points:', 'color: #1f6feb; font-weight: bold;');
console.log('• POST /generate_sql - Convert NLP to SQL');
console.log('• POST /execute_sql - Execute generated SQL');
console.log('%cReady for backend integration!', 'color: #2ea043;');
