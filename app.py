import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Academia Dashboard",
    page_icon="🏋️",
    layout="wide"
)

# ── CONSTANTES DE REPASSE ─────────────────────────────────────
GP_VALOR_UNIT = 16.27
GP_VALOR_COMP = 0.06
GP_TETO = 195.30
GP_MAX_CHECKIN = 13

TP_VALOR_UNIT = 16.01
TP_VALOR_COMP = 15.97
TP_TETO = 208.09
TP_MAX_CHECKIN = 13

# ── LOAD DATA ─────────────────────────────────────────────────


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
    tp["Data"] = tp["Validado_em"].dt.normalize()

    gp_visits = gp.groupby(["Cliente", "Plataforma"]
                           ).size().reset_index(name="Visitas")
    tp_visits = tp.groupby(["Cliente", "Plataforma"]
                           ).size().reset_index(name="Visitas")
    all_visits = pd.concat([gp_visits, tp_visits], ignore_index=True)

    def calcular_repasse(row):
        v = row["Visitas"]
        if row["Plataforma"] == "Gympass":
            if v <= 0:
                return 0.0
            if v <= 12:
                return round(v * GP_VALOR_UNIT, 2)
            return GP_TETO
        else:
            if v <= 0:
                return 0.0
            if v <= 12:
                return round(v * TP_VALOR_UNIT, 2)
            return TP_TETO

    def calcular_perdido(row):
        teto = GP_TETO if row["Plataforma"] == "Gympass" else TP_TETO
        return round(max(0, teto - row["Repasse_Realizado"]), 2)

    def cluster(v):
        if v <= 6:
            return "Baixo (1–6)"
        if v <= 12:
            return "Intermediário (7–12)"
        return "Teto atingido (13+)"

    all_visits["Repasse_Realizado"] = all_visits.apply(
        calcular_repasse, axis=1)
    all_visits["Repasse_Perdido"] = all_visits.apply(calcular_perdido, axis=1)
    all_visits["Cluster"] = all_visits["Visitas"].apply(cluster)

    gp_daily = (gp.groupby(gp["Data"].dt.day_name())
                  .size().reset_index(name="Visitas")
                  .rename(columns={"Data": "DiaNome"}))
    translate = {"Monday": "Seg", "Tuesday": "Ter", "Wednesday": "Qua",
                 "Thursday": "Qui", "Friday": "Sex", "Saturday": "Sáb"}
    gp_daily["Dia"] = pd.Categorical(
        gp_daily["DiaNome"].map(translate),
        categories=["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"], ordered=True
    )
    gp_daily = gp_daily.dropna(subset=["Dia"]).sort_values("Dia")

    gp_hourly = (gp.groupby(gp["Hora"].str[:2].astype(int))
                   .size().reset_index(name="Visitas"))
    gp_hourly.columns = ["Hora", "Visitas"]

    return all_visits, gp, tp, gp_daily, gp_hourly


all_visits, gp, tp, gp_daily, gp_hourly = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Filtros")
    plataformas = st.multiselect(
        "Plataforma",
        options=["Gympass", "Totalpass"],
        default=["Gympass", "Totalpass"]
    )
    clusters = st.multiselect(
        "Cluster",
        options=["Baixo (1–6)", "Intermediário (7–12)", "Teto atingido (13+)"],
        default=["Baixo (1–6)", "Intermediário (7–12)", "Teto atingido (13+)"]
    )
    st.markdown("---")
    st.caption("Dados referentes a março/2026")

df = all_visits[
    all_visits["Plataforma"].isin(plataformas) &
    all_visits["Cluster"].isin(clusters)
]

# ── HEADER ────────────────────────────────────────────────────
st.markdown("## Dashboard de Parcerias — Março 2026")
st.caption("Gympass · Totalpass · Análise de frequência e repasse")
st.divider()

# ── KPI CARDS — LINHA 1: VISÃO GERAL ─────────────────────────
total_clientes = df["Cliente"].nunique()
total_checkins = df["Visitas"].sum()
media_visitas = round(df["Visitas"].mean(), 1)
teto_atingido = (df["Visitas"] >= 13).sum()
repasse_realizado = round(df["Repasse_Realizado"].sum(), 2)
repasse_perdido = round(df["Repasse_Perdido"].sum(), 2)

c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.8, 1.8])
c1.metric("Clientes únicos",    total_clientes)
c2.metric("Check-ins totais",   total_checkins)
c3.metric("Média de visitas",   media_visitas)
c4.metric("Atingiram o teto",   teto_atingido)
c5.metric("Repasse realizado",  f"R$ {repasse_realizado/1000:.1f}k")
c6.metric("Repasse perdido",    f"R$ {repasse_perdido/1000:.1f}k",
          delta=f"-R$ {repasse_perdido/1000:.1f}k", delta_color="inverse")

st.divider()

# ── KPI CARDS — LINHA 2: REPASSE POR PLATAFORMA ──────────────
st.markdown("#### Repasse por plataforma")

gp_df = all_visits[all_visits["Plataforma"] == "Gympass"]
tp_df = all_visits[all_visits["Plataforma"] == "Totalpass"]

gp_clientes = gp_df["Cliente"].nunique()
gp_teto_count = (gp_df["Visitas"] >= 13).sum()
gp_realizado = round(gp_df["Repasse_Realizado"].sum(), 2)
gp_liquido = round(gp_realizado * 0.90, 2)
gp_potencial = round(gp_clientes * GP_TETO, 2)
gp_perdido = round(gp_df["Repasse_Perdido"].sum(), 2)
gp_aproveitamento = round((gp_realizado / gp_potencial) * 100, 1)

tp_clientes = tp_df["Cliente"].nunique()
tp_teto_count = (tp_df["Visitas"] >= 13).sum()
tp_realizado = round(tp_df["Repasse_Realizado"].sum(), 2)
tp_liquido = round(tp_realizado * 0.90, 2)
tp_potencial = round(tp_clientes * TP_TETO, 2)
tp_perdido = round(tp_df["Repasse_Perdido"].sum(), 2)
tp_aproveitamento = round((tp_realizado / tp_potencial) * 100, 1)

col_gp, col_tp = st.columns(2)

with col_gp:
    st.markdown(f"""
    <div style="border:0.5px solid #333; border-radius:10px; padding:14px 18px;">
        <p style="font-size:13px; font-weight:600; margin-bottom:12px;">
            Gympass — teto R$ 195,30 / 13 check-ins
        </p>
        <table style="width:100%; font-size:13px; border-collapse:collapse;">
            <tr style="color:#aaa;">
                <td>Clientes</td>
                <td>Teto atingido</td>
                <td>Repasse bruto</td>
                <td>Líquido (−10%)</td>
            </tr>
            <tr style="font-size:22px; font-weight:600;">
                <td>{gp_clientes}</td>
                <td>{gp_teto_count}</td>
                <td>R$ {gp_realizado/1000:.1f}k</td>
                <td>R$ {gp_liquido/1000:.1f}k</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

with col_tp:
    st.markdown(f"""
    <div style="border:0.5px solid #333; border-radius:10px; padding:14px 18px;">
        <p style="font-size:13px; font-weight:600; margin-bottom:12px;">
            Totalpass — teto R$ 208,09 / 13 check-ins
        </p>
        <table style="width:100%; font-size:13px; border-collapse:collapse;">
            <tr style="color:#aaa;">
                <td>Clientes</td>
                <td>Teto atingido</td>
                <td>Repasse bruto</td>
                <td>Líquido (−10%)</td>
            </tr>
            <tr style="font-size:22px; font-weight:600;">
                <td>{tp_clientes}</td>
                <td>{tp_teto_count}</td>
                <td>R$ {tp_realizado/1000:.1f}k</td>
                <td>R$ {tp_liquido/1000:.1f}k</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── ROW 1: CLUSTERS ───────────────────────────────────────────
col1, col2 = st.columns(2)

color_map = {
    "Baixo (1–6)":           "#E24B4A",
    "Intermediário (7–12)":  "#EF9F27",
    "Teto atingido (13+)":   "#639922"
}

with col1:
    st.markdown("#### Distribuição por cluster")
    cluster_summary = df.groupby("Cluster").agg(
        Clientes=("Cliente", "count"),
        Repasse_Perdido=("Repasse_Perdido", "sum")
    ).reset_index()
    fig_cluster = px.bar(cluster_summary, x="Cluster", y="Clientes",
                         color="Cluster", color_discrete_map=color_map, text="Clientes")
    fig_cluster.update_traces(textposition="outside")
    fig_cluster.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)", height=300,
                              margin=dict(t=10, b=10, l=0, r=0))
    st.plotly_chart(fig_cluster, use_container_width=True)

with col2:
    st.markdown("#### Repasse perdido por cluster (R$)")
    fig_perdido = px.bar(cluster_summary, x="Cluster", y="Repasse_Perdido",
                         color="Cluster", color_discrete_map=color_map,
                         text=cluster_summary["Repasse_Perdido"].apply(lambda x: f"R$ {x:,.0f}"))
    fig_perdido.update_traces(textposition="outside")
    fig_perdido.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)", height=300,
                              margin=dict(t=10, b=10, l=0, r=0))
    st.plotly_chart(fig_perdido, use_container_width=True)

st.divider()

# ── ROW 2: TOP 5 ──────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### Top 5 — Gympass")
    top_gp = (gp_df.sort_values("Visitas", ascending=False).head(5))
    fig_gp = px.bar(top_gp, x="Visitas", y="Cliente", orientation="h",
                    color_discrete_sequence=["#378ADD"], text="Visitas")
    fig_gp.update_traces(textposition="outside")
    fig_gp.update_layout(yaxis=dict(autorange="reversed"), showlegend=False,
                         plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                         height=280, margin=dict(t=10, b=10, l=0, r=0))
    st.plotly_chart(fig_gp, use_container_width=True)

with col4:
    st.markdown("#### Top 5 — Totalpass")
    top_tp = (tp_df.sort_values("Visitas", ascending=False).head(5))
    fig_tp = px.bar(top_tp, x="Visitas", y="Cliente", orientation="h",
                    color_discrete_sequence=["#639922"], text="Visitas")
    fig_tp.update_traces(textposition="outside")
    fig_tp.update_layout(yaxis=dict(autorange="reversed"), showlegend=False,
                         plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                         height=280, margin=dict(t=10, b=10, l=0, r=0))
    st.plotly_chart(fig_tp, use_container_width=True)

st.divider()

# ── ROW 3: PADRÃO TEMPORAL ────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.markdown("#### Visitas por dia da semana — Gympass")
    fig_dow = px.bar(gp_daily, x="Dia", y="Visitas",
                     color_discrete_sequence=["#378ADD"], text="Visitas")
    fig_dow.update_traces(textposition="outside")
    fig_dow.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          height=280, margin=dict(t=10, b=10, l=0, r=0))
    st.plotly_chart(fig_dow, use_container_width=True)

with col6:
    st.markdown("#### Visitas por hora do dia — Gympass")
    fig_hour = px.area(gp_hourly, x="Hora", y="Visitas",
                       color_discrete_sequence=["#378ADD"])
    fig_hour.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           height=280, margin=dict(t=10, b=10, l=0, r=0))
    st.plotly_chart(fig_hour, use_container_width=True)

st.divider()

# ── TABELA DETALHADA ──────────────────────────────────────────
st.markdown("#### Tabela de clientes")
st.dataframe(
    df[["Cliente", "Plataforma", "Visitas", "Cluster",
        "Repasse_Realizado", "Repasse_Perdido"]]
    .sort_values("Visitas", ascending=False)
    .reset_index(drop=True)
    .rename(columns={
        "Repasse_Realizado": "Repasse Realizado (R$)",
        "Repasse_Perdido":   "Repasse Perdido (R$)"
    }),
    use_container_width=True,
    height=350
)
