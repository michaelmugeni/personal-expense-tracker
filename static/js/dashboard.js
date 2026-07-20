document.addEventListener('DOMContentLoaded', function () {

    // ==========================
    // ANIMATED NUMBER COUNTERS
    // ==========================
    var counters = document.querySelectorAll('.counter-value');

    counters.forEach(function (counter) {

        var target = parseFloat(counter.getAttribute('data-target')) || 0;
        var duration = 900;
        var startTime = null;

        function step(timestamp) {

            if (!startTime) startTime = timestamp;

            var progress = Math.min((timestamp - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = target * eased;

            counter.textContent = current.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            });

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                counter.textContent = target.toLocaleString(undefined, {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2
                });
            }
        }

        requestAnimationFrame(step);
    });

    // ==========================
    // CHART COLOR PALETTE
    // ==========================
    var palette = [
        '#10B981', '#0DCAF0', '#8B5CF6', '#FB923C',
        '#EC4899', '#0D6EFD', '#F59E0B', '#14B8A6'
    ];

    // ==========================
    // CATEGORY PIE CHART
    // ==========================
    var pieCanvas = document.getElementById('categoryPieChart');

    if (pieCanvas && window.categoryLabels && window.categoryLabels.length) {

        new Chart(pieCanvas, {
            type: 'pie',
            data: {
                labels: window.categoryLabels,
                datasets: [{
                    data: window.categoryValues,
                    backgroundColor: palette,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 16, usePointStyle: true }
                    }
                },
                animation: {
                    animateScale: true,
                    duration: 900
                }
            }
        });

    } else if (pieCanvas) {

        var ctx = pieCanvas.getContext('2d');
        ctx.font = '14px Poppins, sans-serif';
        ctx.fillStyle = '#94A3B8';
        ctx.textAlign = 'center';
        ctx.fillText('No category data yet', pieCanvas.width / 2, 40);
    }

    // ==========================
    // MONTHLY TREND LINE CHART
    // ==========================
    var lineCanvas = document.getElementById('monthlyLineChart');

    if (lineCanvas && window.monthlyLabels && window.monthlyLabels.length) {

        var ctxLine = lineCanvas.getContext('2d');
        var gradient = ctxLine.createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, 'rgba(16,185,129,0.35)');
        gradient.addColorStop(1, 'rgba(16,185,129,0)');

        new Chart(lineCanvas, {
            type: 'line',
            data: {
                labels: window.monthlyLabels,
                datasets: [{
                    label: 'Spending (KES)',
                    data: window.monthlyValues,
                    borderColor: '#10B981',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#10B981',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                },
                animation: {
                    duration: 900
                }
            }
        });

    } else if (lineCanvas) {

        var ctx2 = lineCanvas.getContext('2d');
        ctx2.font = '14px Poppins, sans-serif';
        ctx2.fillStyle = '#94A3B8';
        ctx2.textAlign = 'center';
        ctx2.fillText('No trend data yet', lineCanvas.width / 2, 40);
    }

    // ==========================
    // VIEW EXPENSE MODAL
    // ==========================
    var viewModal = document.getElementById('viewExpenseModal');

    if (viewModal) {

        viewModal.addEventListener('show.bs.modal', function (event) {

            var trigger = event.relatedTarget;
            if (!trigger) return;

            document.getElementById('modalDate').textContent = trigger.getAttribute('data-date') || '';
            document.getElementById('modalCategory').textContent = trigger.getAttribute('data-category') || '';
            document.getElementById('modalDescription').textContent = trigger.getAttribute('data-description') || '';
            document.getElementById('modalAmount').textContent = trigger.getAttribute('data-amount') || '';
        });
    }

});
