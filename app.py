import streamlit as st
import pandas as pd
import pdfplumber
import re
import requests
from io import BytesIO, StringIO
from datetime import datetime, date

st.set_page_config(
    page_title="Contadeus — Revisor Tributario",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  .main{background:#F8FAFC;} .block-container{padding-top:1.5rem;}
  .hdr{background:linear-gradient(135deg,#1B2A8C,#2563EB);padding:24px 30px;
       border-radius:14px;margin-bottom:24px;color:#fff;}
  .hdr h1{margin:0;font-size:1.75rem;font-weight:800;}
  .hdr p{margin:5px 0 0;opacity:.82;font-size:.93rem;}
  .kpi{background:#fff;border-radius:12px;padding:16px 18px;text-align:center;
       border:1px solid #E5E7EB;box-shadow:0 2px 6px rgba(0,0,0,.05);}
  .kpi .n{font-size:2rem;font-weight:800;line-height:1.1;}
  .kpi .l{font-size:.73rem;color:#6B7280;margin-top:3px;font-weight:500;}
  .red{color:#DC2626;}.grn{color:#16A34A;}.amb{color:#D97706;}.blu{color:#1B2A8C;}
  .card{border-radius:10px;padding:12px 16px;margin:6px 0;font-size:.87rem;line-height:1.65;}
  .card-r{background:#FEF2F2;border-left:4px solid #DC2626;}
  .card-a{background:#FFFBEB;border-left:4px solid #F59E0B;}
  .card-o{background:#FFF7ED;border-left:4px solid #EA580C;}
  .card-g{background:#F0FDF4;border-left:4px solid #16A34A;}
  .card-b{background:#EFF6FF;border-left:4px solid #2563EB;}
  .badge{display:inline-block;padding:2px 9px;border-radius:20px;
         font-size:.73rem;font-weight:700;margin-right:5px;}
  .badge-r{background:#FEE2E2;color:#991B1B;}
  .badge-a{background:#FEF3C7;color:#92400E;}
  .badge-g{background:#D1FAE5;color:#065F46;}
  .sep{height:1px;background:#E5E7EB;margin:20px 0;}
  .emp{background:#EEF2FF;border:2px solid #1B2A8C;color:#1B2A8C;
       padding:6px 16px;border-radius:22px;font-weight:700;font-size:.9rem;
       display:inline-block;margin-bottom:14px;}
  .yr{background:#1F2937;color:#fff;padding:7px 16px;border-radius:8px;
      font-weight:700;font-size:.88rem;margin:16px 0 8px;display:inline-block;}
  .stitle{font-size:1rem;font-weight:700;margin:14px 0 6px;color:#111827;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
UIT = {2023:4950, 2024:5150, 2025:5350, 2026:5500, 2027:5500}
TIM_D = 0.0004
CON_MULTA = {"3052","3042","3022","5310"}

TRIBUTO = {
    "1011":"IGV","3031":"Renta 3ra (General)","3111":"Renta RER (1.5%)",
    "3121":"Renta MYPE (1%)","3038":"ITAN","3052":"Renta 5ta Categoría",
    "3042":"Renta 4ta Categoría","3022":"Renta 2da Categoría",
    "5210":"EsSalud","5310":"ONP","8021":"Fraccionamiento Art.36",
}

MESES = {
    "ENERO":1,"FEBRERO":2,"MARZO":3,"ABRIL":4,"MAYO":5,"JUNIO":6,
    "JULIO":7,"AGOSTO":8,"SETIEMBRE":9,"SEPTIEMBRE":9,
    "OCTUBRE":10,"NOVIEMBRE":11,"DICIEMBRE":12
}
MES_NOM = {
    1:"ENERO",2:"FEBRERO",3:"MARZO",4:"ABRIL",5:"MAYO",6:"JUNIO",
    7:"JULIO",8:"AGOSTO",9:"SETIEMBRE",10:"OCTUBRE",11:"NOVIEMBRE",12:"DICIEMBRE"
}

CRON = {
    2024:{1:[15,16,19,19,20,20,21,21,22,22,23],2:[15,16,18,18,19,19,20,20,21,21,22],
          3:[15,18,19,19,20,20,21,21,22,22,25],4:[15,16,17,17,18,18,19,19,22,22,23],
          5:[14,15,16,16,17,17,20,20,21,21,22],6:[14,17,18,18,19,19,20,20,21,21,24],
          7:[15,16,17,17,18,18,19,19,22,22,23],8:[14,15,16,16,19,19,20,20,21,21,22],
          9:[13,16,17,17,18,18,19,19,20,20,23],10:[15,16,17,17,18,18,21,21,22,22,23],
          11:[14,15,18,18,19,19,20,20,21,21,22],12:[15,16,17,17,20,20,21,21,22,22,23]},
    2025:{1:[17,18,19,19,20,20,21,21,24,24,25],2:[17,18,19,19,20,20,21,21,24,24,25],
          3:[18,19,20,20,21,21,24,24,25,25,26],4:[17,22,23,23,24,24,25,25,28,28,29],
          5:[15,16,19,19,20,20,21,21,22,22,23],6:[16,17,18,18,19,19,20,20,23,23,24],
          7:[15,16,17,17,18,18,21,21,22,22,23],8:[18,19,20,20,21,21,22,22,25,25,26],
          9:[15,16,17,17,18,18,19,19,22,22,23],10:[15,16,17,17,20,20,21,21,22,22,23],
          11:[17,18,19,19,20,20,21,21,24,24,25],12:[15,16,17,17,18,18,19,19,22,22,23]},
    2026:{1:[16,17,18,18,19,19,20,20,23,23,24],2:[16,17,18,18,19,19,20,20,23,23,24],
          3:[17,20,21,21,22,22,23,23,24,24,27],4:[18,19,20,20,21,21,22,22,25,25,26],
          5:[15,16,17,17,18,18,19,19,22,22,23],6:[15,16,17,17,20,20,21,21,22,22,24],
          7:[18,19,20,20,21,21,24,24,25,25,26],8:[15,16,17,17,18,18,21,21,22,22,23],
          9:[16,19,20,20,21,21,22,22,23,23,26],10:[16,17,18,18,19,19,20,20,23,23,24],
          11:[17,18,21,21,22,22,23,23,24,24,28],12:[18,19,20,20,21,21,22,22,25,25,26]},
}

def fecha_venc(anio, mes, dig):
    dias = CRON.get(anio, CRON[2026]).get(mes, [28]*11)
    dia  = dias[min(dig,10)]
    mv,av = mes+1,anio
    if mv>12: mv,av=1,anio+1
    try:    return date(av,mv,dia)
    except: return date(av,mv,28)

def fecha_venc_igv_justo(anio, mes, dig):
    m2,a2=mes+1,anio
    if m2>12: m2,a2=1,anio+1
    return fecha_venc(a2,m2,dig)

def calc_tim(imp, dias): return round(imp*TIM_D*max(dias,0),2)
def calc_multa(anio): return UIT.get(anio,5500)*0.05

def num(s):
    """Convierte cualquier formato numérico a float. (321)/-321/2,681/2.681 todos correctos."""
    s=str(s).strip().strip("()").lstrip("-").replace(" ","")
    if not s or s in ["","nan","None","-"]: return 0.0
    hc,hd=","in s,"."in s
    if hc and hd:
        s=s.replace(",","") if s.index(",")<s.index(".") else s.replace(".","").replace(",",".")
    elif hc:
        p=s.split(",")
        s=s.replace(",","") if len(p)==2 and len(p[1])==3 else s.replace(",",".")
    elif hd:
        p=s.split(".")
        if len(p)==2 and len(p[1])==3: s=s.replace(".","")
    try: return float(s)
    except: return 0.0

def es_pago(s):
    s=str(s).strip()
    return s.startswith("(") or s.startswith("-")

# ══════════════════════════════════════════════════════════════════════════════
# LECTURA GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
def sheet_id_from_url(url):
    m=re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)",url)
    return m.group(1) if m else ""

def leer_sheet(sid):
    for pestana in ["REPORTE DE IMPUESTOS","Sheet1",""]:
        try:
            p=pestana.replace(" ","%20")
            url=f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={p}"
            resp=requests.get(url,timeout=10)
            if resp.status_code==200 and len(resp.text)>100:
                df=pd.read_csv(StringIO(resp.text),header=None,dtype=str)
                if len(df)>5: return df
        except: pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
# PARSEO REPORTE DE IMPUESTOS
# ══════════════════════════════════════════════════════════════════════════════
SECCION_MAP=[
    (r"SALDO IGV|^IGV\b","1011","A"),
    (r"IMPUESTO A LA RENTA|RENTA.*MYPE|RENTA.*RER|RENTA.*GENE","3121","B"),
    (r"RENTA.*4TA|CUARTA","3042","B"),
    (r"RENTA.*5TA|QUINTA","3052","B"),
    (r"RENTA.*2DA|SEGUNDA","3022","B"),
    (r"\bESSALUD\b","5210","C"),
    (r"\bONP\b","5310","C"),
    (r"\bITAN\b","3038","B"),
    (r"FRACCIONAMIENTO|FRACC.*ART","8021","F"),
]

HDRS={
    "MESES","PERIODO","SE PAGÓ","SE PAGO","PENDIENTE DE PAGO",
    "IMPORTE PAGADO","N° DE CUOTAS","AMORTIZA","VENCIM.",
    "TOTALES","TOTAL","INTERÉS","INTERES","SALDO",
}

def det_seccion(txt):
    t=txt.upper().strip()
    am=re.search(r"\b(20[23]\d)\b",t)
    anio=int(am.group(1)) if am else 2026
    for pat,cod,tp in SECCION_MAP:
        if re.search(pat,t): return cod,anio,tp
    return None,None,None

def es_header(vals):
    txt=" ".join(str(v).upper().strip() for v in vals if v and str(v) not in ["nan",""])
    first=vals[0].strip().upper() if vals and vals[0] else ""
    if first in ["IA"] or (first.isdigit() and 1<=int(first)<=99): return False
    return any(h in txt for h in HDRS)

def pend_fila(vals):
    for i in range(len(vals)-1,-1,-1):
        c=str(vals[i]).strip()
        if not c or c in ["nan","","FRACCIONADO","-"]: continue
        if es_pago(c): continue
        v=num(c)
        if v>=0: return v
    return 0.0

def parsear_reporte(df):
    registros=[]; vistos=set()
    sec_cod=sec_anio=sec_tipo=None

    for _,row in df.iterrows():
        vals=[str(v).strip() if pd.notna(v) and str(v) not in ["nan",""] else "" for v in row]
        texto=" ".join(v for v in vals if v)
        if not texto: continue

        cod_d,anio_d,tipo_d=det_seccion(texto)
        if cod_d:
            sec_cod,sec_anio,sec_tipo=cod_d,anio_d,tipo_d
            continue
        if not sec_cod: continue
        if es_header(vals): continue

        v=vals[1:] if vals and vals[0]=="" else vals
        if not v or not v[0]: continue

        # Fraccionamiento
        if sec_tipo=="F":
            cid=v[0].strip().upper()
            if not (cid=="IA" or (cid.isdigit() and 1<=int(cid)<=99)): continue
            total=num(v[4]) if len(v)>4 else 0
            pago_s=v[5].strip() if len(v)>5 else ""
            vcto_s=v[1].strip() if len(v)>1 else ""
            pagada=es_pago(pago_s) and num(pago_s)>0
            pago_monto=num(pago_s) if pagada else 0
            vcto=None
            if re.match(r"\d{1,2}/\d{2}/\d{4}",vcto_s):
                try: vcto=datetime.strptime(vcto_s,"%d/%m/%Y").date()
                except: pass
            ck=("8021",cid,sec_anio)
            if ck in vistos: continue
            vistos.add(ck)
            registros.append({
                "tipo":"F","codigo":"8021","nombre":TRIBUTO["8021"],
                "mes_nom":f"CUOTA {cid}","mes_num":0 if cid=="IA" else int(cid),
                "anio":sec_anio,"declarado":total,
                "pendiente":0.0 if pagada else total,
                "pagado_reg":pago_monto,"pagada":pagada,
                "vcto_sheet":vcto,"igv_justo":None,
            })
            continue

        # Mes normal
        mes_d=None
        for cel in v[:3]:
            cu=cel.upper().strip()
            for mn,mv in MESES.items():
                if cu==mn or cu.startswith(mn+" "): mes_d=(mn,mv); break
            if mes_d: break
        if not mes_d: continue

        mn,mv=mes_d
        ck=(sec_cod,mn,sec_anio)
        if ck in vistos: continue

        pend=pend_fila(v)
        decl=0.0
        for c in v[1:5]:
            if c and not es_pago(c) and c not in ["FRACCIONADO","-"]:
                vv=num(c)
                if vv>0: decl=vv; break
        if decl==0: decl=pend

        igv_j=None
        if sec_tipo=="A" and len(v)>2:
            c=v[2].strip()
            if re.match(r"\d{1,2}/\d{2}/\d{4}$",c):
                try: igv_j=datetime.strptime(c,"%d/%m/%Y").date()
                except: pass

        vistos.add(ck)
        registros.append({
            "tipo":sec_tipo,"codigo":sec_cod,"nombre":TRIBUTO.get(sec_cod,""),
            "mes_nom":mn,"mes_num":mv,"anio":sec_anio,
            "declarado":decl,"pendiente":pend,
            "pagado_reg":decl-pend if decl>pend else 0,
            "pagada":pend==0 and decl>0,
            "vcto_sheet":None,"igv_justo":igv_j,
        })
    return registros

def pdf_a_df(pdf_bytes):
    filas=[]
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if not table: continue
                    for row in table:
                        vals=[str(v or "").strip().replace("\n"," ") for v in row]
                        if any(v for v in vals): filas.append(vals)
    except Exception as e:
        st.error(f"Error leyendo PDF reporte: {e}")
    if not filas: return pd.DataFrame()
    mc=max(len(r) for r in filas)
    return pd.DataFrame([r+[""]*(mc-len(r)) for r in filas])

# ══════════════════════════════════════════════════════════════════════════════
# PDF SUNAT
# ══════════════════════════════════════════════════════════════════════════════
def parsear_sunat(pdf_bytes):
    filas=[]
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if not table or len(table)<2: continue
                    h=[str(c or "").lower().replace("\n"," ") for c in table[0]]
                    if not any("período" in x or "periodo" in x for x in h): continue
                    if not any("tributo" in x for x in h): continue
                    for row in table[1:]:
                        if not row or len(row)<8: continue
                        v=[str(x or "").strip().replace("\n"," ") for x in row]
                        per,ord_,fstr,cod,mstr=v[0],v[2],v[3],v[5],v[7]
                        if not re.match(r"^202[3-9]\d{2}$",per): continue
                        if cod not in TRIBUTO: continue
                        imp=num(mstr)
                        if imp<=0: continue
                        fp=None
                        if re.match(r"\d{1,2}/\d{2}/\d{4}",fstr):
                            try: fp=datetime.strptime(fstr.strip(),"%d/%m/%Y").date()
                            except: pass
                        filas.append({"PERIODO":per,"N_ORDEN":ord_,"COD":cod,"FECHA":fp,"IMPORTE":imp})
    except Exception as e:
        st.error(f"Error leyendo PDF SUNAT: {e}")
        return pd.DataFrame()
    if not filas: return pd.DataFrame()
    df=pd.DataFrame(filas).drop_duplicates(subset=["N_ORDEN"],keep="first")
    return df.reset_index(drop=True)

def combinar_sunat(archivos):
    dfs,nombres=[],[]
    for arch in archivos:
        arch.seek(0); df=parsear_sunat(arch.read())
        if not df.empty:
            df["_arch"]=arch.name; dfs.append(df); nombres.append(arch.name)
        else: st.warning(f"⚠️ Sin pagos en: **{arch.name}**")
    if not dfs: return pd.DataFrame(),nombres
    combinado=pd.concat(dfs,ignore_index=True)
    antes=len(combinado)
    combinado=combinado.drop_duplicates(subset=["N_ORDEN"],keep="first")
    dup=antes-len(combinado)
    if dup>0: st.info(f"ℹ️ {dup} pagos duplicados eliminados.")
    return combinado.reset_index(drop=True),nombres

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS CENTRAL
# ══════════════════════════════════════════════════════════════════════════════
def analizar(extracto, reporte, digito, igv_justo, hoy):
    actualizar=[]   # pago en SUNAT no registrado en reporte
    vencidos=[]     # declarado, no pagado, vencido
    con_atraso=[]   # registrado pero pagado tarde
    al_dia=[]       # correcto
    vistos=set()

    for _,fila in extracto.iterrows():
        per=str(fila["PERIODO"]).strip()
        if not re.match(r"^202[3-9]\d{2}$",per): continue
        anio,mes=int(per[:4]),int(per[4:6])
        cod=str(fila["COD"]).strip()
        if cod not in TRIBUTO: continue
        imp=float(fila["IMPORTE"])
        if imp<=0: continue
        nord=str(fila["N_ORDEN"]).strip()
        fp=fila["FECHA"]
        fecha_pago=fp if isinstance(fp,date) else None
        mes_nom=MES_NOM.get(mes,str(mes))

        # Fecha vencimiento
        if cod=="1011" and igv_justo:
            fij=next((r["igv_justo"] for r in reporte
                     if r["codigo"]=="1011" and r["mes_num"]==mes
                     and r["anio"]==anio and r["igv_justo"]),None)
            fv=fij or fecha_venc_igv_justo(anio,mes,digito)
            tv="IGV Justo"
        elif cod=="8021":
            # Usar vencimiento real de la cuota desde el reporte
            fv=next((r["vcto_sheet"] for r in reporte
                    if r["codigo"]=="8021" and r["anio"]==anio
                    and abs(r["declarado"]-imp)<1.0),None)
            tv="Fracc"
        else:
            fv=fecha_venc(anio,mes,digito)
            tv="Normal"

        # ¿Registrado?
        if cod=="8021":
            ya_reg=any(r["codigo"]=="8021" and r["anio"]==anio
                      and r.get("pagada") and abs(r.get("pagado_reg",0)-imp)<1.0
                      for r in reporte)
        else:
            ya_reg=any(r["codigo"]==cod and r["mes_num"]==mes and r["anio"]==anio
                      for r in reporte)

        dt=max((fecha_pago-fv).days,0) if fecha_pago and fv else 0
        tarde=dt>0
        tim_v=calc_tim(imp,dt) if tarde else 0.0
        mul_v=calc_multa(anio) if (tarde and cod in CON_MULTA) else 0.0

        base={"codigo":cod,"nombre":TRIBUTO[cod],
              "periodo":f"{mes_nom}-{anio}" if cod!="8021" else f"S/{imp:.0f}",
              "mes":mes_nom,"mes_num":mes,"anio":anio,
              "importe":imp,"fecha_pago":fecha_pago,
              "fecha_venc":fv,"tipo_venc":tv,
              "dias_tarde":dt,"tarde":tarde,
              "tim":tim_v,"multa":mul_v,"tiene_multa":cod in CON_MULTA,
              "n_orden":nord,"ya_reg":ya_reg}

        vistos.add((cod,mes_nom,anio))

        if not ya_reg:
            pest={"1011":f"IGV {anio}","5210":"ESSALUD","5310":"ONP",
                  "3052":"RENTA_5TA","3042":"RENTA_4TA","3038":"ITAN",
                  "8021":"FRACCIONAMIENTOS"}.get(cod,f"RENTA {anio}")
            fp_s=fecha_pago.strftime("%d/%m/%Y") if fecha_pago else ""
            instr=(f"Pestaña \"{pest}\" → {mes_nom} → SE PAGÓ = S/ {imp:,.2f} · Fecha: {fp_s}"
                  if cod!="8021" else f"Tabla Fraccionamientos → registrar S/ {imp:,.2f} pagado {fp_s}")
            actualizar.append({**base,"instruccion":instr})
        elif tarde and (tim_v>0 or mul_v>0):
            con_atraso.append(base)
        else:
            al_dia.append(base)

    # Vencidos del reporte
    for r in reporte:
        cod=r["codigo"]; mn=r["mes_nom"]; mv=r["mes_num"]; anio=r["anio"]
        saldo=r["pendiente"]
        if saldo<=0: continue

        if cod=="8021":
            # Cuotas fracc vencidas sin pagar
            if r.get("pagada"): continue
            fv=r.get("vcto_sheet")
            if not fv or fv>=hoy: continue
            dv=(hoy-fv).days
            # No duplicar con extracto SUNAT
            ya_en_ext=any(str(f["COD"])=="8021" and f["ANIO"]==anio and abs(f["IMPORTE"]-r["declarado"])<1.0
                         for _,f in extracto.rename(columns={"COD":"COD","IMPORTE":"IMPORTE"}).iterrows()
                         ) if not extracto.empty else False
            if ya_en_ext: continue
            vencidos.append({
                "codigo":"8021","nombre":TRIBUTO["8021"],
                "periodo":f"{mn}-{anio}","mes":mn,"mes_num":mv,"anio":anio,
                "importe":r["declarado"],"fecha_pago":None,
                "fecha_venc":fv,"tipo_venc":"Fracc",
                "dias_tarde":dv,"tarde":True,
                "tim":calc_tim(r["declarado"],dv),"multa":0,
                "tiene_multa":False,"n_orden":"","ya_reg":True,
                "instruccion":f"{mn} S/{r['declarado']:,.2f} — venció {fv.strftime('%d/%m/%Y')} — {dv}d",
            })
            continue

        if (cod,mn,anio) in vistos: continue

        if cod=="1011" and igv_justo and r["igv_justo"]:
            fv=r["igv_justo"]; tv="IGV Justo"
        elif cod=="1011" and igv_justo:
            fv=fecha_venc_igv_justo(anio,mv,digito); tv="IGV Justo"
        else:
            fv=fecha_venc(anio,mv,digito); tv="Normal"

        if fv>=hoy: continue
        dv=(hoy-fv).days
        tim_v=calc_tim(saldo,dv)
        mul_v=calc_multa(anio) if cod in CON_MULTA else 0.0

        vencidos.append({
            "codigo":cod,"nombre":TRIBUTO.get(cod,""),
            "periodo":f"{mn}-{anio}","mes":mn,"mes_num":mv,"anio":anio,
            "importe":saldo,"fecha_pago":None,"fecha_venc":fv,"tipo_venc":tv,
            "dias_tarde":dv,"tarde":True,"tim":tim_v,"multa":mul_v,
            "tiene_multa":cod in CON_MULTA,"n_orden":"","ya_reg":True,
            "instruccion":f"Declarado S/{r['declarado']:,.2f} — sin pagar — {dv} días vencido",
        })

    return {
        "actualizar": actualizar,
        "vencidos":   sorted(vencidos,  key=lambda x:x["dias_tarde"],reverse=True),
        "con_atraso": sorted(con_atraso,key=lambda x:x["dias_tarde"],reverse=True),
        "al_dia":     al_dia,
    }

# ══════════════════════════════════════════════════════════════════════════════
# EXCEL
# ══════════════════════════════════════════════════════════════════════════════
def gen_excel(empresa,ruc,res,extracto,nombres,fuente):
    buf=BytesIO()
    act=res["actualizar"]; ven=res["vencidos"]
    mul=res["con_atraso"]; ok=res["al_dia"]
    t_mul=sum(r["multa"]+r["tim"] for r in act+ven+mul)

    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        hoy_s=datetime.now().strftime("%d/%m/%Y %H:%M")
        anios=sorted({r["anio"] for r in act+ven+mul+ok})
        pd.DataFrame({"Campo":[
            "Empresa","RUC","Fecha análisis","PDF SUNAT","Fuente reporte",
            "Años analizados","Pagos en extracto","Falta actualizar",
            "Vencidos sin pagar","Pagados con atraso","Al día","Multas+TIM S/",
        ],"Valor":[
            empresa,ruc,hoy_s,", ".join(nombres),fuente,
            ", ".join(str(a) for a in anios),len(extracto),
            len(act),len(ven),len(mul),len(ok),f"{t_mul:,.2f}",
        ]}).to_excel(w,sheet_name="RESUMEN",index=False)

        def rows(lst,extra):
            out=[]
            for r in lst:
                d={"Año":r["anio"],"Tributo":r["nombre"],"Período":r["periodo"],
                   "Importe S/":r["importe"],
                   "Fecha pago":r["fecha_pago"].strftime("%d/%m/%Y") if r.get("fecha_pago") else "",
                   "N° Orden":r.get("n_orden","")}
                for k in extra:
                    if k=="Vencimiento": d[k]=r["fecha_venc"].strftime("%d/%m/%Y") if r.get("fecha_venc") else ""
                    elif k=="Días": d[k]=r["dias_tarde"]
                    elif k=="TIM S/": d[k]=r["tim"]
                    elif k=="Multa S/": d[k]=r["multa"] if r["multa"] else "No aplica"
                    elif k=="Total S/": d[k]=r["importe"]+r["tim"]+r["multa"]
                    elif k=="Instrucción": d[k]=r.get("instruccion","")
                    elif k=="Tipo venc.": d[k]=r["tipo_venc"]
                out.append(d)
            return out

        if act: pd.DataFrame(rows(act,["Instrucción","Días","TIM S/","Multa S/"])).to_excel(w,sheet_name="🟡 ACTUALIZAR REPORTE",index=False)
        if ven: pd.DataFrame(rows(ven,["Vencimiento","Días","TIM S/","Multa S/","Total S/","Instrucción"])).to_excel(w,sheet_name="🔴 VENCIDOS SIN PAGAR",index=False)
        if mul: pd.DataFrame(rows(mul,["Vencimiento","Días","TIM S/","Multa S/","Tipo venc."])).to_excel(w,sheet_name="🟠 PAGADOS CON ATRASO",index=False)
        if ok:  pd.DataFrame(rows(ok, ["Vencimiento","Tipo venc."])).to_excel(w,sheet_name="✅ AL DÍA",index=False)
        extracto.to_excel(w,sheet_name="EXTRACTO SUNAT",index=False)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
  <h1>📊 Contadeus — Revisor Tributario</h1>
  <p>Cruza extracto SUNAT con reporte de impuestos · Actualizar · Vencidos · Multas</p>
</div>
""", unsafe_allow_html=True)

SK=["listo","resultado","empresa","ruc","extracto_df","nombres_sunat","fuente"]
for k in SK:
    if k not in st.session_state:
        st.session_state[k]=(False if k=="listo" else [] if k=="nombres_sunat" else
                             pd.DataFrame() if k=="extracto_df" else
                             {} if k=="resultado" else "")

HOY=date.today()

# ── RESULTADOS ──────────────────────────────────────────────────────────────
if st.session_state.listo and st.session_state.resultado:
    res=st.session_state.resultado
    act=res["actualizar"]; ven=res["vencidos"]
    mul=res["con_atraso"]; ok=res["al_dia"]
    empresa=st.session_state.empresa; ruc=st.session_state.ruc
    t_mul=sum(r["multa"]+r["tim"] for r in act+ven+mul)
    anios=sorted({r["anio"] for r in act+ven+mul+ok},reverse=True)

    st.markdown(f'<div class="emp">🏢 {empresa}{f" · RUC {ruc}" if ruc else ""} · Años: {" · ".join(str(a) for a in anios)}</div>',unsafe_allow_html=True)

    for col,(n,lbl,color) in zip(st.columns(5),[
        (len(act),"Falta actualizar","amb"),(len(ven),"Vencidos sin pagar","red"),
        (len(mul),"Pagados con atraso","amb"),(len(ok),"Al día","grn"),
        (f"S/ {t_mul:,.0f}","Multas + TIM","red")]):
        with col:
            st.markdown(f'<div class="kpi"><div class="n {color}">{n}</div><div class="l">{lbl}</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="sep"></div>',unsafe_allow_html=True)

    # A) FALTA ACTUALIZAR
    if act:
        st.markdown('<div class="stitle">🟡 FALTA ACTUALIZAR EL REPORTE DE IMPUESTOS</div>',unsafe_allow_html=True)
        st.markdown('<div class="card card-a">Estos pagos están en el extracto SUNAT pero <strong>no están registrados</strong> en el reporte del cliente.</div>',unsafe_allow_html=True)
        for anio in anios:
            items=[r for r in act if r["anio"]==anio]
            if not items: continue
            st.markdown(f'<div class="yr">📅 {anio}</div>',unsafe_allow_html=True)
            for r in items:
                atr=""
                if r["tarde"]:
                    tipo_m=f'⚠️ Multa S/ {r["multa"]:,.0f}' if r["multa"] else "Solo TIM"
                    atr=(f'<br><span class="badge badge-r">{tipo_m}</span>'
                        f'<span class="badge badge-a">TIM S/ {r["tim"]:,.2f}</span>'
                        f' — {r["dias_tarde"]} días tarde')
                fp_s=r["fecha_pago"].strftime("%d/%m/%Y") if r["fecha_pago"] else "N/D"
                st.markdown(f"""<div class="card card-a">
                    <strong>📌 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp; Pagado: <strong>{fp_s}</strong>
                    &nbsp;·&nbsp; N° {r['n_orden']}{atr}<br>
                    <span style="color:#92400E;">▶ {r.get('instruccion','')}</span>
                </div>""",unsafe_allow_html=True)

    # B) VENCIDOS
    if ven:
        st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
        st.markdown('<div class="stitle">🔴 IMPUESTOS VENCIDOS SIN PAGAR</div>',unsafe_allow_html=True)
        st.markdown('<div class="card card-r">Declarados en el reporte pero <strong>sin pagar</strong>. SUNAT puede cobrar coactivamente.</div>',unsafe_allow_html=True)
        for anio in anios:
            items=[r for r in ven if r["anio"]==anio]
            if not items: continue
            st.markdown(f'<div class="yr">📅 {anio}</div>',unsafe_allow_html=True)
            for r in items:
                costo=r["importe"]+r["tim"]+r["multa"]
                mt=(f'<span class="badge badge-r">Multa S/ {r["multa"]:,.0f}</span>' if r["multa"] else "")
                vs=r["fecha_venc"].strftime("%d/%m/%Y") if r.get("fecha_venc") else "N/D"
                st.markdown(f"""<div class="card card-r">
                    <strong>🚨 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp; Venció: <strong>{vs}</strong>
                    &nbsp;·&nbsp; <strong>{r['dias_tarde']} días vencido</strong><br>
                    {mt}<span class="badge badge-a">TIM S/ {r['tim']:,.2f}</span>
                    <span class="badge badge-r">Total regularizar: S/ {costo:,.2f}</span>
                </div>""",unsafe_allow_html=True)

    # C) CON ATRASO
    if mul:
        st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
        with st.expander(f"🟠 {len(mul)} pagados con atraso — multas y TIM generados"):
            for anio in anios:
                items=[r for r in mul if r["anio"]==anio]
                if not items: continue
                st.markdown(f'<div class="yr">📅 {anio}</div>',unsafe_allow_html=True)
                for r in items:
                    ml=f'⚠️ Multa S/ {r["multa"]:,.0f}' if r["multa"] else "Solo TIM"
                    vs=r["fecha_venc"].strftime("%d/%m/%Y") if r.get("fecha_venc") else ""
                    fp_s=r["fecha_pago"].strftime("%d/%m/%Y") if r.get("fecha_pago") else ""
                    st.markdown(f"""<div class="card card-o">
                        <strong>{r['nombre']} — {r['periodo']}</strong>
                        &nbsp;·&nbsp; S/ {r['importe']:,.2f}
                        &nbsp;·&nbsp; Pagado: {fp_s} &nbsp;·&nbsp; Vencía: {vs}
                        &nbsp;·&nbsp; {r['dias_tarde']}d tarde &nbsp;·&nbsp; {ml}
                        &nbsp;·&nbsp; TIM S/ {r['tim']:,.2f} &nbsp;·&nbsp; ({r['tipo_venc']})
                    </div>""",unsafe_allow_html=True)

    # D) AL DÍA
    if ok:
        with st.expander(f"✅ {len(ok)} pagos al día"):
            for r in ok:
                fp_s=r["fecha_pago"].strftime("%d/%m/%Y") if r.get("fecha_pago") else ""
                st.markdown(f'<div class="card card-g">✓ {r["nombre"]} — {r["periodo"]} — S/ {r["importe"]:,.2f} — {fp_s}</div>',unsafe_allow_html=True)

    if not act and not ven and not mul:
        st.markdown('<div class="card card-g">✅ <strong>Todo al día. No hay pendientes.</strong></div>',unsafe_allow_html=True)

    st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
    col_dl,col_nx=st.columns(2)
    with col_dl:
        eb=gen_excel(empresa,ruc,res,st.session_state.extracto_df,
                     st.session_state.nombres_sunat,st.session_state.fuente)
        n=empresa[:20].replace(" ","_") if empresa else ruc
        st.download_button("⬇️  Descargar reporte Excel",data=eb,
                          file_name=f"Contadeus_{n}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          use_container_width=True,type="primary")
    with col_nx:
        if st.button("➡️  Analizar otra empresa",use_container_width=True):
            for k in SK:
                st.session_state[k]=(False if k=="listo" else [] if k=="nombres_sunat" else
                                     pd.DataFrame() if k=="extracto_df" else
                                     {} if k=="resultado" else "")
            st.rerun()
    st.markdown('<div class="card card-b">💡 <strong>Descarga el Excel antes de analizar otra empresa.</strong></div>',unsafe_allow_html=True)

# ── FORMULARIO ──────────────────────────────────────────────────────────────
else:
    col_f,col_h=st.columns([3,2])
    with col_f:
        st.markdown("### 🏢 Datos de la empresa")
        ruc_inp=st.text_input("RUC (11 dígitos)",placeholder="20613979779")
        digito_calc=None
        if ruc_inp and len(ruc_inp.strip())==11 and ruc_inp.strip().isdigit():
            digito_calc=int(ruc_inp.strip()[-1])
            st.markdown(f'<div class="card card-b" style="font-size:.82rem;padding:7px 12px;">✓ Dígito RUC: <strong>{digito_calc}</strong> — cronograma SUNAT calculado</div>',unsafe_allow_html=True)
        elif ruc_inp: st.warning("El RUC debe tener 11 dígitos.")

        empresa_inp=st.text_input("Nombre (opcional)",placeholder="TDD INVERSIONES S.A.C.")
        igv_chk=st.checkbox("✅ Acogida a IGV Justo (Ley 30524)",value=True)

        st.markdown("")
        st.markdown("### 📄 PDF 1 — Extracto SUNAT")
        st.caption("SUNAT SOL → Mis declaraciones y pagos → Reporte electrónico → PDF. Puedes subir varios años.")
        arch_sunat=st.file_uploader("",type=["pdf"],accept_multiple_files=True,label_visibility="collapsed",key="up_sunat")
        if arch_sunat:
            st.markdown(f'<div class="card card-g" style="font-size:.82rem;padding:7px 12px;">📄 {len(arch_sunat)} PDF(s): {" · ".join(a.name for a in arch_sunat)}</div>',unsafe_allow_html=True)

        st.markdown("")
        st.markdown("### 📊 Reporte de Impuestos del cliente")
        tab_s,tab_p=st.tabs(["🔗 Link del Google Sheet","📁 PDF exportado"])
        with tab_s:
            sheet_url=st.text_input("",placeholder="https://docs.google.com/spreadsheets/d/...",
                                   label_visibility="collapsed")
        with tab_p:
            arch_rep=st.file_uploader("",type=["pdf"],accept_multiple_files=False,
                                     label_visibility="collapsed",key="up_rep")
            if arch_rep:
                st.markdown(f'<div class="card card-g" style="font-size:.82rem;padding:7px 12px;">📊 {arch_rep.name}</div>',unsafe_allow_html=True)

        st.markdown("")
        if st.button("🔍  Analizar",type="primary",use_container_width=True):
            err=[]
            if not ruc_inp.strip() or len(ruc_inp.strip())!=11: err.append("RUC inválido.")
            if not arch_sunat: err.append("Sube el PDF de SUNAT.")
            if not sheet_url.strip() and not arch_rep: err.append("Proporciona el link del Sheet o el PDF del reporte.")
            for e in err: st.error(e)

            if not err and digito_calc is not None:
                empresa_final=empresa_inp.strip() or ruc_inp.strip()
                rep_df=None; fuente=""

                if sheet_url.strip():
                    sid=sheet_id_from_url(sheet_url)
                    if not sid: st.error("Link inválido."); st.stop()
                    with st.spinner("Leyendo Google Sheet..."):
                        rep_df=leer_sheet(sid); fuente=f"Sheet: ...{sheet_url[-30:]}"
                    if rep_df is None: st.error("No se pudo leer el Sheet. Verifica que esté compartido."); st.stop()
                elif arch_rep:
                    with st.spinner("Leyendo PDF reporte..."):
                        arch_rep.seek(0); rep_df=pdf_a_df(arch_rep.read()); fuente=arch_rep.name
                    if rep_df is None or rep_df.empty: st.error("No se pudo leer el PDF."); st.stop()

                with st.spinner(f"Procesando {len(arch_sunat)} PDF(s) SUNAT..."):
                    ext_df,nombres=combinar_sunat(arch_sunat)
                    if ext_df.empty: st.error("Sin pagos en el PDF SUNAT."); st.stop()

                with st.spinner("Analizando..."):
                    rep_parsed=parsear_reporte(rep_df)
                    resultado=analizar(ext_df,rep_parsed,digito_calc,igv_chk,HOY)

                if sum(len(v) for v in resultado.values())==0:
                    st.info("Sin registros para analizar.")
                else:
                    st.session_state.update({"listo":True,"resultado":resultado,
                        "empresa":empresa_final,"ruc":ruc_inp.strip(),
                        "extracto_df":ext_df,"nombres_sunat":nombres,"fuente":fuente})
                    st.rerun()

    with col_h:
        st.markdown("""<div class="card card-b" style="margin-top:8px;">
            <strong>📋 Qué hace esta app</strong><br><br>
            🟡 <strong>Actualizar</strong> — pagos en SUNAT no registrados en tu reporte<br><br>
            🔴 <strong>Vencidos</strong> — declarados pero sin pagar, SUNAT puede cobrar coactivamente<br><br>
            🟠 <strong>Con multa</strong> — pagados tarde (ONP/R5ta/R4ta/R2da = multa 5% UIT)<br><br>
            ✅ <strong>Al día</strong> — todo correcto
        </div>""",unsafe_allow_html=True)
        st.markdown("""<div class="card card-r" style="margin-top:10px;">
            <strong>⚠️ Tributos con multa 5% UIT</strong><br>
            ONP · Renta 5ta · Renta 4ta · Renta 2da<br>
            UIT 2024=S/5,150 · 2025=S/5,350 · 2026=S/5,500
        </div>""",unsafe_allow_html=True)
        st.markdown("""<div class="card card-g" style="margin-top:10px;">
            <strong>🔒 La app nunca modifica ningún archivo</strong><br>
            Solo lee y compara. Tú decides qué actualizar.
        </div>""",unsafe_allow_html=True)
