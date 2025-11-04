// Biến toàn cục
let currentFile = null;
let processingResults = {
    poscar: null,
    qe: null
};
const API_BASE_URL = 'http://localhost:5000';

// Khởi tạo ứng dụng
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
    checkBackendConnection();
});

function initEventListeners() {
    // File upload
    const fileUpload = document.getElementById('fileUpload');
    const fileInput = document.getElementById('fileInput');
    
    fileUpload.addEventListener('click', () => fileInput.click());
    fileUpload.addEventListener('dragover', handleDragOver);
    fileUpload.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Slider
    const vacuumSlider = document.getElementById('vacuumSlider');
    vacuumSlider.addEventListener('input', updateVacuumValue);
    
    // Process button
    const processBtn = document.getElementById('processBtn');
    processBtn.addEventListener('click', processSlab);
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function processFile(file) {
    currentFile = file;
    
    // Hiển thị thông tin file
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('fileFormat').textContent = detectFileFormat(file.name);
    document.getElementById('fileInfo').style.display = 'block';
    
    // Log thông tin
    addLog(`📁 Đã chọn file: ${file.name}`, 'success');
    addLog(`📏 Kích thước: ${formatFileSize(file.size)}`, 'info');
    addLog(`🔍 Định dạng: ${detectFileFormat(file.name)}`, 'info');
}

function detectFileFormat(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    switch(ext) {
        case 'vasp': case 'poscar': return 'POSCAR/VASP';
        case 'cif': return 'CIF';
        case 'in': case 'txt': return 'Quantum ESPRESSO';
        default: return 'Tự động nhận diện';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateVacuumValue() {
    const slider = document.getElementById('vacuumSlider');
    const value = document.getElementById('vacuumValue');
    value.textContent = slider.value;
}

function addLog(message, type = 'info') {
    const results = document.getElementById('results');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    
    const icon = getLogIcon(type);
    logEntry.innerHTML = `<span class="log-icon">${icon}</span> ${message}`;
    
    results.appendChild(logEntry);
    results.scrollTop = results.scrollHeight;
}

function getLogIcon(type) {
    switch(type) {
        case 'success': return '✅';
        case 'error': return '❌';
        case 'warning': return '⚠️';
        default: return 'ℹ️';
    }
}

async function checkBackendConnection() {
    const backendStatus = document.getElementById('backendStatus');
    const apiStatus = document.getElementById('apiStatus');
    
    backendStatus.textContent = 'Đang kiểm tra...';
    backendStatus.className = 'status-value checking';
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            timeout: 5000
        });
        
        if (response.ok) {
            backendStatus.textContent = 'Đã kết nối';
            backendStatus.className = 'status-value connected';
            apiStatus.textContent = 'Sẵn sàng';
            apiStatus.className = 'status-value ready';
            addLog('✅ Backend đã sẵn sàng!', 'success');
        } else {
            throw new Error('Backend response not OK');
        }
    } catch (error) {
        backendStatus.textContent = 'Mất kết nối';
        backendStatus.className = 'status-value disconnected';
        apiStatus.textContent = 'Không khả dụng';
        apiStatus.className = 'status-value disconnected';
        addLog('❌ Không thể kết nối đến backend. Đảm bảo server đang chạy trên port 5000.', 'error');
        addLog('💡 Chạy lệnh: python app.py trong thư mục backend', 'info');
    }
}

async function processSlab() {
    if (!currentFile) {
        addLog('❌ Vui lòng chọn file cấu trúc trước!', 'error');
        return;
    }

    showLoading();
    clearResults();
    
    // Cập nhật trạng thái
    document.getElementById('apiStatus').textContent = 'Đang xử lý...';
    document.getElementById('apiStatus').className = 'status-value processing';

    addLog('🔄 Bắt đầu xử lý tạo surface...', 'info');
    addLog(`📐 Chỉ số Miller: (${document.getElementById('hIndex').value},${document.getElementById('kIndex').value},${document.getElementById('lIndex').value})`, 'info');
    addLog(`📏 Chân không: ${document.getElementById('vacuumSlider').value}Å`, 'info');
    addLog(`📊 Số lớp: ${document.getElementById('layers').value}`, 'info');

    try {
        // Tạo cả 2 định dạng
        await createBothFormats();
        
        // Cập nhật trạng thái thành công
        document.getElementById('apiStatus').textContent = 'Hoàn thành';
        document.getElementById('apiStatus').className = 'status-value connected';
        
        addLog('🎉 Đã tạo thành công cả 2 định dạng!', 'success');
        addLog('💡 Bạn có thể download POSCAR cho VASP hoặc QE Input cho Quantum ESPRESSO', 'info');
        
    } catch (error) {
        console.error('Processing Error:', error);
        addLog('❌ Lỗi xử lý: ' + error.message, 'error');
        document.getElementById('apiStatus').textContent = 'Lỗi';
        document.getElementById('apiStatus').className = 'status-value disconnected';
    } finally {
        hideLoading();
    }
}

async function createBothFormats() {
    // Tạo POSCAR
    addLog('📄 Đang tạo file POSCAR...', 'info');
    const poscarResult = await createFormat('poscar');
    processingResults.poscar = poscarResult;
    addLog('✅ Đã tạo POSCAR thành công', 'success');
    
    // Tạo QE Input
    addLog('⚡ Đang tạo file QE Input...', 'info');
    const qeResult = await createFormat('qe');
    processingResults.qe = qeResult;
    addLog('✅ Đã tạo QE Input thành công', 'success');
    
    // Hiển thị thông tin kết quả (lấy từ kết quả đầu tiên)
    displayResultsInfo(poscarResult.results);
    showDownloadSection();
}

async function createFormat(format) {
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('h', document.getElementById('hIndex').value);
    formData.append('k', document.getElementById('kIndex').value);
    formData.append('l', document.getElementById('lIndex').value);
    formData.append('vacuum', document.getElementById('vacuumSlider').value);
    formData.append('layers', document.getElementById('layers').value);
    formData.append('format', format);

    const response = await fetch(`${API_BASE_URL}/process`, {
        method: 'POST',
        body: formData
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || `Lỗi tạo định dạng ${format}`);
    }

    return result;
}

function displayResultsInfo(results) {
    if (!results) return;
    
    document.getElementById('infoNatoms').textContent = results.natoms || '-';
    document.getElementById('infoNtypes').textContent = results.ntypes || '-';
    document.getElementById('infoElements').textContent = results.elements ? results.elements.join(', ') : '-';
    document.getElementById('infoVacuum').textContent = results.vacuum_thickness ? `${results.vacuum_thickness.toFixed(2)} Å` : '-';
    document.getElementById('infoSlabThickness').textContent = results.slab_thickness ? `${results.slab_thickness.toFixed(2)} Å` : '-';
    document.getElementById('infoSurfaceArea').textContent = results.surface_area ? `${results.surface_area.toFixed(2)} Å²` : '-';
    
    document.getElementById('resultsInfo').style.display = 'block';
}

function clearResults() {
    document.getElementById('results').innerHTML = '';
    document.getElementById('downloadSection').style.display = 'none';
    document.getElementById('resultsInfo').style.display = 'none';
    processingResults = { poscar: null, qe: null };
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('processBtn').disabled = true;
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('processBtn').disabled = false;
}

function showDownloadSection() {
    document.getElementById('downloadSection').style.display = 'block';
}

function downloadFile(type) {
    const result = processingResults[type];
    
    if (!result || !result.file_content) {
        addLog(`❌ Không có kết quả cho định dạng ${type.toUpperCase()}!`, 'error');
        return;
    }

    try {
        const blob = new Blob([result.file_content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = result.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        addLog(`✅ Đã download: ${result.filename}`, 'success');
        
    } catch (error) {
        addLog(`❌ Lỗi download: ${error.message}`, 'error');
    }
}

async function downloadBoth() {
    if (!processingResults.poscar || !processingResults.qe) {
        addLog('❌ Chưa có đủ kết quả để download cả hai!', 'error');
        return;
    }

    addLog('📦 Đang download cả hai định dạng...', 'info');
    
    // Download POSCAR
    downloadFile('poscar');
    
    // Đợi một chút rồi download QE
    setTimeout(() => {
        downloadFile('qe');
        addLog('🎉 Đã download cả hai định dạng thành công!', 'success');
    }, 500);
}

// Utility function để thêm timeout cho fetch
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const [resource, config] = args;
    const timeout = 60000; // 60 seconds cho xử lý lớn
    
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    return originalFetch(resource, {
        ...config,
        signal: controller.signal
    }).then(response => {
        clearTimeout(id);
        return response;
    }).catch(error => {
        clearTimeout(id);
        throw error;
    });
};