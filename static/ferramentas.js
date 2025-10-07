document.addEventListener('DOMContentLoaded', function() {
    // Apply theme
    const theme = localStorage.getItem('theme') || 'light';
    document.body.className = theme;

    const generateBtn = document.getElementById('generate-btn');
    const resultDiv = document.getElementById('result');

    generateBtn.addEventListener('click', function() {
        // Generate a random 12-digit number (first 12 digits of EAN-13)
        let code = '';
        for (let i = 0; i < 12; i++) {
            code += Math.floor(Math.random() * 10);
        }

        // Calculate check digit
        let sum = 0;
        for (let i = 0; i < 12; i++) {
            sum += parseInt(code[i]) * (i % 2 === 0 ? 1 : 3);
        }
        let checkDigit = (10 - (sum % 10)) % 10;

        const fullCode = code + checkDigit;

        resultDiv.innerHTML = `
            <p><strong>Código GTIN-13/EAN-13 gerado:</strong> ${fullCode}</p>
            <p>Pode ser usado para gerar um código de barras.</p>
        `;
    });
});
