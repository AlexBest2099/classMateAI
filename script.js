document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('uploadForm');
    const docTypeSelect = document.getElementById('docType');
    const fileInput = document.getElementById('fileUpload');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const statusMessage = document.getElementById('statusMessage');
    const dropZone = document.getElementById('dropZone');
    const recentUploads = document.getElementById('recentUploads');

    setStatus('ready', 'Ready to upload');

    fileInput.addEventListener('change', function () {
        if (this.files.length > 0) {
            fileNameDisplay.textContent = this.files[0].name;
            fileNameDisplay.classList.remove('hidden');
        } else {
            fileNameDisplay.classList.add('hidden');
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(event => {
        dropZone.addEventListener(event, () => dropZone.classList.add('drag-over'));
    });

    ['dragleave', 'drop'].forEach(event => {
        dropZone.addEventListener(event, () => dropZone.classList.remove('drag-over'));
    });

    dropZone.addEventListener('drop', e => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileNameDisplay.textContent = files[0].name;
            fileNameDisplay.classList.remove('hidden');
        }
    });

    dropZone.addEventListener('click', () => fileInput.click());

    form.addEventListener('submit', async e => {
        e.preventDefault();
        const selectedType = docTypeSelect.value;
        const selectedFile = fileInput.files[0];

        if (!selectedType) return setStatus('error', 'Error: Please select a document type.');
        if (!selectedFile) return setStatus('error', 'Error: Please select a file to upload.');

        setStatus('uploading', 'Uploading your document...');

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('docType', selectedType);

        try {
            const response = await fetch('/api/upload', { method: 'POST', body: formData });

            if (response.ok) {
                const data = await response.json();
                setStatus('success', 'Success: File processed successfully!');
                addRecentUpload(selectedFile.name, selectedType);
                form.reset();
                fileNameDisplay.classList.add('hidden');
            } else {
                const errorData = await response.json().catch(() => null);
                const message = errorData?.message || 'Unknown error occurred';
                setStatus('error', `Error: Upload failed. ${message}`);
            }
        } catch (err) {
            console.error('Upload error:', err);
            setStatus('error', 'Error: Network error. Please try again.');
        }
    });

    function setStatus(type, message) {
        statusMessage.className = `mt-6 p-4 rounded-md text-sm font-medium`;
        statusMessage.classList.remove('hidden', 'animate-pulse');

        const styles = {
            ready: 'bg-gray-100 text-gray-800',
            uploading: 'bg-blue-100 text-blue-800 animate-pulse',
            success: 'bg-green-100 text-green-800',
            error: 'bg-red-100 text-red-800',
            warning: 'bg-yellow-100 text-yellow-800'
        };

        statusMessage.classList.add(...styles[type].split(' '));
        statusMessage.textContent = message;
    }

    function addRecentUpload(fileName, docType) {
        if (recentUploads.querySelector('.italic')) {
            recentUploads.innerHTML = '';
        }
    
        const time = new Date().toLocaleTimeString();
        const colorMap = {
            pdf: 'bg-red-100 text-red-800',
            docx: 'bg-indigo-100 text-indigo-800',
            image: 'bg-yellow-100 text-yellow-800'
        };
        
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between border border-gray-200 rounded-xl p-4'; // made it more rounded
        div.innerHTML = `
            <div class="flex items-center space-x-3">
                <svg class="h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div>
                    <p class="text-sm font-medium text-gray-900">${fileName}</p>
                    <p class="text-xs text-gray-500">Uploaded at ${time}</p>
                </div>
            </div>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorMap[docType]} capitalize">${docType}</span>
        `;
        recentUploads.insertBefore(div, recentUploads.firstChild);
    }
    
});
