// Función para abrir el modal de edición
function editarProducto(id, nombre, descripcion, precio) {
    // Mostrar el modal
    document.getElementById('modal-editar').style.display = 'block';
    
    // Rellenar los campos del formulario
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-nombre').value = nombre;
    document.getElementById('edit-descripcion').value = descripcion || '';
    document.getElementById('edit-precio').value = precio;
}

// Función para cerrar el modal
function cerrarModal() {
    document.getElementById('modal-editar').style.display = 'none';
}

// Cerrar el modal si se hace clic fuera de él
window.onclick = function(event) {
    const modal = document.getElementById('modal-editar');
    if (event.target === modal) {
        cerrarModal();
    }
}

// Cerrar modal con la tecla ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        cerrarModal();
    }
});
// Función para abrir el modal de edición
function editarProducto(id, nombre, descripcion, precio) {
    // Mostrar el modal
    const modal = document.getElementById('modal-editar');
    modal.style.display = 'block';
    document.body.classList.add('modal-open');
    
    // Rellenar los campos del formulario
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-nombre').value = nombre;
    document.getElementById('edit-descripcion').value = descripcion || '';
    document.getElementById('edit-precio').value = precio;
}

// Función para cerrar el modal
function cerrarModal() {
    const modal = document.getElementById('modal-editar');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    
    // Limpiar el formulario
    document.getElementById('edit-id').value = '';
    document.getElementById('edit-nombre').value = '';
    document.getElementById('edit-descripcion').value = '';
    document.getElementById('edit-precio').value = '';
}

// Cerrar el modal si se hace clic fuera de él
window.onclick = function(event) {
    const modal = document.getElementById('modal-editar');
    if (event.target === modal) {
        cerrarModal();
    }
}

// Cerrar modal con la tecla ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        cerrarModal();
    }
});

// Prevenir múltiples envíos del formulario
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Procesando...';
            }
        });
    });
    
    // Lazy loading para imágenes
    const images = document.querySelectorAll('img[loading="lazy"]');
    if ('loading' in HTMLImageElement.prototype) {
        // El navegador soporta lazy loading nativo
        images.forEach(img => {
            img.src = img.dataset.src || img.src;
        });
    }
});