document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.querySelector('input[type="file"]');
    const form = document.querySelector('form');
    const resultBox = document.querySelector('.result');
    const preTag = resultBox ? resultBox.querySelector('pre') : null;

    // Loader element
    const loader = document.createElement('div');
    loader.id = 'loader';
    loader.innerHTML = `<div class="spinner"></div><p>Analyzing your prescription...</p>`;
    loader.style.display = 'none';
    loader.style.textAlign = 'center';
    document.body.appendChild(loader);

    // Medicine keywords (sample)
    const medicineKeywords = ['paracetamol', 'amoxicillin', 'ibuprofen', 'cetirizine'];

    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                loader.style.display = 'block'; // show spinner
                setTimeout(() => {
                    form.submit(); // auto-submit after short delay
                }, 500);
            }
        });
    }

    // Highlight medicine names
    if (preTag) {
        let text = preTag.textContent;
        medicineKeywords.forEach(med => {
            const regex = new RegExp(`\\b(${med})\\b`, 'gi');
            text = text.replace(regex, '<mark>$1</mark>');
        });
        preTag.innerHTML = text; // update with highlighted names
    }

    // Copy Button
    if (resultBox && !document.querySelector('#copyBtn')) {
        const copyBtn = document.createElement('button');
        copyBtn.id = 'copyBtn';
        copyBtn.textContent = "📋 Copy Extracted Text";
        Object.assign(copyBtn.style, {
            marginTop: "10px",
            padding: "8px 16px",
            border: "none",
            borderRadius: "5px",
            backgroundColor: "#007BFF",
            color: "white",
            cursor: "pointer"
        });

        resultBox.appendChild(copyBtn);

        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(preTag.textContent).then(() => {
                copyBtn.textContent = "✅ Copied!";
                setTimeout(() => copyBtn.textContent = "📋 Copy Extracted Text", 2000);
            });
        });
    }

    // Translation Button
    if (resultBox && !document.querySelector('#translateBtn')) {
        const translateBtn = document.createElement('button');
        translateBtn.id = 'translateBtn';
        translateBtn.textContent = "🌐 Translate to Hindi";
        translateBtn.style.cssText = copyBtn.style.cssText;

        resultBox.appendChild(translateBtn);

        translateBtn.addEventListener('click', () => {
            // Mock translated result
            preTag.innerHTML = "<i>यह एक उदाहरण अनुवाद है।</i><br>" + preTag.innerHTML;
            translateBtn.disabled = true;
            translateBtn.textContent = "✅ Translated";
        });
    }

});
