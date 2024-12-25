function draw_cate_chart(label, chart_type, labels, datasets, id) {
    const ctx = document.getElementById(id)
    new Chart(ctx, {
        type: chart_type,
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: datasets,
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function years_dynamically(select_year, startYear= 2020) {
    const yearSelect = document.getElementById('year-select');
    const currentYear = new Date().getFullYear();

    for (let year = startYear; year <= currentYear; year++) {
        const option = document.createElement('option');
        option.value = year.toString();
        option.textContent = year.toString();
        yearSelect.appendChild(option);
    }
    yearSelect.value=select_year.toString()
}