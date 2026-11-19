import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Permanência e Êxito - IFMT CNP", layout="wide"
)
st.title("📊 Painel de Permanência e Êxito - Campus Campo Novo do Parecis")

# 1. Upload da planilha exportada do SUAP
arquivo = st.file_uploader(
    "Suba a planilha exportada do SUAP (.xlsx ou .csv)", type=["xlsx", "csv"]
)

if arquivo:
  # Lê o arquivo
  if arquivo.name.endswith(".xlsx"):
    df = pd.read_excel(arquivo)
  else:
    try:
      df = pd.read_csv(arquivo, sep=";", encoding="utf-8")
    except:
      df = pd.read_csv(arquivo, sep=";", encoding="latin1")

  # Limpeza e conversão de colunas numéricas (tratando vírgulas do SUAP)
  def limpar_numero(serie):
    return pd.to_numeric(
        serie.astype(str).str.replace(",", ".").str.replace("%", "").str.strip(),
        errors="coerce",
    )

  if "Frequência no Período" in df.columns:
    df["Freq_Num"] = limpar_numero(df["Frequência no Período"])
  if "I.R.A." in df.columns:
    df["IRA_Num"] = limpar_numero(df["I.R.A."])
  if "Renda Per Capita" in df.columns:
    df["Renda_Num"] = limpar_numero(df["Renda Per Capita"])

  # Trata Ano de Ingresso como texto limpo (sem ".0") para filtros e gráficos
  if "Ano de Ingresso" in df.columns:
    df["Ano_Ingresso_Str"] = (
        df["Ano de Ingresso"]
        .fillna("Não informado")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
    )

  # Classificação de Faixas de Renda Per Capita
  def classificar_renda(v):
    if pd.isna(v):
      return "Não informado"
    elif v <= 0.5:
      return "1. Até 0,5 SM"
    elif v <= 1.0:
      return "2. De 0,5 a 1,0 SM"
    elif v <= 1.5:
      return "3. De 1,0 a 1,5 SM"
    elif v <= 3.0:
      return "4. De 1,5 a 3,0 SM"
    else:
      return "5. Acima de 3,0 SM"

  if "Renda_Num" in df.columns:
    df["Faixa de Renda"] = df["Renda_Num"].apply(classificar_renda)

  col_situacao = "Situação no Curso"

  # ==========================================
  # 2. FILTROS NA BARRA LATERAL
  # ==========================================
  st.sidebar.header("🔍 Filtros de Análise")

  if "Modalidade" in df.columns:
    modalidades = ["Todas"] + sorted(
        df["Modalidade"].dropna().unique().tolist()
    )
    mod_sel = st.sidebar.selectbox("Modalidade:", modalidades)
    if mod_sel != "Todas":
      df = df[df["Modalidade"] == mod_sel]

  if "Descrição do Curso" in df.columns:
    cursos = ["Todos"] + sorted(
        df["Descrição do Curso"].dropna().unique().tolist()
    )
    curso_sel = st.sidebar.selectbox("Curso:", cursos)
    if curso_sel != "Todos":
      df = df[df["Descrição do Curso"] == curso_sel]

  if "Ano_Ingresso_Str" in df.columns:
    anos_disp = sorted(df["Ano_Ingresso_Str"].unique().tolist())
    anos_sel = st.sidebar.multiselect(
        "Ano de Ingresso:", options=anos_disp, default=anos_disp
    )
    if anos_sel:
      df = df[df["Ano_Ingresso_Str"].isin(anos_sel)]

  if col_situacao in df.columns:
    situacoes_disp = sorted(df[col_situacao].dropna().unique().tolist())
    sit_sel = st.sidebar.multiselect(
        f"{col_situacao}:", options=situacoes_disp, default=situacoes_disp
    )
    if sit_sel:
      df = df[df[col_situacao].isin(sit_sel)]

  # ==========================================
  # 3. MÉTRICAS PRINCIPAIS (KPIs)
  # ==========================================
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("Estudantes Filtrados", len(df))

  if "Freq_Num" in df.columns:
    baixa_freq = df[df["Freq_Num"] < 75]
    c2.metric("Alerta: Frequência < 75%", len(baixa_freq))

  if "IRA_Num" in df.columns:
    media_ira = df["IRA_Num"].mean()
    c3.metric(
        "Média Geral do I.R.A.",
        f"{media_ira:.2f}" if pd.notna(media_ira) else "-",
    )

  if col_situacao in df.columns:
    evadidos = df[
        df[col_situacao]
        .astype(str)
        .str.contains("Evasão|Evadido|Desistente", case=False)
    ]
    c4.metric("Total em Evasão", len(evadidos))

  st.divider()

  # ==========================================
  # 4. LINHA 1 (INÍCIO): PANORAMA GERAL (SITUAÇÃO E ANO DE INGRESSO)
  # ==========================================
  g_ini1, g_ini2 = st.columns(2)

  with g_ini1:
    if col_situacao in df.columns:
      df_sit_total = (
          df[col_situacao]
          .fillna("Não informado")
          .value_counts()
          .reset_index()
      )
      df_sit_total.columns = [col_situacao, "Qtd"]

      fig_ini1 = px.bar(
          df_sit_total,
          x=col_situacao,
          y="Qtd",
          color=col_situacao,
          title="Quantidade de Estudantes por Situação no Curso",
          text_auto=True,
      )
      fig_ini1.update_layout(showlegend=False)
      st.plotly_chart(fig_ini1, use_container_width=True)

  with g_ini2:
    if "Ano_Ingresso_Str" in df.columns:
      df_ano_total = (
          df["Ano_Ingresso_Str"].value_counts().sort_index().reset_index()
      )
      df_ano_total.columns = ["Ano de Ingresso", "Qtd"]

      fig_ini2 = px.bar(
          df_ano_total,
          x="Ano de Ingresso",
          y="Qtd",
          title="Quantidade de Ingressantes por Ano",
          text_auto=True,
      )
      # Garante que o eixo X trate os anos como categorias discretas
      fig_ini2.update_xaxes(type="category")
      st.plotly_chart(fig_ini2, use_container_width=True)

  st.divider()

  # ==========================================
  # 5. LINHA 2: RENDA PER CAPITA E ZONA RESIDENCIAL
  # ==========================================
  g1, g2 = st.columns(2)

  with g1:
    if "Faixa de Renda" in df.columns and col_situacao in df.columns:
      df_renda = (
          df.groupby(["Faixa de Renda", col_situacao])
          .size()
          .reset_index(name="Qtd")
      )
      fig1 = px.bar(
          df_renda,
          x="Faixa de Renda",
          y="Qtd",
          color=col_situacao,
          title=f"{col_situacao} por Faixa de Renda",
          barmode="stack",
          text_auto=True,
      )
      st.plotly_chart(fig1, use_container_width=True)

  with g2:
    if "Zona Residencial" in df.columns and col_situacao in df.columns:
      df_zona = (
          df.groupby(["Zona Residencial", col_situacao])
          .size()
          .reset_index(name="Qtd")
      )
      fig2 = px.bar(
          df_zona,
          x="Zona Residencial",
          y="Qtd",
          color=col_situacao,
          title=f"{col_situacao}: Zona Urbana vs. Rural",
          barmode="group",
          text_auto=True,
      )
      st.plotly_chart(fig2, use_container_width=True)

  st.divider()

  # ==========================================
  # 6. LINHA 3: FREQUÊNCIA E I.R.A.
  # ==========================================
  g3, g4 = st.columns(2)

  with g3:
    if (
        "Faixa de Renda" in df.columns
        and "Freq_Num" in df.columns
        and "IRA_Num" in df.columns
    ):
      df_medias_renda = (
          df.groupby("Faixa de Renda")[["Freq_Num", "IRA_Num"]]
          .mean()
          .reset_index()
      )
      df_medias_renda.columns = [
          "Faixa de Renda",
          "Frequência Média (%)",
          "I.R.A. Médio",
      ]

      df_melt = df_medias_renda.melt(
          id_vars="Faixa de Renda", var_name="Indicador", value_name="Média"
      )
      fig3 = px.bar(
          df_melt,
          x="Faixa de Renda",
          y="Média",
          color="Indicador",
          barmode="group",
          title="Média de Frequência (%) e I.R.A. por Faixa de Renda",
          text_auto=".1f",
      )
      st.plotly_chart(fig3, use_container_width=True)

  with g4:
    if (
        "Freq_Num" in df.columns
        and "IRA_Num" in df.columns
        and col_situacao in df.columns
    ):
      df_disp = df.dropna(subset=["Freq_Num", "IRA_Num"])
      fig4 = px.scatter(
          df_disp,
          x="Freq_Num",
          y="IRA_Num",
          color=col_situacao,
          hover_data=(
              ["Matrícula", "Descrição do Curso"]
              if "Matrícula" in df.columns
              else None
          ),
          title=f"Frequência (%) x I.R.A. por {col_situacao}",
          labels={"Freq_Num": "Frequência (%)", "IRA_Num": "I.R.A."},
      )
      fig4.add_vline(
          x=75,
          line_dash="dash",
          line_color="red",
          annotation_text="Mínimo 75%",
      )
      st.plotly_chart(fig4, use_container_width=True)

  st.divider()

  # ==========================================
  # 7. LINHA 4: ETNIA/RAÇA E ESCOLA DE ORIGEM
  # ==========================================
  g5, g6 = st.columns(2)

  with g5:
    col_etnia = (
        "Etnia/Raça (Caracterização)"
        if "Etnia/Raça (Caracterização)" in df.columns
        else "Etnia/Raça"
    )
    if col_etnia in df.columns and col_situacao in df.columns:
      df_etnia = df.copy()
      df_etnia[col_etnia] = df_etnia[col_etnia].fillna("Não informado")
      df_etnia_grp = (
          df_etnia.groupby([col_etnia, col_situacao])
          .size()
          .reset_index(name="Qtd")
      )
      fig5 = px.bar(
          df_etnia_grp,
          x=col_etnia,
          y="Qtd",
          color=col_situacao,
          title=f"{col_situacao} por Etnia/Raça",
          barmode="group",
          text_auto=True,
      )
      st.plotly_chart(fig5, use_container_width=True)

  with g6:
    if "Tipo de Escola de Origem" in df.columns and col_situacao in df.columns:
      df_esc = df.copy()
      df_esc["Tipo de Escola de Origem"] = df_esc[
          "Tipo de Escola de Origem"
      ].fillna("Não informado")
      df_esc_grp = (
          df_esc.groupby(["Tipo de Escola de Origem", col_situacao])
          .size()
          .reset_index(name="Qtd")
      )
      fig6 = px.bar(
          df_esc_grp,
          x="Tipo de Escola de Origem",
          y="Qtd",
          color=col_situacao,
          title=f"{col_situacao} por Tipo de Escola de Origem",
          barmode="group",
          text_auto=True,
      )
      st.plotly_chart(fig6, use_container_width=True)

  st.divider()

  # ==========================================
  # 8. LINHA 5: FORMA DE INGRESSO
  # ==========================================
  if "Forma de Ingresso" in df.columns:
    g7, g8 = st.columns(2)

    with g7:
      df_ing_total = (
          df["Forma de Ingresso"]
          .fillna("Não informado")
          .value_counts()
          .reset_index()
      )
      df_ing_total.columns = ["Forma de Ingresso", "Qtd"]
      df_ing_total = df_ing_total.sort_values(by="Qtd", ascending=True)

      fig7 = px.bar(
          df_ing_total,
          x="Qtd",
          y="Forma de Ingresso",
          orientation="h",
          title="Quantidade Total de Estudantes por Forma de Ingresso",
          text_auto=True,
      )
      st.plotly_chart(fig7, use_container_width=True)

    with g8:
      if col_situacao in df.columns:
        df_temp = df.copy()
        df_temp["Forma de Ingresso"] = df_temp["Forma de Ingresso"].fillna(
            "Não informado"
        )
        df_ing_sit = (
            df_temp.groupby(["Forma de Ingresso", col_situacao])
            .size()
            .reset_index(name="Qtd")
        )

        fig8 = px.bar(
            df_ing_sit,
            x="Qtd",
            y="Forma de Ingresso",
            color=col_situacao,
            orientation="h",
            barmode="stack",
            title=f"{col_situacao} por Forma de Ingresso",
            text_auto=True,
        )
        st.plotly_chart(fig8, use_container_width=True)
