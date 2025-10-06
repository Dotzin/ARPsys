document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('report-form');
    const resultsSection = document.getElementById('results-section');
    const forecastTableBody = document.querySelector('#forecast-table tbody');

    // Initialize DataTables after data is loaded
    function initDataTables() {
        $('#forecast-table').DataTable();
        $('#orders-table').DataTable();
        $('#rankings-table').DataTable();
    }

    // Tab switching
    window.showTab = function(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.querySelectorAll('.tab-button').forEach(button => button.classList.remove('active'));

        // Show selected tab
        document.getElementById(tabName + '-tab').classList.add('active');
        event.target.classList.add('active');
    }
    const exportBtn = document.getElementById('export-btn');

    let reportData = null;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const dataInicio = document.getElementById('data-inicio').value;
        const dataFim = document.getElementById('data-fim').value;

        if (!dataInicio || !dataFim) {
            alert('Por favor, selecione ambas as datas.');
            return;
        }

        try {
            const response = await fetch(`/relatorio_flex?data_inicio=${dataInicio}&data_fim=${dataFim}`);
            if (!response.ok) {
                throw new Error('Erro ao buscar relatório');
            }
            reportData = await response.json();

            renderKPIs(reportData.kpis_gerais);
            renderForecastTable(reportData.forecast.dados);
            renderNichoChart(reportData.relatorios.por_nicho);
            renderHourChart(reportData.relatorios.por_hora);
            renderWeekdayChart(reportData.relatorios.por_dia_semana);
            renderDailySalesChart(reportData.relatorios.diario);
            renderRankings(reportData.rankings.top_skus);
            renderOrdersTable(reportData.relatorios.pedidos_lista);

            resultsSection.style.display = 'block';
            document.getElementById('export-btn').style.display = 'inline-block';

            // Initialize DataTables after rendering
            setTimeout(initDataTables, 100);
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao gerar relatório: ' + error.message);
        }
    });

    exportBtn.addEventListener('click', function() {
        if (!reportData) {
            alert('Gere um relatório primeiro.');
            return;
        }

        const wb = XLSX.utils.book_new();

        // Sheet 1: KPIs
        const kpisWS = XLSX.utils.json_to_sheet([reportData.kpis_gerais]);
        XLSX.utils.book_append_sheet(wb, kpisWS, 'KPIs');

        // Sheet 2: Forecast
        const forecastWS = XLSX.utils.json_to_sheet(reportData.forecast.dados);
        XLSX.utils.book_append_sheet(wb, forecastWS, 'Previsao');

        // Sheet 3: Nicho
        const nichoWS = XLSX.utils.json_to_sheet(reportData.relatorios.por_nicho);
        XLSX.utils.book_append_sheet(wb, nichoWS, 'Nicho');

        // Sheet 4: Por Hora
        const horaWS = XLSX.utils.json_to_sheet(reportData.relatorios.por_hora);
        XLSX.utils.book_append_sheet(wb, horaWS, 'Por_Hora');

        // Sheet 5: Por Dia Semana
        const diaSemanaWS = XLSX.utils.json_to_sheet(reportData.relatorios.por_dia_semana);
        XLSX.utils.book_append_sheet(wb, diaSemanaWS, 'Por_Dia_Semana');

        // Sheet 6: Diário
        const diarioWS = XLSX.utils.json_to_sheet(reportData.relatorios.diario);
        XLSX.utils.book_append_sheet(wb, diarioWS, 'Diario');

        // Sheet 7: Rankings
        const rankingsWS = XLSX.utils.json_to_sheet(reportData.rankings.top_skus);
        XLSX.utils.book_append_sheet(wb, rankingsWS, 'Top_SKUs');

        // Sheet 8: Pedidos
        const pedidosWS = XLSX.utils.json_to_sheet(reportData.relatorios.pedidos_lista);
        XLSX.utils.book_append_sheet(wb, pedidosWS, 'Pedidos');

        XLSX.writeFile(wb, 'relatorio_flex.xlsx');
    });

    function renderForecastTable(forecast) {
        forecastTableBody.innerHTML = '';
        forecast.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.payment_date}</td>
                <td>${item.sku}</td>
                <td>${item.quantity}</td>
                <td>${item.total_value}</td>
                <td>${item.forecast_lucro_liquido_next}</td>
            `;
            forecastTableBody.appendChild(row);
        });
    }

    function renderKPIs(kpis) {
        const container = document.getElementById('kpis-display');
        container.innerHTML = `
            <p><strong>Faturamento Total:</strong> R$ ${kpis.faturamento_total.toFixed(2)}</p>
            <p><strong>Lucro Líquido Total:</strong> R$ ${kpis.lucro_liquido_total.toFixed(2)}</p>
            <p><strong>Total Pedidos:</strong> ${kpis.total_pedidos}</p>
            <p><strong>Total Unidades:</strong> ${kpis.total_unidades}</p>
            <p><strong>Ticket Médio (Pedido):</strong> R$ ${kpis.ticket_medio.pedido.toFixed(2)}</p>
            <p><strong>Ticket Médio (Unidade):</strong> R$ ${kpis.ticket_medio.unidade.toFixed(2)}</p>
        `;
    }

    function renderNichoChart(porNicho) {
        const ctx = document.getElementById('nicho-chart').getContext('2d');
        const labels = porNicho.map(item => item.nicho || 'Sem nicho');
        const data = porNicho.map(item => item.lucro_liquido);
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Lucro Líquido',
                    data: data,
                    backgroundColor: 'rgba(0, 123, 255, 0.5)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function renderHourChart(porHora) {
        const ctx = document.getElementById('hour-chart').getContext('2d');
        const labels = porHora.map(item => `${item.hour}h`);
        const data = porHora.map(item => item.lucro_liquido);
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Lucro Líquido',
                    data: data,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function renderWeekdayChart(porDiaSemana) {
        const ctx = document.getElementById('weekday-chart').getContext('2d');
        const weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
        const labels = porDiaSemana.map(item => weekdays[item.weekday] || item.weekday);
        const data = porDiaSemana.map(item => item.lucro_liquido);
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Lucro Líquido',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function renderDailySalesChart(diario) {
        const ctx = document.getElementById('daily-sales-chart').getContext('2d');
        const labels = diario.map(item => item.data);
        const data = diario.map(item => item.resumo.faturamento);
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Faturamento',
                    data: data,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function renderRankings(topSkus) {
        const tbody = document.querySelector('#rankings-table tbody');
        tbody.innerHTML = '';
        topSkus.slice(0, 10).forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.sku}</td>
                <td>R$ ${item.profit.toFixed(2)}</td>
                <td>R$ ${item.gross_profit.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    function renderOrdersTable(pedidos) {
        const tbody = document.querySelector('#orders-table tbody');
        tbody.innerHTML = '';
        pedidos.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(item.payment_date).toLocaleDateString()}</td>
                <td>${item.order_id || ''}</td>
                <td>${item.cart_id || ''}</td>
                <td>${item.sku}</td>
                <td>${item.title}</td>
                <td>${item.quantity}</td>
                <td>R$ ${item.total_value.toFixed(2)}</td>
                <td>R$ ${item.profit.toFixed(2)}</td>
                <td>${item.nicho}</td>
            `;
            tbody.appendChild(row);
        });
    }
});
