# Contadeus — Revisor Tributario v3

## Qué hace
Cruza el extracto SUNAT con el reporte de impuestos del cliente y produce 4 resultados:

1. 🟡 **Falta actualizar** — pagos que SUNAT registra pero no están en tu reporte
2. 🔴 **Vencidos sin pagar** — declarados pero no pagados, SUNAT puede cobrar coactivamente
3. 🟠 **Pagados con atraso** — generan TIM y multa 5% UIT (ONP/R5ta/R4ta/R2da)
4. ✅ **Al día** — correcto

## Inputs
- RUC (calcula dígito automáticamente)
- PDF de SUNAT: "Reporte Electrónico de Declaraciones y Pagos"
- Reporte de impuestos: link del Google Sheet O PDF exportado

## Actualizar
Editar app.py en GitHub → Streamlit Cloud actualiza en 1 minuto.

## Cambios frecuentes
- Nueva UIT: buscar `UIT = {`
- Nuevo cronograma SUNAT: buscar `CRON = {`
