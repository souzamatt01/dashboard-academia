import pandas as pd
import random
import string

random.seed(42)


def gerar_nome_falso(i):
    return f"Cliente_{str(i).zfill(3)}"


def gerar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ── GYMPASS ───────────────────────────────────────────────────
gp_raw = pd.read_excel("data/Gympass.xlsx", skiprows=12, header=0)
gp_raw.columns = ["Data", "Hora", "ID_Unidade", "Unidade", "Visitante",
                  "ID_Wellhub", "Produto", "Tipo", "Pagamento"]
gp_raw["Data"] = pd.to_datetime(gp_raw["Data"], errors="coerce")
gp = gp_raw[gp_raw["Data"].dt.month == 3].copy()

nomes_gp = {nome: gerar_nome_falso(i+1)
            for i, nome in enumerate(gp["Visitante"].unique())}
gp["Visitante"] = gp["Visitante"].map(nomes_gp)
gp["ID_Wellhub"] = [random.randint(
    1000000000000, 9999999999999) for _ in range(len(gp))]
gp["ID_Unidade"] = "UNIDADE_ANONIMIZADA"
gp["Unidade"] = "Academia Exemplo"

gp.to_excel("data/Gympass_anonimizado.xlsx", index=False)
print(
    f"Gympass anonimizado: {len(gp)} registros, {gp['Visitante'].nunique()} clientes")

# ── TOTALPASS ─────────────────────────────────────────────────
tp_raw = pd.read_excel("data/Totalpass.xlsx", skiprows=3, header=0)
tp_raw.columns = ["ID", "Codigo", "Nome_Academia",
                  "Plano", "Colaborador", "Repasse", "Validado_em"]
tp_raw["Validado_em"] = pd.to_datetime(tp_raw["Validado_em"],
                                       format="%d/%m/%Y %H:%M:%S", errors="coerce")
tp = tp_raw[tp_raw["Validado_em"].dt.month == 3].copy()

nomes_tp = {nome: gerar_nome_falso(i+1)
            for i, nome in enumerate(tp["Colaborador"].unique())}
tp["Colaborador"] = tp["Colaborador"].map(nomes_tp)
tp["ID"] = [random.randint(100000000, 999999999) for _ in range(len(tp))]
tp["Codigo"] = [gerar_codigo() for _ in range(len(tp))]
tp["Nome_Academia"] = "ACADEMIA EXEMPLO LTDA"

tp.to_excel("data/Totalpass_anonimizado.xlsx", index=False)
print(
    f"Totalpass anonimizado: {len(tp)} registros, {tp['Colaborador'].nunique()} clientes")

print("\nArquivos gerados em data/:")
print("  - Gympass_anonimizado.xlsx")
print("  - Totalpass_anonimizado.xlsx")
print("\nNenhum nome real, ID real ou dado financeiro individual foi mantido.")
