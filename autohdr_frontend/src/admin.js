// Admin Dashboard Logic - AutoHDR Key Management

const API_BASE = import.meta.env?.VITE_API_BASE || "https://autohdr-backend.up.railway.app";

// DOM Elements
const keyForm = document.getElementById('key-form');
const adminPassInput = document.getElementById('admin-pass');
const keyNameInput = document.getElementById('key-name');
const btnCreate = document.getElementById('btn-create');
const btnList = document.getElementById('btn-list');
const btnCopy = document.getElementById('btn-copy');
const resultDiv = document.getElementById('new-key-result');
const displayKey = document.getElementById('display-key');
const keysBody = document.getElementById('keys-body');

/**
 * Hiển thị thông báo Toast đơn giản
 */
function showToast(message, isError = false) {
    // Tạm thời dùng alert, có thể cải tiến UI sau
    alert(message);
}

/**
 * Liệt kê danh sách keys
 */
async function loadKeys() {
    const password = adminPassInput.value;
    if (!password) {
        showToast("Vui lòng nhập mật khẩu Admin!");
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/admin/keys/list`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Sai mật khẩu hoặc lỗi server");
        }

        const keys = await response.json();
        renderKeys(keys);
    } catch (error) {
        showToast(error.message, true);
    }
}

/**
 * Render bảng danh sách keys
 */
function renderKeys(keys) {
    if (!keys || keys.length === 0) {
        keysBody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 2rem; color: var(--text-light);">Chưa có Key nào được tạo.</td></tr>`;
        return;
    }

    keysBody.innerHTML = keys.map(k => {
        const expires = k.expires_at ? new Date(k.expires_at).toLocaleDateString('vi-VN') : 'Vĩnh viễn';
        const machine = k.machine_id ? `<span style="font-size: 0.7rem; color: var(--text-light);">${k.machine_id.substring(0, 15)}...</span>` : '<span style="color: var(--text-light);">Chưa dùng</span>';
        
        return `
            <tr style="border-bottom: 1px solid var(--border);">
                <td style="padding: 0.75rem;">${k.name}</td>
                <td style="padding: 0.75rem;"><code style="background: #f1f5f9; padding: 2px 4px; border-radius: 4px; font-weight: 600;">${k.key}</code></td>
                <td style="padding: 0.75rem;">${expires}</td>
                <td style="padding: 0.75rem;">${machine}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Tạo Key mới
 */
keyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const password = adminPassInput.value;
    const name = keyNameInput.value;
    const expiryType = document.querySelector('input[name="expiry"]:checked').value;
    
    const payload = {
        password,
        name,
        forever: expiryType === 'forever',
        days: expiryType === '30' ? 30 : null
    };

    btnCreate.disabled = true;
    btnCreate.innerText = "Đang tạo...";

    try {
        const response = await fetch(`${API_BASE}/api/admin/keys/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Không thể tạo Key");
        }

        const data = await response.json();
        const record = data.record;

        // Hiển thị kết quả
        displayKey.innerText = record.key;
        resultDiv.style.display = 'block';
        showToast("Tạo Key thành công!");
        
        // Cập nhật lại danh sách
        loadKeys();
        
    } catch (error) {
        showToast(error.message, true);
    } finally {
        btnCreate.disabled = false;
        btnCreate.innerText = "Tạo License Key";
    }
});

btnList.addEventListener('click', loadKeys);

btnCopy.addEventListener('click', () => {
    const key = displayKey.innerText;
    navigator.clipboard.writeText(key).then(() => {
        btnCopy.innerText = "Coiped!";
        setTimeout(() => btnCopy.innerText = "Copy", 2000);
    });
});

// Lưu mật khẩu vào localStorage nếu đã nhập (tiện dụng cho admin)
adminPassInput.addEventListener('change', () => {
    sessionStorage.setItem('admin_password', adminPassInput.value);
});

// Load mật khẩu từ session nếu có
window.addEventListener('load', () => {
    const saved = sessionStorage.getItem('admin_password');
    if (saved) adminPassInput.value = saved;
});
