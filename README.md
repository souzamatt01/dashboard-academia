# Academia Dashboard — Análise de Parcerias Gympass & Totalpass

Dashboard interativo com relatório executivo em PDF para análise de frequência e repasse de academias parceiras do Gympass e Totalpass.

Desenvolvido como projeto de consultoria de dados com foco em KPIs financeiros e tomada de decisão para gestores.

---

## Objetivo

Transformar os dados brutos de check-in das plataformas de parceria em insights acionáveis para o gestor da academia, respondendo perguntas como:

- Quantos clientes estão gerando repasse máximo?
- Quanto de receita está sendo perdido por baixa frequência?
- Quais clientes priorizar para aumentar o repasse no próximo mês?

---

## Funcionalidades

### Dashboard principal
- KPIs de repasse realizado, perdido e líquido (após taxa de 10%)
- Análise de repasse por plataforma com teto configurável
- Clusterização de clientes em 3 grupos por frequência de visitas
- Top 5 clientes mais frequentes por plataforma
- Padrão de visitas por dia da semana e hora do dia
- Filtros interativos por plataforma e cluster

### Simulador de conversão
- Slider interativo para projetar ganho financeiro por conversão de cluster
- Comparativo de 4 cenários: conservador, moderado, otimista e máximo
- Tabela de clientes priorizados por maior potencial de ganho

### Relatório executivo em PDF
- Gerado diretamente pelo dashboard com um clique
- KPIs consolidados, tabela de clusters e hipótese de conversão por cenário
- Alertas automáticos baseados nos dados do mês
- Ranking dos top 10 clientes por frequência
- Rodapé com identificação do consultor responsável

---

## Regras de negócio implementadas

| Plataforma | Valor por check-in | Teto de repasse |
|------------|-------------------|-----------------|
| Gympass    | R$ 16,27 (até 12º) | R$ 195,30      |
| Totalpass  | R$ 16,01 (até 12º) | R$ 208,09      |

Clusters definidos com base na régua de repasse:

- **Baixo (1–6):** menos da metade do caminho para o teto
- **Intermediário (7–12):** gerando valor mas abaixo do teto
- **Teto atingido (13+):** repasse máximo garantido

---

## Stack

- Python 3.13
- Streamlit — dashboard interativo
- Pandas — manipulação de dados
- Plotly — visualizações
- fpdf2 — geração de PDF

---

## Como rodar localmente

```bash
# Clone o repositório
git clone https://github.com/souzamatt01/dashboard-academia.git
cd dashboard-academia

# Crie o ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Instale as dependências
pip install -r requirements.txt

# Rode o dashboard
streamlit run app.py
```

O relatório PDF é gerado pelo botão dentro do próprio dashboard, sem necessidade de rodar scripts separados.

---

## Estrutura do projeto

```
dashboard-academia/
├── data/
│   ├── Gympass_anonimizado.xlsx
│   └── Totalpass_anonimizado.xlsx
├── pages/
│   └── 1_Simulador.py
├── app.py
├── relatorio.py
├── anonimizar.py
├── requirements.txt
└── README.md
```

---

## Privacidade e LGPD

Os dados utilizados neste repositório são **totalmente anonimizados**. Nenhum nome real de cliente, ID de usuário ou dado financeiro individual foi mantido. Os arquivos originais com dados reais nunca foram commitados neste repositório.

---

## Autor

**Matheus Souza**  
Cientista de Dados | Consultor de Dados  
[LinkedIn](https://www.linkedin.com/in/matheus-souza2099/) · [GitHub](https://github.com/souzamatt01)