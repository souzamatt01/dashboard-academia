import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Simulador de Conversão",
                   page_icon="📈", layout="wide")

# ── CONSTANTES ────────────────────────────────────────────────
GP_TETO = 195.30
TP_TETO = 208.09


@st.cache_data
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
            return "Baixo (1–6)"
        if v <= 12:
            return "Intermediário (7–12)"
        return "Teto atingido (13+)"

    all_visits["Cluster"] = all_visits["Visitas"].apply(cluster)
    return all_visits


all_visits = load_data()
intermediarios = all_visits[all_visits["Cluster"]
                            == "Intermediário (7–12)"].copy()
total_inter = len(intermediarios)

# ── HEADER ────────────────────────────────────────────────────
st.markdown("## Simulador de Conversão")
st.caption("Projete o impacto financeiro de converter clientes do cluster intermediário para o teto de repasse")
st.divider()

# ── CONTEXTO ──────────────────────────────────────────────────
ganho_potencial_total = round(
    intermediarios["Repasse_Perdido"].sum() * 0.90, 2)

col1, col2, col3 = st.columns(3)
col1.metric("Clientes no cluster intermediário", total_inter)
col2.metric("Visitas médias atuais", f"{intermediarios['Visitas'].mean():.1f}")
col3.metric("Ganho potencial se todos converterem",
            f"R$ {ganho_potencial_total:,.2f}")

st.divider()

# ── SIMULADOR ─────────────────────────────────────────────────
st.markdown("#### Quantos clientes intermediários você quer converter?")
st.caption(
    "Arraste o slider e veja o impacto financeiro projetado para o próximo mês")

n_converter = st.slider(
    label="Clientes a converter",
    min_value=1,
    max_value=total_inter,
    value=round(total_inter * 0.25),
    step=1
)

# Pega os n clientes com maior repasse perdido (maior potencial)
top_converter = intermediarios.sort_values(
    "Repasse_Perdido", ascending=False).head(n_converter)

ganho_bruto = round(top_converter["Repasse_Perdido"].sum(), 2)
ganho_liquido = round(ganho_bruto * 0.90, 2)
pct_convertida = round((n_converter / total_inter) * 100, 1)

st.markdown("---")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Clientes selecionados",    n_converter)
r2.metric("% do cluster convertida",  f"{pct_convertida}%")
r3.metric("Ganho bruto projetado",    f"R$ {ganho_bruto:,.2f}")
r4.metric("Ganho líquido (−10%)",     f"R$ {ganho_liquido:,.2f}",
          delta=f"+R$ {ganho_liquido:,.2f}", delta_color="normal")

st.divider()

# ── COMPARATIVO CENÁRIOS ──────────────────────────────────────
st.markdown("#### Comparativo de cenários")

cenarios = []
for label, pct in [("Conservador (25%)", 0.25), ("Moderado (50%)", 0.50), ("Otimista (75%)", 0.75), ("Máximo (100%)", 1.0)]:
    n = max(1, round(total_inter * pct))
    top = intermediarios.sort_values(
        "Repasse_Perdido", ascending=False).head(n)
    ganho = round(top["Repasse_Perdido"].sum() * 0.90, 2)
    cenarios.append({"Cenário": label, "Clientes": n,
                    "Ganho líquido (R$)": ganho})

df_cenarios = pd.DataFrame(cenarios)

fig = px.bar(
    df_cenarios,
    x="Cenário",
    y="Ganho líquido (R$)",
    color="Cenário",
    color_discrete_sequence=["#E24B4A", "#EF9F27", "#378ADD", "#639922"],
    text=df_cenarios["Ganho líquido (R$)"].apply(lambda x: f"R$ {x:,.0f}")
)
fig.update_traces(textposition="outside")
fig.update_layout(
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    height=350,
    margin=dict(t=30, b=10, l=0, r=0)
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── TABELA DOS CLIENTES SELECIONADOS ─────────────────────────
st.markdown(
    f"#### Clientes priorizados para conversão ({n_converter} selecionados)")
st.caption("Ordenados por maior potencial de ganho — esses são os clientes que mais impactam o repasse se atingirem o teto")

st.dataframe(
    top_converter[["Cliente", "Plataforma", "Visitas",
                   "Repasse_Realizado", "Repasse_Perdido"]]
    .reset_index(drop=True)
    .rename(columns={
        "Repasse_Realizado": "Repasse Atual (R$)",
        "Repasse_Perdido":   "Ganho Potencial (R$)"
    }),
    use_container_width=True,
    height=350
)
