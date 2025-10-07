document.addEventListener('DOMContentLoaded', function() {
    // Apply theme
    const theme = localStorage.getItem('theme') || 'light';
    document.body.className = theme;

    // Assume the app runs on localhost:8000, adjust if needed
    const ws = new WebSocket('ws://localhost:8000/ws/relatorio_diario');

    // Store previous rankings for change detection, persist in localStorage
    let previousTopNichos = JSON.parse(localStorage.getItem('previousTopNichos')) || [];
    let previousTopSkus = JSON.parse(localStorage.getItem('previousTopSkus')) || [];

    ws.onopen = function(event) {
        document.getElementById('kpis-display').innerHTML = '<p>Conectado ao servidor. Aguardando relatório...</p>';
    };

    ws.onmessage = function(event) {
        console.log('WS message received:', event.data);
        try {
            const data = JSON.parse(event.data);
            if (data.tipo === 'relatorio_diario_inicial' || data.tipo === 'relatorio_diario') {
                displayReport(data.dados);
            }
        } catch (error) {
            console.error('Erro ao processar mensagem:', error);
            document.getElementById('kpis-display').innerHTML = '<p>Erro ao processar dados do relatório.</p>';
        }
    };

    ws.onclose = function(event) {
        document.getElementById('kpis-display').innerHTML = '<p>Conexão fechada. Recarregue a página para reconectar.</p>';
    };

    ws.onerror = function(error) {
        console.error('Erro no WebSocket:', error);
        document.getElementById('kpis-display').innerHTML = '<p>Erro na conexão WebSocket.</p>';
    };

    function renderKPIs(kpis) {
        const div = document.getElementById('kpis-display');
        div.innerHTML = `
            <div class="kpi-card">
                <h3>Lucro Líquido: R$ ${kpis.lucro_liquido.toFixed(2)}</h3>
                <p>Faturamento: R$ ${kpis.faturamento.toFixed(2)}</p>
                <p>Total Pedidos: ${kpis.total_pedidos}</p>
                <p>Total Unidades: ${kpis.total_unidades}</p>
            </div>
        `;
    }

    function renderNichoChart(nichos) {
        const ctx = document.getElementById('nicho-chart').getContext('2d');
        // Destroy existing chart if it exists
        if (window.nichoChart) {
            window.nichoChart.destroy();
        }
        const labels = nichos.map(n => n.nicho || 'Sem nicho');
        const data = nichos.map(n => n.lucro_liquido);
        const isDark = document.body.classList.contains('dark');
        window.nichoChart = new Chart(ctx, {
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

    function renderUltimaVenda(venda) {
        const div = document.getElementById('ultima-venda-display');
        if (venda) {
            div.innerHTML = `
                <div class="card">
                    <p><strong>Data:</strong> ${new Date(venda.payment_date).toLocaleString()}</p>
                    <p><strong>Order ID:</strong> ${venda.order_id}</p>
                    <p><strong>SKU:</strong> ${venda.sku}</p>
                    <p><strong>Título:</strong> ${venda.title}</p>
                    <p><strong>Quantidade:</strong> ${venda.quantity}</p>
                    <p><strong>Valor Total:</strong> R$ ${venda.total_value.toFixed(2)}</p>
                    <p><strong>Lucro Líquido:</strong> R$ ${venda.profit.toFixed(2)}</p>
                    <p><strong>Nicho:</strong> ${venda.nicho}</p>
                </div>
            `;
        } else {
            div.innerHTML = '<p>Nenhuma venda encontrada.</p>';
        }
    }

    function renderMelhorProduto(produto) {
        const div = document.getElementById('melhor-produto-display');
        if (produto) {
            div.innerHTML = `
                <div class="card">
                    <p><strong>SKU:</strong> ${produto.sku}</p>
                    <p><strong>Lucro Líquido Total:</strong> R$ ${produto.profit.toFixed(2)}</p>
                    <p><strong>Faturamento Total:</strong> R$ ${produto.total_value.toFixed(2)}</p>
                    <p><strong>Quantidade Total:</strong> ${produto.quantity}</p>
                </div>
            `;
        } else {
            div.innerHTML = '<p>Nenhum produto encontrado.</p>';
        }
    }

    function renderMelhorAnuncio(anuncio) {
        const div = document.getElementById('melhor-anuncio-display');
        if (anuncio) {
            div.innerHTML = `
                <div class="card">
                    <p><strong>Anúncio:</strong> ${anuncio.ad}</p>
                    <p><strong>Lucro Líquido Total:</strong> R$ ${anuncio.profit.toFixed(2)}</p>
                    <p><strong>Faturamento Total:</strong> R$ ${anuncio.total_value.toFixed(2)}</p>
                    <p><strong>Quantidade Total:</strong> ${anuncio.quantity}</p>
                </div>
            `;
        } else {
            div.innerHTML = '<p>Nenhum anúncio encontrado.</p>';
        }
    }

    function renderUltimas15Vendas(vendas) {
        const tbody = document.querySelector('#ultimas-15-table tbody');
        tbody.innerHTML = '';
        vendas.forEach(v => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(v.payment_date).toLocaleString()}</td>
                <td>${v.order_id}</td>
                <td>${v.sku}</td>
                <td>${v.title}</td>
                <td>${v.quantity}</td>
                <td>R$ ${v.total_value.toFixed(2)}</td>
                <td>R$ ${v.profit.toFixed(2)}</td>
                <td>${v.nicho}</td>
            `;
            tbody.appendChild(row);
        });
        $('#ultimas-15-table').DataTable();
    }

    function renderVendasNegativas(vendas) {
        const tbody = document.querySelector('#vendas-negativas-table tbody');
        tbody.innerHTML = '';
        vendas.forEach(v => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(v.payment_date).toLocaleString()}</td>
                <td>${v.order_id}</td>
                <td>${v.sku}</td>
                <td>${v.title}</td>
                <td>${v.quantity}</td>
                <td>R$ ${v.total_value.toFixed(2)}</td>
                <td>R$ ${v.profit.toFixed(2)}</td>
                <td>${v.nicho}</td>
            `;
            tbody.appendChild(row);
        });
        $('#vendas-negativas-table').DataTable();
    }

    function getChangeArrow(currentList, previousList, item, key) {
        const currentIndex = currentList.findIndex(i => i[key] === item[key]);
        const previousIndex = previousList.findIndex(i => i[key] === item[key]);
        if (previousIndex === -1) return '🆕'; // new
        if (currentIndex < previousIndex) return '▲';
        if (currentIndex > previousIndex) return '▼';
        return '▬';
    }

    function renderRankingNichos(nichos) {
        const tbody = document.querySelector('#ranking-nichos-table tbody');
        tbody.innerHTML = '';
        nichos.forEach((n, index) => {
            const arrow = getChangeArrow(nichos, previousTopNichos, n, 'nicho');
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${n.nicho || 'Sem nicho'}</td>
                <td>R$ ${n.lucro_liquido.toFixed(2)}</td>
                <td>${arrow}</td>
            `;
            tbody.appendChild(row);
        });
        previousTopNichos = [...nichos];
        localStorage.setItem('previousTopNichos', JSON.stringify(previousTopNichos));
    }

    function renderRankingSkus(skus) {
        const tbody = document.querySelector('#ranking-skus-table tbody');
        tbody.innerHTML = '';
        skus.forEach((s, index) => {
            const arrow = getChangeArrow(skus, previousTopSkus, s, 'sku');
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${s.sku}</td>
                <td>R$ ${s.lucro_liquido.toFixed(2)}</td>
                <td>${arrow}</td>
            `;
            tbody.appendChild(row);
        });
        previousTopSkus = [...skus];
        localStorage.setItem('previousTopSkus', JSON.stringify(previousTopSkus));
    }

    function renderEmpty() {
        document.getElementById('kpis-display').innerHTML = '<p>Sem dados para hoje.</p>';
        document.getElementById('ultima-venda-display').innerHTML = '<p>Sem vendas hoje.</p>';
        document.getElementById('melhor-produto-display').innerHTML = '<p>Sem produtos hoje.</p>';
        document.getElementById('melhor-anuncio-display').innerHTML = '<p>Sem anúncios hoje.</p>';
        const tbody15 = document.querySelector('#ultimas-15-table tbody');
        tbody15.innerHTML = '<tr><td colspan="8">Sem vendas hoje.</td></tr>';
        const tbodyNeg = document.querySelector('#vendas-negativas-table tbody');
        tbodyNeg.innerHTML = '<tr><td colspan="8">Sem vendas negativas hoje.</td></tr>';
        const tbodyNichos = document.querySelector('#ranking-nichos-table tbody');
        tbodyNichos.innerHTML = '<tr><td colspan="4">Sem dados.</td></tr>';
        const tbodySkus = document.querySelector('#ranking-skus-table tbody');
        tbodySkus.innerHTML = '<tr><td colspan="4">Sem dados.</td></tr>';
    }

    function displayReport(report) {
        console.log('Display report called', report);
        if (report.status === 'sucesso') {
            renderKPIs(report.kpis_diarios);
            renderNichoChart(report.analise_por_nicho_dia);
            renderRankingNichos(report.rankings_diarios.top_nichos);
            renderRankingSkus(report.rankings_diarios.top_skus);
            renderUltimaVenda(report.ultima_venda);
            renderMelhorProduto(report.melhor_produto);
            renderMelhorAnuncio(report.melhor_anuncio);
            renderUltimas15Vendas(report.ultimas_15_vendas);
            renderVendasNegativas(report.vendas_negativas);
        } else if (report.status === 'sem_dados') {
            renderEmpty();
        } else {
            document.getElementById('kpis-display').innerHTML = '<p>Erro no relatório: ' + (report.erro || 'Desconhecido') + '</p>';
        }
    }
});
