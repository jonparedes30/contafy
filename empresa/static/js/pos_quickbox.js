/**
 * POS QuickBox - Gestión del carrito POS
 * Maneja:
 * - Actualización del carrito visual
 * - Cálculo de totales
 * - Sincronización con formulario
 * - Eventos de cambio del carrito
 */

(function() {
    'use strict';

    /**
     * Inicializar el módulo de QuickBox POS
     */
    window.POSQuickBox = window.POSQuickBox || {};

    /**
     * Event emitter simple para cambios en el carrito
     */
    const cartChangeEvent = new CustomEvent('posCartChange', {
        detail: { timestamp: new Date(), source: 'pos_quickbox' }
    });

    /**
     * Notificar cambio en el carrito
     */
    POSQuickBox.notifyCartChange = function(data) {
        const event = new CustomEvent('posCartChange', {
            detail: Object.assign({ timestamp: new Date(), source: 'pos_quickbox' }, data || {})
        });
        document.dispatchEvent(event);
    };

    /**
     * Actualizar el total del carrito visualmente
     */
    POSQuickBox.updateCartTotals = function(subtotal, iva, total) {
        const subtotalEl = document.getElementById('pos-subtotal');
        const ivaEl = document.getElementById('pos-iva');
        const totalEl = document.getElementById('pos-total');

        if (subtotalEl) {
            subtotalEl.textContent = '$' + (subtotal || 0).toFixed(2);
        }
        if (ivaEl) {
            ivaEl.textContent = '$' + (iva || 0).toFixed(2);
        }
        if (totalEl) {
            totalEl.textContent = '$' + (total || 0).toFixed(2);
        }

        // Notificar cambio
        POSQuickBox.notifyCartChange({ subtotal, iva, total });
    };

    /**
     * Sincronizar cambio en cantidad o precio con el carrito
     */
    POSQuickBox.syncCartItem = function(rowElement, cantidad, precio) {
        try {
            const subtotal = Math.max(0, (cantidad || 0) * (precio || 0));
            const subtotalCell = rowElement.querySelector('[data-field="subtotal"]');
            if (subtotalCell) {
                subtotalCell.textContent = '$' + subtotal.toFixed(2);
            }
            POSQuickBox.notifyCartChange({ itemUpdated: true });
        } catch (err) {
            console.warn('Error sincronizando item del carrito:', err);
        }
    };

    /**
     * Limpiar el carrito visualmente
     */
    POSQuickBox.clearCart = function() {
        const tbody = document.getElementById('pos-cart-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No hay productos</td></tr>';
        }
        POSQuickBox.updateCartTotals(0, 0, 0);
    };

    /**
     * Agregar fila al carrito
     */
    POSQuickBox.addCartRow = function(productId, productName, cantidad, precio) {
        try {
            const tbody = document.getElementById('pos-cart-body');
            if (!tbody) return false;

            // Remover placeholder si existe
            const placeholder = tbody.querySelector('tr:has(td[colspan])');
            if (placeholder) {
                placeholder.remove();
            }

            const subtotal = Math.max(0, (cantidad || 0) * (precio || 0));
            const row = document.createElement('tr');
            row.id = 'cart-row-' + productId;
            row.innerHTML = `
                <td>${productName || 'Producto'}</td>
                <td><input type="number" class="form-control form-control-sm" value="${cantidad || 1}" min="1"></td>
                <td>$<input type="number" step="0.01" class="form-control form-control-sm" value="${(precio || 0).toFixed(2)}" style="width: 100px;"></td>
                <td data-field="subtotal">$${subtotal.toFixed(2)}</td>
                <td><button type="button" class="btn btn-sm btn-danger" onclick="POSQuickBox.removeCartRow( ${productId})">✕</button></td>
            `;

            tbody.appendChild(row);

            // Notificar
            POSQuickBox.notifyCartChange({ itemAdded: productId });
            return true;
        } catch (err) {
            console.error('Error agregando fila al carrito:', err);
            return false;
        }
    };

    /**
     * Eliminar fila del carrito
     */
    POSQuickBox.removeCartRow = function(productId) {
        try {
            const row = document.getElementById('cart-row-' + productId);
            if (row) {
                row.remove();
                POSQuickBox.notifyCartChange({ itemRemoved: productId });
            }
        } catch (err) {
            console.warn('Error removiendo fila del carrito:', err);
        }
    };

    /**
     * Obtener resumen del carrito actual
     */
    POSQuickBox.getCartSummary = function() {
        const rows = document.querySelectorAll('#pos-cart-body tr[id^="cart-row-"]');
        const items = [];
        let total = 0;

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 4) {
                const nombre = cells[0].textContent || '';
                const cantidad = parseFloat(cells[1].querySelector('input')?.value || 0);
                const precio = parseFloat(cells[2].querySelector('input')?.value || 0);
                const subtotal = cantidad * precio;

                items.push({ nombre, cantidad, precio, subtotal });
                total += subtotal;
            }
        });

        return { items, total, count: items.length };
    };

    /**
     * Hook para sincronizar cuando el formulario está listo
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Escuchar cambios en el carrito POS
        document.addEventListener('posCartChange', function(e) {
            // Aquí puedes agregar lógica adicional cuando el carrito cambia
            // Por ejemplo, actualizar el estado del botón 'Cobrar'
            const cobrarBtn = document.getElementById('pos-btn-cobrar');
            if (cobrarBtn) {
                const summary = POSQuickBox.getCartSummary();
                cobrarBtn.disabled = summary.count === 0;
            }
        });

        // Inicializar estado del botón
        const cobrarBtn = document.getElementById('pos-btn-cobrar');
        if (cobrarBtn) {
            cobrarBtn.disabled = true;
        }
    });

    // Exportar para scripts globales
    window.POSQuickBox = POSQuickBox;
})();
