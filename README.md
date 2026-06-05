# Contadeus — Revisor Tributario v5

Cruza el **extracto SUNAT** con el **reporte de impuestos del cliente** y genera un resumen operativo para Contadeus y un mensaje listo para WhatsApp.

## Cambios principales v5

- El **reporte de impuestos es la fuente principal** para IGV Justo.
- Si la fila del IGV contiene una fecha de IGV Justo / fecha máxima de pago, el sistema usa esa fecha.
- Si no encuentra fecha en el reporte, aplica fallback técnico: **vencimiento original + 3 meses**.
- La TIM se calcula con tasa histórica básica SUNAT en moneda nacional:
  - desde 01/04/2021: 0.9% mensual / 30
  - desde 01/04/2020: 1.0% mensual / 30
  - desde 01/03/2010: 1.2% mensual / 30
- Las retenciones/aportes fuera de plazo ya **no muestran monto exacto de multa**.
- Para ONP, Renta 5ta, Renta 4ta y Renta 2da, el sistema solo muestra: **Afecto a multa - revisar gradualidad**.

## Qué detecta

1. 🚨 Retenciones vencidas afectas a multa
2. 🔴 Impuestos vencidos sin pagar
3. 🟡 Pagos en SUNAT pendientes de actualizar en el reporte
4. 🟠 Pagados con atraso, con TIM generada
5. ✅ Pagos al día

## Inputs

- RUC de 11 dígitos
- PDF SUNAT: **Reporte Electrónico de Declaraciones y Pagos**
- Reporte de impuestos del cliente:
  - Google Sheet compartido como “cualquier persona con el enlace puede ver”, o
  - PDF exportado del reporte

## Regla IGV Justo

Orden de prioridad:

1. Fecha IGV Justo encontrada en el reporte de impuestos.
2. Si no hay fecha, vencimiento original del periodo + 3 meses.
3. Si no está marcado “Acogida a IGV Justo”, usa el vencimiento normal del cronograma SUNAT.

## Actualización en GitHub

Reemplaza estos archivos:

- `app.py`
- `README.md`
- `requirements.txt`

Streamlit Cloud debería actualizar automáticamente después del commit.
