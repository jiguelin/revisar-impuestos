# Contadeus — Revisor Tributario

Sistema de revisión tributaria para estudios contables peruanos.
Cruza el extracto SUNAT con el reporte de impuestos del cliente.

---

## ¿Qué hace?

Sube dos archivos y el sistema detecta automáticamente:

| Categoría | Descripción |
|-----------|-------------|
| 🔴 Vencidos + multa | ONP / R5ta / R4ta / R2da vencidos — afectos a multa |
| 🔴 Vencidos sin pagar | IGV / Renta / EsSalud / Fracc sin pagar |
| 🟡 Falta actualizar | Pagado en SUNAT pero no registrado en el reporte |
| 🟠 Pagados con atraso | Registrado pero fuera de fecha — TIM generado |
| ✅ Al día | Correcto |

Al final genera un **mensaje listo para WhatsApp** con las obligaciones
prioritarias del cliente, ordenadas por urgencia.

---

## Cómo usar

1. Ingresa el RUC (11 dígitos) — el dígito y el cronograma se calculan solos
2. Sube el **PDF de SUNAT**: SUNAT SOL → Mis declaraciones y pagos → Reporte electrónico → PDF
3. Ingresa el **link del Google Sheet** del reporte de impuestos del cliente
   *(o sube el PDF exportado desde Google Sheets → Archivo → Descargar → PDF)*
4. Clic en **Analizar**
5. Descarga el Excel o copia el mensaje para WhatsApp

> Puedes subir varios PDFs SUNAT a la vez (2022 + 2023 + 2024 + 2025 + 2026).

---

## Regla fundamental

**El reporte de impuestos es la fuente de verdad.**

Si una sección fue eliminada del reporte porque ya estaba todo pagado
→ el sistema la ignora completamente y no genera alertas falsas.

---

## Orden de prioridades de pago

| # | Tributo | Razón |
|---|---------|-------|
| 1 | Renta 5ta categoría | Retención — multa 100% + riesgo penal |
| 2 | Renta 4ta categoría | Retención — multa 100% + riesgo penal |
| 3 | Renta 2da categoría | Retención — multa 100% + riesgo penal |
| 4 | ONP | Retención previsional — no fraccionable |
| 5 | Fraccionamiento Art.36 | Compromiso firmado SUNAT — reactiva deuda original |
| 6 | AFP | Retención previsional — cobranza judicial |
| 7 | EsSalud | |
| 8 | Renta MYPE / RER / General | Fraccionable |
| 9 | IGV | Fraccionable — ordenado por antigüedad |
| 99 | SIS | Cronograma propio — seguimiento independiente |

---

## TIM (Tasa de Interés Moratorio)

- **Vigente desde 01/04/2021:** 0.9% mensual = **0.03% diario** (RS 044-2021/SUNAT)
- El sistema usa historial de tasas para calcular correctamente deudas de años anteriores
- Las multas **no usan TIM** desde 01/01/2024 (Ley 31962) — el sistema solo alerta, no calcula monto de multa

---

## IGV Justo (Ley 30524)

- Si el reporte tiene fecha en columna "FECHA IGV JUSTO" → usa esa fecha directamente
- Si no tiene fecha → calcula automáticamente: vencimiento normal + 3 meses
- El checkbox en la app solo sirve como respaldo cuando el reporte no tiene la fecha

---

## Cronogramas SUNAT incluidos

| Año | Fuente |
|-----|--------|
| 2022 | RS 189-2021/SUNAT — sunat.gob.pe |
| 2023 | RS 281-2022/SUNAT — sunat.gob.pe |
| 2024 | RS 281-2022/SUNAT — sunat.gob.pe |
| 2025 | El Peruano — confirmado Contadeus |
| 2026 | sunat.gob.pe |

---

## Actualizar la app (GitHub + Streamlit Cloud)

1. Abre `app.py` en GitHub → lápiz (editar) → hacer cambio → **Commit changes**
2. Streamlit Cloud detecta el cambio y actualiza en ~1 minuto
3. No hay que reinstalar nada ni tocar servidores

### Cambios frecuentes

| Qué cambiar | Dónde buscarlo en app.py |
|-------------|--------------------------|
| Nueva UIT | `UIT = {` |
| Nueva TIM | `TIM_HIST = [` |
| Nuevo cronograma SUNAT | `CRON = {` |
| Nuevo tributo | `TRIBUTO = {` y `SMAP = [` |
| Mensajes al cliente | `MENSAJE_CLIENTE = {` |
| Prioridades de pago | `PRIORIDAD_PAGO = {` |

---

## AFP y SIS

- **AFP:** aparece como pendiente manual en la app. No tiene vencimiento SUNAT.
  El cliente ve: *"Puede generar gastos adicionales de cobranza judicial."*
- **SIS:** cronograma propio por empresa, seguimiento independiente.
  Aparece como pendiente manual sin cálculo de intereses.

---

## Instalación local (opcional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

*Contadeus International SAC — Sistema interno*
