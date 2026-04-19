"""
relatorio.py
Gerador de relatório executivo em PDF para o dashboard de parcerias.
Usa fpdf2. Retorna bytes para download direto no Streamlit.
"""

import io
from datetime import datetime
from fpdf import FPDF

# ── CONSTANTES ────────────────────────────────────────────────
GP_TETO = 195.30
TP_TETO = 208.09
GP_VALOR_UNIT = 16.27
TP_VALOR_UNIT = 16.01


# ── CLASSE PDF ────────────────────────────────────────────────
class _PDF(FPDF):

    def __init__(self, nome_academia, mes_ref):
        super().__init__()
        self.nome_academia = nome_academia
        self.mes_ref = mes_ref

    def header(self):
        self.set_fill_color(30, 30, 30)
        self.rect(0, 0, 210, 24, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 5)
        self.cell(0, 8, f"Relatorio de Parcerias  -  {self.mes_ref}")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 180, 180)
        self.set_xy(10, 14)
        self.cell(
            0, 6, f"{self.nome_academia}  .  Gympass & Totalpass  .  Frequencia e repasse")
        self.ln(20)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0, 10,
            f"Gerado em {datetime.now().strftime('%d/%m/%Y as %H:%M')}  .  "
            "Matheus Souza - Consultoria de Dados  .  github.com/souzamatt01",
            align="C",
        )


# ── HELPERS VISUAIS ───────────────────────────────────────────
def _kpi_box(pdf, x, y, w, h, label, value, bg_rgb):
    pdf.set_fill_color(*bg_rgb)
    pdf.rect(x, y, w, h, "F")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(190, 190, 190)
    pdf.set_xy(x + 3, y + 2.5)
    pdf.cell(w - 6, 5, label)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(x + 3, y + 8)
    pdf.cell(w - 6, 9, value)


def _secao(pdf, titulo):
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 7, titulo)
    pdf.ln(1)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)


def _cabecalho_tabela(pdf, headers, col_widths):
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_x(10)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 7, h, fill=True)
    pdf.ln()


def _safe(text: str) -> str:
    """Normaliza texto para latin-1 (compativel com Helvetica no fpdf2)."""
    return (
        str(text)
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


def _linha_tabela(pdf, valores, col_widths, bg_rgb=(245, 245, 245)):
    pdf.set_fill_color(*bg_rgb)
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_x(10)
    for v, w in zip(valores, col_widths):
        pdf.cell(w, 7, _safe(v), fill=True)
    pdf.ln()


def _caixa_destaque(pdf, texto_titulo, texto_corpo, bg_rgb, titulo_rgb):
    y = pdf.get_y()
    pdf.set_fill_color(*bg_rgb)
    pdf.rect(10, y, 190, 26, "F")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*titulo_rgb)
    pdf.set_xy(13, y + 3)
    pdf.cell(0, 5, texto_titulo)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(30, 30, 30)
    pdf.set_xy(13, y + 10)
    pdf.multi_cell(184, 5, texto_corpo)
    pdf.set_y(y + 28)


# ── FUNÇÃO PRINCIPAL ──────────────────────────────────────────
def gerar_pdf(all_visits, nome_academia="Academia", mes_ref="Marco 2026") -> bytes:

    # ── MÉTRICAS GERAIS ───────────────────────────────────────
    total_clientes = all_visits["Cliente"].nunique()
    total_checkins = int(all_visits["Visitas"].sum())
    repasse_bruto = round(all_visits["Repasse_Realizado"].sum(), 2)
    repasse_liquido = round(repasse_bruto * 0.90, 2)
    repasse_perdido = round(all_visits["Repasse_Perdido"].sum(), 2)
    teto_atingido = int((all_visits["Visitas"] >= 13).sum())
    media_visitas = round(all_visits["Visitas"].mean(), 1)

    gp_df = all_visits[all_visits["Plataforma"] == "Gympass"]
    tp_df = all_visits[all_visits["Plataforma"] == "Totalpass"]

    gp_clientes = len(gp_df)
    tp_clientes = len(tp_df)
    gp_realizado = round(gp_df["Repasse_Realizado"].sum(), 2)
    tp_realizado = round(tp_df["Repasse_Realizado"].sum(), 2)
    gp_perdido = round(gp_df["Repasse_Perdido"].sum(), 2)
    tp_perdido = round(tp_df["Repasse_Perdido"].sum(), 2)
    gp_liquido = round(gp_realizado * 0.90, 2)
    tp_liquido = round(tp_realizado * 0.90, 2)
    gp_teto = int((gp_df["Visitas"] >= 13).sum())
    tp_teto = int((tp_df["Visitas"] >= 13).sum())
    gp_pot = gp_clientes * GP_TETO
    tp_pot = tp_clientes * TP_TETO

    _intermediarios = all_visits[
        all_visits["Cluster"].isin(
            ["Intermediário (7–12)", "Intermediario (7-12)"])
    ].copy()
    total_inter = len(_intermediarios)
    media_visitas_int = round(
        _intermediarios["Visitas"].mean(), 1) if total_inter > 0 else 0

    _baixo = all_visits[all_visits["Cluster"].isin(
        ["Baixo (1–6)", "Baixo (1-6)"])]
    n_baixo = len(_baixo)
    perd_baixo = round(_baixo["Repasse_Perdido"].sum(), 2)

    cenarios = []
    for label, pct in [
        ("Conservador (25%)", 0.25),
        ("Moderado (50%)",    0.50),
        ("Otimista (75%)",    0.75),
        ("Maximo (100%)",     1.00),
    ]:
        n = max(1, round(total_inter * pct))
        top = _intermediarios.sort_values(
            "Repasse_Perdido", ascending=False).head(n)
        ganho = round(top["Repasse_Perdido"].sum() * 0.90, 2)
        cenarios.append((label, n, ganho))

    # ── MONTAR PDF ────────────────────────────────────────────
    pdf = _PDF(nome_academia=nome_academia, mes_ref=mes_ref)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=18)

    # KPI CARDS
    kpis = [
        ("Clientes unicos",  str(total_clientes),              (40,  40,  40)),
        ("Check-ins totais", str(total_checkins),              (40,  40,  40)),
        ("Media de visitas", str(media_visitas),               (40,  40,  40)),
        ("Teto atingido",    f"{teto_atingido} clientes",      (40,  40,  40)),
        ("Repasse liquido",
         f"R$ {repasse_liquido/1000:.1f}k", (20,  90,  50)),
        ("Repasse perdido",
         f"R$ {repasse_perdido/1000:.1f}k", (140, 40,  40)),
    ]
    box_w, box_h, gap = 30, 24, 2
    start_x, start_y = 10, pdf.get_y()
    for i, (label, value, color) in enumerate(kpis):
        _kpi_box(pdf, start_x + i * (box_w + gap), start_y,
                 box_w, box_h, label, value, color)
    pdf.set_y(start_y + box_h + 8)

    # REPASSE POR PLATAFORMA
    _secao(pdf, "1. Repasse por Plataforma")
    headers_plat = ["Plataforma", "Clientes", "Teto atingido",
                    "Repasse bruto", "Liquido (-10%)", "Perdido", "Aproveitamento"]
    cols_plat = [35, 22, 30, 33, 30, 28, 32]
    _cabecalho_tabela(pdf, headers_plat, cols_plat)
    linhas_plat = [
        ("Gympass",   gp_clientes, gp_teto,
         f"R$ {gp_realizado:,.2f}", f"R$ {gp_liquido:,.2f}",
         f"R$ {gp_perdido:,.2f}",
         f"{round(gp_realizado/gp_pot*100, 1)}%" if gp_pot > 0 else "-"),
        ("Totalpass", tp_clientes, tp_teto,
         f"R$ {tp_realizado:,.2f}", f"R$ {tp_liquido:,.2f}",
         f"R$ {tp_perdido:,.2f}",
         f"{round(tp_realizado/tp_pot*100, 1)}%" if tp_pot > 0 else "-"),
    ]
    for i, linha in enumerate(linhas_plat):
        _linha_tabela(pdf, linha, cols_plat, (245, 245, 245)
                      if i % 2 == 0 else (237, 237, 237))
    pdf.ln(8)

    # CLUSTERS
    _secao(pdf, "2. Distribuicao por Cluster de Frequencia")
    cluster_summary = (
        all_visits
        .groupby("Cluster")
        .agg(Clientes=("Cliente", "count"),
             Visitas_Total=("Visitas", "sum"),
             Repasse_Real=("Repasse_Realizado", "sum"),
             Repasse_Perd=("Repasse_Perdido", "sum"))
        .reset_index()
    )
    ordem_map = {
        "Baixo (1-6)": 0, "Baixo (1–6)": 0,
        "Intermediario (7-12)": 1, "Intermediário (7–12)": 1,
        "Teto atingido (13+)": 2,
    }
    cluster_summary["_ord"] = cluster_summary["Cluster"].map(
        ordem_map).fillna(9)
    cluster_summary = cluster_summary.sort_values("_ord")
    headers_cl = ["Cluster", "Clientes", "Check-ins",
                  "Repasse realizado", "Repasse perdido"]
    cols_cl = [60, 25, 25, 45, 45]
    _cabecalho_tabela(pdf, headers_cl, cols_cl)
    cor_cluster = {0: (252, 235, 235), 1: (250, 238, 218), 2: (234, 243, 222)}
    for _, row in cluster_summary.iterrows():
        bg = cor_cluster.get(int(row["_ord"]), (245, 245, 245))
        _linha_tabela(pdf, [
            row["Cluster"],
            str(int(row["Clientes"])),
            str(int(row["Visitas_Total"])),
            f"R$ {row['Repasse_Real']:,.2f}",
            f"R$ {row['Repasse_Perd']:,.2f}",
        ], cols_cl, bg)
    pdf.ln(8)

    # HIPÓTESE DE CONVERSÃO
    _secao(pdf, "3. Hipotese de Conversao  -  Intermediario para o Teto")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(10)
    visitas_faltam = round(13 - media_visitas_int,
                           1) if media_visitas_int > 0 else "-"
    pdf.multi_cell(
        190, 5,
        f"O cluster intermediario possui {total_inter} clientes com media de "
        f"{media_visitas_int} visitas/mes. Sao necessarias em media {visitas_faltam} visitas "
        f"adicionais por cliente para atingir o teto de repasse. "
        f"Abaixo, o impacto financeiro projetado por cenario (ja descontada a taxa de 10%):"
    )
    pdf.ln(4)
    headers_cen = ["Cenario", "Clientes convertidos",
                   "Ganho liquido projetado (R$)"]
    cols_cen = [70, 55, 75]
    _cabecalho_tabela(pdf, headers_cen, cols_cen)
    cores_cen = [(240, 150, 150), (240, 200, 120),
                 (120, 180, 230), (150, 210, 120)]
    for i, (label, n, ganho) in enumerate(cenarios):
        _linha_tabela(
            pdf, [label, str(n), f"R$ {ganho:,.2f}"], cols_cen, cores_cen[i])
    pdf.ln(8)

    # ALERTAS
    _secao(pdf, "4. Alertas e Oportunidades")
    if n_baixo > 0:
        _caixa_destaque(
            pdf,
            "ATENCAO  -  Clientes com baixa frequencia",
            f"{n_baixo} clientes do cluster Baixo deixaram de gerar R$ {perd_baixo:,.2f} "
            "em repasse. Acao sugerida: campanha de reativacao ou oferta de upgrade para plano proprio.",
            bg_rgb=(253, 237, 237), titulo_rgb=(140, 40, 40),
        )
    if total_inter > 0 and cenarios:
        _caixa_destaque(
            pdf,
            "OPORTUNIDADE  -  Cenario conservador de conversao",
            f"Priorizar acoes de engajamento para os {cenarios[0][1]} clientes do cenario "
            f"conservador representa um ganho liquido imediato de R$ {cenarios[0][2]:,.2f}/mes "
            f"com minimo esforco operacional. No cenario otimista, o potencial chega a "
            f"R$ {cenarios[2][2]:,.2f}/mes.",
            bg_rgb=(230, 241, 251), titulo_rgb=(20, 70, 130),
        )
    pct_teto = round((gp_teto + tp_teto) / total_clientes *
                     100, 1) if total_clientes > 0 else 0
    if pct_teto >= 15:
        _caixa_destaque(
            pdf,
            "OPORTUNIDADE  -  Alta fidelidade",
            f"{pct_teto}% dos clientes atingiram o teto de visitas. "
            "Alta frequencia indica potencial de conversao para plano direto com maior margem.",
            bg_rgb=(234, 243, 222), titulo_rgb=(40, 100, 20),
        )

    # TOP 10 CLIENTES
    pdf.add_page()
    _secao(pdf, "5. Top 10 Clientes por Frequencia")
    top10 = (
        all_visits
        .sort_values("Visitas", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    headers_top = ["#", "Cliente", "Plataforma", "Visitas",
                   "Cluster", "Repasse realizado", "Repasse perdido"]
    cols_top = [10, 45, 25, 18, 38, 35, 35]
    _cabecalho_tabela(pdf, headers_top, cols_top)
    for i, row in top10.iterrows():
        _linha_tabela(pdf, [
            str(i + 1),
            row["Cliente"],
            row["Plataforma"],
            str(int(row["Visitas"])),
            row["Cluster"],
            f"R$ {row['Repasse_Realizado']:,.2f}",
            f"R$ {row['Repasse_Perdido']:,.2f}",
        ], cols_top, (245, 245, 245) if i % 2 == 0 else (237, 237, 237))

    # ── RETORNAR BYTES ────────────────────────────────────────
    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
