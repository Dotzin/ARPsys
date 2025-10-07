document.addEventListener('DOMContentLoaded', function() {
    // Apply theme
    const theme = localStorage.getItem('theme') || 'light';
    document.body.className = theme;

    const form = document.getElementById('report-form');
    const resultsSection = document.getElementById('results-section');
    const forecastTableBody = document.querySelector('#forecast-table tbody');

    // Initialize DataTables after data is loaded
    function initDataTables() {
        if ($.fn.DataTable.isDataTable('#forecast-table')) {
            $('#forecast-table').DataTable().destroy();
        }
        if ($.fn.DataTable.isDataTable('#orders-table')) {
            $('#orders-table').DataTable().destroy();
        }
        if ($.fn.DataTable.isDataTable('#rankings-table')) {
            $('#rankings-table').DataTable().destroy();
        }
        if ($.fn.DataTable.isDataTable('#top-nichos-table')) {
            $('#top-nichos-table').DataTable().destroy();
        }
        if ($.fn.DataTable.isDataTable('#top-ads-table')) {
            $('#top-ads-table').DataTable().destroy();
        }
        $('#forecast-table').DataTable();
        $('#orders-table').DataTable();
        $('#rankings-table').DataTable();
        $('#top-nichos-table').DataTable();
        $('#top-ads-table').DataTable();
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
    const refreshBtn = document.getElementById('refresh-btn');

    let reportData = null;
    let currentDataInicio = null;
    let currentDataFim = null;

    // Chart instances stored on window

    async function loadAndRenderReport(dataInicio, dataFim) {
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
        renderTopNichos(reportData.rankings.top_por_nicho);
        renderTopAds(reportData.rankings.top_ads);
        renderOrdersTable(reportData.relatorios.pedidos_lista);
        renderSkuDetails(reportData.rankings.top_skus_per_nicho);

        resultsSection.style.display = 'block';
        refreshBtn.style.display = 'inline-block';
        exportBtn.style.display = 'inline-block';
        document.getElementById('sku-details-container').style.display = 'block';

        currentDataInicio = dataInicio;
        currentDataFim = dataFim;

        // Initialize DataTables after rendering
        setTimeout(initDataTables, 100);
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const dataInicio = document.getElementById('data-inicio').value;
        const dataFim = document.getElementById('data-fim').value;

        if (!dataInicio || !dataFim) {
            alert('Por favor, selecione ambas as datas.');
            return;
        }

        try {
            await loadAndRenderReport(dataInicio, dataFim);
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao gerar relatório: ' + error.message);
        }
    });

    refreshBtn.addEventListener('click', async function() {
        if (!currentDataInicio || !currentDataFim) {
            alert('Gere um relatório primeiro.');
            return;
        }

        try {
            await loadAndRenderReport(currentDataInicio, currentDataFim);
        } catch (error) {
            console.error('Erro ao atualizar relatório:', error);
            alert('Erro ao atualizar relatório: ' + error.message);
        }
    });

    exportBtn.addEventListener('click', function() {
        alert('Função não implementada');
    });

    function renderForecastTable(forecast) {
        forecastTableBody.innerHTML = '';
        forecast.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(item.payment_date).toLocaleDateString()}</td>
                <td>R$ ${item.previsao_lucro_diario.toFixed(2)}</td>
                <td>${item.quantidade_total_diaria}</td>
                <td>R$ ${item.valor_total_diario.toFixed(2)}</td>
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
        // Destroy existing chart if it exists
        if (window.nichoChart) {
            window.nichoChart.destroy();
        }
        const labels = porNicho.map(item => item.nicho || 'Sem nicho');
        const data = porNicho.map(item => item.lucro_liquido);
        const isDark = document.body.classList.contains('dark');
        window.nichoChart = new Chart(ctx, {
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
                        beginAtZero: true,
                        ticks: {
                            color: isDark ? '#ffffff' : '#333'
                        },
                        grid: {
                            color: isDark ? '#444' : '#ddd'
                        }
                    },
                    x: {
                        ticks: {
                            color: isDark ? '#ffffff' : '#333'
                        },
                        grid: {
                            color: isDark ? '#444' : '#ddd'
                        }
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
        // Destroy existing chart if it exists
        if (window.hourChart) {
            window.hourChart.destroy();
        }
        const labels = porHora.map(item => `${item.hour}h`);
        const data = porHora.map(item => item.lucro_liquido);
        window.hourChart = new Chart(ctx, {
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
        // Destroy existing chart if it exists
        if (window.weekdayChart) {
            window.weekdayChart.destroy();
        }
        const weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
        const labels = porDiaSemana.map(item => weekdays[item.weekday] || item.weekday);
        const data = porDiaSemana.map(item => item.lucro_liquido);
        window.weekdayChart = new Chart(ctx, {
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
        // Destroy existing chart if it exists
        if (window.dailySalesChart) {
            window.dailySalesChart.destroy();
        }
        const labels = diario.map(item => item.data);
        const data = diario.map(item => item.resumo.lucro_liquido);
        window.dailySalesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Lucro Líquido',
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
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${item.title}</td>
                <td>${item.quantity}</td>
                <td>R$ ${item.total_value.toFixed(2)}</td>
                <td>R$ ${item.profit.toFixed(2)}</td>
                <td>${item.nicho}</td>
            `;
            tbody.appendChild(row);
        });
    }

    function renderTopNichos(topPorNicho) {
        const tbody = document.querySelector('#top-nichos-table tbody');
        tbody.innerHTML = '';
        topPorNicho.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.nicho}</td>
                <td>${item.sku}</td>
                <td>R$ ${item.profit.toFixed(2)}</td>
                <td>R$ ${item.gross_profit.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    function renderTopAds(topAds) {
        const tbody = document.querySelector('#top-ads-table tbody');
        tbody.innerHTML = '';
        topAds.slice(0, 30).forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.ad}</td>
                <td>R$ ${item.profit.toFixed(2)}</td>
                <td>R$ ${item.gross_profit.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    function renderSkuDetails(topSkusPerNicho) {
        const tabsContainer = document.getElementById('sku-tabs');
        const contentContainer = document.getElementById('sku-tab-content');
        tabsContainer.innerHTML = '';
        contentContainer.innerHTML = '';

        const nichos = Object.keys(topSkusPerNicho);
        nichos.forEach((nicho, index) => {
            const skus = topSkusPerNicho[nicho] || [];

            // Create tab button
            const tabButton = document.createElement('button');
            tabButton.className = 'sku-tab-button';
            tabButton.textContent = nicho;
            tabButton.onclick = () => showSkuTab(nicho);
            if (index === 0) tabButton.classList.add('active');
            tabsContainer.appendChild(tabButton);

            // Create tab content
            const tabContent = document.createElement('div');
            tabContent.id = `sku-${nicho}`;
            tabContent.className = 'sku-tab-content';
            if (index === 0) tabContent.classList.add('active');

            const table = document.createElement('table');
            table.className = 'display';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Lucro Líquido</th>
                        <th>Lucro Bruto</th>
                    </tr>
                </thead>
                <tbody>
                    ${skus.map(sku => `
                        <tr>
                            <td>${sku.sku}</td>
                            <td>R$ ${sku.profit.toFixed(2)}</td>
                            <td>R$ ${sku.gross_profit.toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
            tabContent.appendChild(table);
            contentContainer.appendChild(tabContent);

            // Initialize DataTable
            $(table).DataTable();
        });
    }

    window.showSkuTab = function(nicho) {
        document.querySelectorAll('.sku-tab-content').forEach(content => content.classList.remove('active'));
        document.querySelectorAll('.sku-tab-button').forEach(button => button.classList.remove('active'));
        document.getElementById(`sku-${nicho}`).classList.add('active');
        event.target.classList.add('active');
    }
});
