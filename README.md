# Contadeus — Revisor Tributario v6

Cruza el **extracto SUNAT** con el **reporte de impuestos del cliente** y genera:

1. un resumen operativo interno para Contadeus;
2. un Excel de revisión; y
3. un mensaje listo para enviar por WhatsApp al cliente.

## Cambios principales v6

- Mensaje al cliente más claro y menos técnico.
- Encabezado del WhatsApp: **Reporte Tributario · RUC · fecha del reporte**.
- Despedida: **El equipo de Contadeus International**.
- AFP muestra: **Puede generar gastos adicionales de cobranza judicial.**
- ONP, Renta 5ta, Renta 4ta y Renta 2da muestran: **Puede generar multas e intereses.**
- IGV, Renta, EsSalud muestran: **Incluye intereses acumulados a la fecha.**
- ITAN muestra: **Pendiente de pago.**
- Las multas ya no se calculan ni se suman al total del cliente.
- Las retenciones/aportes afectos a multa solo muestran alerta interna: **Afecto a multa - revisar gradualidad**.

## IGV Justo

Orden de prioridad:

1. Usa la fecha IGV Justo encontrada en el reporte de impuestos.
2. Si no hay fecha en el reporte, usa fallback técnico: vencimiento normal + 3 meses.
3. Si no está marcada la opción de IGV Justo, usa el vencimiento normal del cronograma SUNAT.

## TIM

La TIM se calcula con tasa histórica básica SUNAT en moneda nacional:

- desde 01/04/2021: 0.9% mensual / 30
- desde 01/04/2020: 1.0% mensual / 30
- desde 01/03/2010: 1.2% mensual / 30

## Qué detecta

1. 🚨 Retenciones vencidas afectas a multa
2. 🔴 Impuestos vencidos sin pagar
3. 🟡 Pagos en SUNAT pendientes de actualizar en el reporte
4. 🟠 Pagados con atraso, con TIM generada y alerta de multa si aplica
5. ✅ Pagos al día

## Inputs

- RUC de 11 dígitos
- PDF SUNAT: **Reporte Electrónico de Declaraciones y Pagos**
- Reporte de impuestos del cliente:
  - Google Sheet compartido como “cualquier persona con el enlace puede ver”, o
  - PDF exportado del reporte

## Actualización en GitHub

Reemplaza estos archivos:

- `app.py`
- `README.md`
- `requirements.txt`

Luego haz commit en GitHub. Streamlit Cloud debería actualizar automáticamente.
