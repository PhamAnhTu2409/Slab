async function processSlab() {
    if (!currentFile) {
        addLog('❌ Vui lòng chọn file cấu trúc trước!', 'error');
        return;
    }

    showLoading();
    
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('h', document.getElementById('hIndex').value);
    formData.append('k', document.getElementById('kIndex').value);
    formData.append('l', document.getElementById('lIndex').value);
    formData.append('vacuum', document.getElementById('vacuumSlider').value);
    formData.append('layers', document.getElementById('layers').value);
    formData.append('format', document.getElementById('outputPOSCAR').checked ? 'poscar' : 'qe');

    try {
        const response = await fetch('http://localhost:5000/process', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        // Hiển thị logs từ backend
        result.logs.forEach(log => {
            addLog(log.message, log.type);
        });

        if (result.success) {
            // Lưu kết quả thật từ backend
            processingResults = {
                content: result.file_content,
                filename: result.filename,
                format: result.format
            };
            showDownloadSection();
        } else {
            addLog('❌ ' + result.error, 'error');
        }
    } catch (error) {
        addLog('❌ Lỗi kết nối đến server: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}   