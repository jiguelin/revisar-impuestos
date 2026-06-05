# Contadeus — Revisor Tributario v4

Aplicación Streamlit para cruzar el **Extracto SUNAT de Declaraciones y Pagos** con el **Reporte de Impuestos del cliente**.

## Cambios principales v4

1. **IGV Justo corregido**
   - Ya no usa vencimiento + 1 mes.
   - Si el reporte contiene una fecha máxima del padrón IGV Justo, usa esa fecha.
   - También permite pegar fechas máximas manualmente, por ejemplo:
     ```text
     202603=24/07/2026
     ABRIL 2026 25/08/2026
     ```
   - Si no hay fecha específica, usa fallback conservador: vencimiento original + 3 meses.

2. **TIM corregida**
   - Usa tabla histórica básica SUNAT.
   - Desde 01/04/2021 usa 0.9% mensual / 30 días.
   - Calcula intereses solo desde el día siguiente al vencimiento real o prorrogado.

3. **Multas corregidas como alerta**
   - Ya no calcula multa exacta.
   - Para retenciones/aportes fuera de plazo muestra: `Afecto a multa - revisar gradualidad`.
   - El monto final al cliente no incluye multa, solo tributo + TIM.

4. **Mensaje para cliente mejorado**
   - Ordena por prioridad técnica.
   - No muestra cálculos internos de multa.
   - Advierte de regularización sin alarmar innecesariamente.

## Inputs

- RUC del cliente.
- Nombre del cliente.
- PDF SUNAT: `Reporte Electrónico de Declaraciones y Pagos`.
- Reporte de impuestos: Google Sheet o PDF exportado.
- Opcional: fechas máximas IGV Justo copiadas del padrón SUNAT.

## Recomendación operativa

Para IGV Justo, lo más seguro es consultar el padrón SUNAT y pegar la fecha máxima correspondiente en el campo opcional de la app.

Padrón SUNAT: `Consulta Padrón de Prórroga de Pago de IGV`.

## Deploy

Subir estos tres archivos al repositorio de GitHub conectado a Streamlit Cloud:

- `app.py`
- `README.md`
- `requirements.txt`

Streamlit Cloud actualizará automáticamente después del commit.
