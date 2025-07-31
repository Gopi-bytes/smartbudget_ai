<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const ctx = document.getElementById('breakdownChart').getContext('2d');
const breakdownChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: {{ chart_labels | tojson }},
        datasets: [{
            label: 'Expenses (€)',
            data: {{ chart_data | tojson }},
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            barThickness: 25  // 👈 makes bars thinner
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Monthly Expense Breakdown'
            },
            legend: { display: false }
        },
        maintainAspectRatio: false
    }
});
</script>
