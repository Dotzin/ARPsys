function changeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const selectedTheme = themeToggle.value;
    localStorage.setItem('theme', selectedTheme);
    document.body.className = selectedTheme;
}

document.addEventListener('DOMContentLoaded', function() {
    // Apply theme
    const theme = localStorage.getItem('theme') || 'light';
    document.body.className = theme;
    document.getElementById('theme-toggle').value = theme;

    // Modal functionality
    const modal = document.getElementById('sku-modal');
    const btn = document.getElementById('add-sku-btn');
    const span = document.getElementsByClassName('close')[0];

    btn.onclick = function() {
        modal.style.display = 'block';
    }

    span.onclick = function() {
        modal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }

    // Send XLSX
    document.getElementById('send-xlsx-btn').onclick = async function() {
        const fileInput = document.getElementById('xlsx-file');
        const file = fileInput.files[0];
        if (!file) {
            alert('Selecione um arquivo XLSX.');
            return;
        }
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/sku_nicho/inserir_xlsx', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.mensagem);
                modal.style.display = 'none';
            } else {
                alert('Erro: ' + result.erro);
            }
        } catch (error) {
            alert('Erro ao enviar arquivo: ' + error);
        }
    }

    // Add single SKU
    document.getElementById('add-single-btn').onclick = async function() {
        const sku = document.getElementById('single-sku').value;
        const nicho = document.getElementById('single-nicho').value;
        if (!sku || !nicho) {
            alert('Preencha SKU e Nicho.');
            return;
        }
        try {
            const response = await fetch('/sku_nicho/inserir', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ sku, nicho })
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.mensagem);
                modal.style.display = 'none';
            } else {
                alert('Erro: ' + result.erro);
            }
        } catch (error) {
            alert('Erro ao adicionar SKU: ' + error);
        }
    }
});
