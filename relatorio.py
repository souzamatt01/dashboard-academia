import pandas as pd
from fpdf import FPDF
from datetime import datetime

# ── CONSTANTES ────────────────────────────────────────────────
GP_TETO = 195.30
TP_TETO = 208.09

# ── LOAD DATA ─────────────────────────────────────────────────


def load_data():
    gp_raw = pd.read_excel("data/Gympass_anonimizado.xlsx", header=0)
    gp_raw.columns = ["Data", "Hora", "ID_Unidade", "Unidade", "Visitante",
                      "ID_Wellhub", "Produto", "Tipo", "Pagamento"]
    gp_raw["Data"] = pd.to_datetime(gp_raw["Data"], errors="coerce")
    gp = gp_raw[gp_raw["Data"].dt.month == 3].copy()
    gp["Plataforma"] = "Gympass"
    gp = gp.rename(columns={"Visitante": "Cliente"})

    tp_raw = pd.read_excel("data/Totalpass_anonimizado.xlsx", header=0)
    tp_raw.columns = ["ID", "Codigo", "Nome_Academia",
                      "Plano", "Cliente", "Repasse", "Validado_em"]
    tp_raw["Validado_em"] = pd.to_datetime(tp_raw["Validado_em"],
                                           format="%d/%m/%Y %H:%M:%S", errors="coerce")
    tp = tp_raw[tp_raw["Validado_em"].dt.month == 3].copy()
    tp["Plataforma"] = "Totalpass"

    gp_visits = gp.groupby(["Cliente", "Plataforma"]
                           ).size().reset_index(name="Visitas")
    tp_visits = tp.groupby(["Cliente", "Plataforma"]
                           ).size().reset_index(name="Visitas")
    all_visits = pd.concat([gp_visits, tp_visits], ignore_index=True)

    def calcular_repasse(row):
        v = row["Visitas"]
        if row["Plataforma"] == "Gympass":
            return round(v * 16.27, 2) if v <= 12 else GP_TETO
        else:
            return round(v * 16.01, 2) if v <= 12 else TP_TETO

    all_visits["Repasse_Realizado"] = all_visits.apply(
        calcular_repasse, axis=1)
    all_visits["Repasse_Perdido"] = all_visits.apply(
        lambda r: round(max(0, (GP_TETO if r["Plataforma"] == "Gympass" else TP_TETO) - r["Repasse_Realizado"]), 2), axis=1)

    def cluster(v):
        if v <= 6:
            return "Baixo (1-6)"
        if v <= 12:
            return "Intermediario (7-12)"
        return "Teto atingido (13+)"

    all_visits["Cluster"] = all_visits["Visitas"].apply(cluster)
    return all_visits


all_visits = load_data()

# ── MÉTRICAS ──────────────────────────────────────────────────
total_clientes = all_visits["Cliente"].nunique()
total_checkins = all_visits["Visitas"].sum()
repasse_bruto = round(all_visits["Repasse_Realizado"].sum(), 2)
repasse_liquido = round(repasse_bruto * 0.90, 2)
repasse_perdido = round(all_visits["Repasse_Perdido"].sum(), 2)
teto_atingido = (all_visits["Visitas"] >= 13).sum()

intermediarios = all_visits[all_visits["Cluster"]
                            == "Intermediario (7-12)"].copy()
total_inter = len(intermediarios)
media_visitas_int = round(intermediarios["Visitas"].mean(), 1)

cenarios = []
for label, pct in [("Conservador (25%)", 0.25), ("Moderado (50%)", 0.50),
                   ("Otimista (75%)", 0.75), ("Maximo (100%)", 1.0)]:
    n = max(1, round(total_inter * pct))
    top = intermediarios.sort_values(
        "Repasse_Perdido", ascending=False).head(n)
    ganho = round(top["Repasse_Perdido"].sum() * 0.90, 2)
    cenarios.append((label, n, ganho))

# ── PDF ───────────────────────────────────────────────────────


class PDF(FPDF):

    def header(self):
        self.set_fill_color(30, 30, 30)
        self.rect(0, 0, 210, 22, 'F')
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 6)
        self.cell(0, 10, "Relatorio de Parcerias - Marco 2026")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 180, 180)
        self.set_xy(10, 14)
        self.cell(0, 6, "Gympass . Totalpass . Analise de frequencia e repasse")
        self.ln(18)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10,
                  f"Gerado em {datetime.now().strftime('%d/%m/%Y')} · Análise: Matheus Souza · Dados: Gympass & Totalpass",
                  align="C")


def kpi_box(pdf, x, y, w, h, label, value, color):
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, h, 'F')
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(200, 200, 200)
    pdf.set_xy(x + 3, y + 3)
    pdf.cell(w - 6, 5, label)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(x + 3, y + 9)
    pdf.cell(w - 6, 10, value)


pdf = PDF()
pdf.add_page()
pdf.set_auto_page_break(auto=False)

# ── KPI BOXES ─────────────────────────────────────────────────
kpis = [
    ("Clientes únicos",     str(total_clientes),              (40, 40, 40)),
    ("Teto atingido",       f"{teto_atingido} clientes",      (40, 40, 40)),
    ("Repasse líquido",     f"R$ {repasse_liquido:,.2f}",     (20, 90, 50)),
    ("Repasse perdido",     f"R$ {repasse_perdido:,.2f}",     (140, 40, 40)),
]

box_w, box_h, gap = 44, 24, 4
start_x, start_y = 10, 28
for i, (label, value, color) in enumerate(kpis):
    kpi_box(pdf, start_x + i * (box_w + gap), start_y,
            box_w, box_h, label, value, color)

# ── SEÇÃO: CLUSTERS ───────────────────────────────────────────
y = 62
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(30, 30, 30)
pdf.set_xy(10, y)
pdf.cell(0, 7, "Distribuicao de clientes por cluster - Marco 2026")

cluster_data = all_visits.groupby("Cluster").agg(
    Clientes=("Cliente", "count"),
    Repasse_Perdido=("Repasse_Perdido", "sum")
).reset_index()

y += 9
headers = ["Cluster", "Clientes", "Repasse perdido (R$)"]
cols = [80, 30, 60]
pdf.set_fill_color(50, 50, 50)
pdf.set_text_color(255, 255, 255)
pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(10, y)
for h, w in zip(headers, cols):
    pdf.cell(w, 7, h, fill=True)
pdf.ln()

row_colors = {
    "Baixo (1-6)":          (252, 235, 235),
    "Intermediario (7-12)": (250, 238, 218),
    "Teto atingido (13+)":  (234, 243, 222),
}
label_map = {
    "Baixo (1-6)":          "Baixo (1-6)",
    "Intermediario (7-12)": "Intermediario (7-12)",
    "Teto atingido (13+)":  "Teto atingido (13+)",
}
order = ["Baixo (1-6)", "Intermediario (7-12)", "Teto atingido (13+)"]

for cl in order:
    row = cluster_data[cluster_data["Cluster"] == cl]
    if row.empty:
        continue
    r = row.iloc[0]
    rc = row_colors.get(cl, (245, 245, 245))
    pdf.set_fill_color(*rc)
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(80, 7, label_map[cl], fill=True)
    pdf.cell(30, 7, str(int(r["Clientes"])), fill=True)
    pdf.cell(60, 7, f"R$ {r['Repasse_Perdido']:,.2f}", fill=True)
    pdf.ln()

# ── SEÇÃO: HIPÓTESE DE CONVERSÃO ──────────────────────────────
y = pdf.get_y() + 10
pdf.set_xy(10, y)
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(30, 30, 30)
pdf.cell(0, 7, "Hipotese de conversao - Cluster intermediario para o Teto")

y += 8
pdf.set_xy(10, y)
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(190, 5,
               f"O cluster intermediário possui {total_inter} clientes com média de {media_visitas_int} visitas/mês. "
               f"São necessárias em média {13 - media_visitas_int:.0f} visitas adicionais por cliente para atingir o teto de repasse. "
               f"Abaixo, o impacto financeiro projetado por cenário de conversão (já descontada a taxa de 10%):")

y = pdf.get_y() + 4
headers2 = ["Cenário", "Clientes convertidos", "Ganho líquido projetado"]
cols2 = [65, 55, 70]
pdf.set_fill_color(50, 50, 50)
pdf.set_text_color(255, 255, 255)
pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(10, y)
for h, w in zip(headers2, cols2):
    pdf.cell(w, 7, h, fill=True)
pdf.ln()

bar_colors = [
    (240, 150, 150),
    (240, 200, 120),
    (120, 180, 230),
    (150, 210, 120),
]
for i, (label, n, ganho) in enumerate(cenarios):
    pdf.set_fill_color(*bar_colors[i])
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(65, 7, label, fill=True)
    pdf.cell(55, 7, str(n), fill=True)
    pdf.cell(70, 7, f"R$ {ganho:,.2f}", fill=True)
    pdf.ln()

# ── SEÇÃO: INSIGHT FINAL ──────────────────────────────────────
y = pdf.get_y() + 10
pdf.set_xy(10, y)
pdf.set_fill_color(230, 241, 251)
pdf.rect(10, y, 190, 22, 'F')
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(20, 70, 130)
pdf.set_xy(13, y + 3)
pdf.cell(0, 5, "Recomendacao estrategica")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(30, 30, 30)
pdf.set_xy(13, y + 9)
pdf.multi_cell(184, 5,
               f"Priorizar acoes de engajamento para os {cenarios[0][1]} clientes do cenario conservador representa "
               f"um ganho liquido imediato de R$ {cenarios[0][2]:,.2f}/mes com minimo esforco operacional. "
               f"No cenario otimista, o potencial chega a R$ {cenarios[2][2]:,.2f}/mes.")

# ── SALVAR ────────────────────────────────────────────────────
pdf.output("assets/relatorio_marco_2026.pdf")
print("Relatório gerado: assets/relatorio_marco_2026.pdf")
