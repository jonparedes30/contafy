-- Script para migrar campos de total a monto
-- Ejecutar en PostgreSQL

-- Renombrar campo total a monto en tabla empresa_venta
ALTER TABLE empresa_venta RENAME COLUMN total TO monto;

-- Renombrar campo total a monto en tabla empresa_compra  
ALTER TABLE empresa_compra RENAME COLUMN total TO monto;

-- Verificar cambios
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'empresa_venta' AND column_name IN ('total', 'monto');

SELECT column_name FROM information_schema.columns 
WHERE table_name = 'empresa_compra' AND column_name IN ('total', 'monto');