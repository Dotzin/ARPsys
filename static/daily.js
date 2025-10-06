document.addEventListener('DOMContentLoaded', function() {
    const reportDisplay = document.getElementById('report-display');

    // Assume the app runs on localhost:8000, adjust if needed
    const ws = new WebSocket('ws://localhost:8000/ws/relatorio_diario');

    ws.onopen = function(event) {
        reportDisplay.innerHTML = '<p>Conectado ao servidor. Aguardando relatório...</p>';
    };

    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.tipo === 'relatorio_diario_inicial' || data.tipo === 'relatorio_diario') {
                displayReport(data.dados);
            }
        } catch (error) {
            console.error('Erro ao processar mensagem:', error);
            reportDisplay.innerHTML = '<p>Erro ao processar dados do relatório.</p>';
        }
    };

    ws.onclose = function(event) {
        reportDisplay.innerHTML = '<p>Conexão fechada. Recarregue a página para reconectar.</p>';
    };

    ws.onerror = function(error) {
        console.error('Erro no WebSocket:', error);
        reportDisplay.innerHTML = '<p>Erro na conexão WebSocket.</p>';
    };

    function displayReport(report) {
        if (report.status === 'sucesso') {
            let html = '<h3>Relatório Diário</h3>';
            html += '<pre>' + JSON.stringify(report, null, 2) + '</pre>';
            reportDisplay.innerHTML = html;
        } else {
            reportDisplay.innerHTML = '<p>Erro no relatório: ' + (report.erro || 'Desconhecido') + '</p>';
        }
    }
});
