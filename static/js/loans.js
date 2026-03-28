// Loan Management Logic

document.addEventListener('DOMContentLoaded', () => {
     // Check if on loans page
     const loanInterface = document.getElementById('loanInterface');
     if (!loanInterface) return;

     loadLoanData();
     setupCalculators();
});

async function loadLoanData() {
     // 1. Check Verification Status
     const user = JSON.parse(localStorage.getItem('user') || '{}');
     const verificationStatus = localStorage.getItem('verificationStatus') || user.verificationStatus || 'unverified';

     // Update badge
     const badge = document.getElementById('accountBadge');
     if (badge) {
          if (verificationStatus === 'verified') {
               badge.textContent = 'Verified';
               badge.style.color = '#00A86B';
               badge.style.background = 'rgba(0, 168, 107, 0.1)';
               document.getElementById('lockOverlay').style.display = 'none';
          } else {
               badge.textContent = 'Unverified';
               badge.style.color = '#94A3B8';
               document.getElementById('lockOverlay').style.display = 'flex';
               return; // Stop loading if locked
          }
     }

     // 2. Fetch Active Loans & Limit
     try {
          // Fetch dashboard stats (which includes active loans total)
          const response = await fetchWithAuth(`${DASHBOARD_API}/api/stats/dashboard`);
          if (response.ok) {
               const data = await response.json();
               if (data.success && data.stats) {
                    const activeEl = document.getElementById('activeLoans');
                    if (activeEl) activeEl.textContent = formatCurrency(data.stats.activeLoans || 0);
               }
          }

          // Set Limit (Mock logic or from backend user profile)
          const limit = user.loanLimit || 50000;
          document.getElementById('creditLimit').textContent = formatCurrency(limit);
          const slider = document.getElementById('loanSlider');
          if (slider) slider.max = limit;

     } catch (error) {
          console.error("Error loading loan data:", error);
     }
}

function setupCalculators() {
     const amountInput = document.getElementById('loanAmount');
     const slider = document.getElementById('loanSlider');
     const durationInput = document.getElementById('loanDuration');

     if (amountInput && slider) {
          amountInput.addEventListener('input', updateCalculator);
          slider.addEventListener('input', (e) => {
               amountInput.value = e.target.value;
               updateCalculator();
          });
     }
     if (durationInput) {
          durationInput.addEventListener('change', updateCalculator);
     }
     updateCalculator(); // Init
}

function updateCalculator() {
     const amountInput = document.getElementById('loanAmount');
     if (!amountInput) return;

     const amount = parseFloat(amountInput.value) || 0;
     const duration = parseInt(document.getElementById('loanDuration').value) || 12;
     const rate = 0.045; // 4.5% Fixed APR for now

     const totalInterest = amount * rate * (duration / 12);
     const totalRepay = amount + totalInterest;
     const monthly = totalRepay / duration;

     document.getElementById('sumPrincipal').textContent = formatCurrency(amount);
     document.getElementById('sumMonthly').textContent = formatCurrency(monthly);
     document.getElementById('sumTotal').textContent = formatCurrency(totalRepay);
}

// Global function for the Apply button
window.submitLoanRequest = async function () {
     const amount = document.getElementById('loanAmount').value;
     const duration = document.getElementById('loanDuration').value;
     const reason = "General Investment"; // Could add specific field

     const btn = document.querySelector('button[onclick="submitLoanRequest()"]');
     const originalText = btn.innerText;
     btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Processing...`;
     btn.disabled = true;

     try {
          const response = await fetchWithAuth(`${DASHBOARD_API}/api/loans/apply`, {
               method: 'POST',
               body: JSON.stringify({
                    amount: parseFloat(amount),
                    duration: parseInt(duration),
                    reason
               })
          });

          const data = await response.json();

          if (response.ok && data.success) {
               showToast(`Loan application for $${amount} submitted!`, 'success');
               loadLoanData(); // Refresh stats
          } else {
               showToast(data.message || 'Application failed', 'error');
          }
     } catch (error) {
          showToast('Network error during application', 'error');
     } finally {
          btn.innerHTML = originalText;
          btn.disabled = false;
     }
};

function formatCurrency(val) {
     return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}
