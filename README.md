# 🚀 FIAP Tech Challenge - Fase 4: Predição de Ações com LSTM

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16-orange?style=for-the-badge&logo=tensorflow)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)
![Status](https://img.shields.io/badge/Status-Concluído-green?style=for-the-badge)

## 📄 Sobre o Projeto

Este projeto compõe a **Fase 4** do Tech Challenge da Pós-Graduação em **Machine Learning Engineering** da FIAP.

O objetivo foi desenvolver uma pipeline completa de Machine Learning (End-to-End) para prever o preço de fechamento das ações da **Petrobras (PETR4.SA)**. O sistema utiliza uma Rede Neural Recorrente (RNN) do tipo **LSTM (Long Short-Term Memory)**, capaz de capturar padrões temporais complexos em séries financeiras.

Diferente de uma "caixa preta", este projeto foca na **explicabilidade**, apresentando ao usuário final não apenas o valor previsto, mas também os indicadores macroeconômicos e técnicos que alimentaram a decisão da IA.

---

## 🎯 Funcionalidades Principais

*   **Pipeline de Dados em Tempo Real:** Coleta dados históricos via `yfinance` e indicadores macroeconômicos (Selic) via API do Banco Central.
*   **Engenharia de Features Avançada:** Calcula automaticamente 34 indicadores, incluindo RSI, MACD, Bandas de Bollinger, Volatilidade de Parkinson e correlações com Brent/Dólar.
*   **Modelo LSTM Otimizado:** Rede neural treinada para prever o *Retorno Logarítmico* (Log Return), garantindo estacionariedade e melhores resultados.
*   **Dashboard Interativo:** Frontend amigável que exibe:
    *   Cotação atual e dados de mercado.
    *   Painel de indicadores macroeconômicos e técnicos.
    *   Explicação pedagógica da metodologia usada.
    *   Tabela de previsão futura.
*   **API RESTful:** Backend robusto construído com **FastAPI**.

---

## 🛠️ Tecnologias Utilizadas

*   **Linguagem:** Python 3.12
*   **Gerenciamento de Dependências:** Poetry
*   **Machine Learning:** TensorFlow/Keras, Scikit-learn
*   **Processamento de Dados:** Pandas, NumPy, Yfinance
*   **Backend:** FastAPI, Uvicorn
*   **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
*   **Containerização:** Docker (Pronto para deploy)

---

## 🧠 Arquitetura da Solução

O projeto atende aos requisitos do desafio seguindo esta estrutura:

1.  **Coleta & Pré-processamento:**
    *   Os dados são normalizados usando `MinMaxScaler`.
    *   Transformação de séries temporais em janelas deslizantes (*sliding windows*) de 20 dias (Lookback).
2.  **Modelo LSTM:**
    *   Arquitetura com camadas LSTM, Dropout (para evitar overfitting) e Dense.
    *   Target: Log Return (Retorno Logarítmico) para estabilidade numérica.
3.  **Persistência:**
    *   O modelo treinado é salvo em `.keras`.
    *   Os escaladores (Scalers) são salvos em `.pkl` para garantir que os dados de entrada da API sofram a mesma transformação do treino.
4.  **Inferência (API):**
    *   O endpoint `/api/predict` recebe o pedido, baixa os dados mais recentes do mercado, processa as features e retorna a previsão com a escala invertida para o preço real (R$).

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
*   Python 3.12+
*   Poetry (Recomendado) ou Pip
*   Git

### Passo a Passo

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/SEU-USUARIO/tc-fiap-fase4.git
    cd tc-fiap-fase4
    ```

2.  **Instale as dependências com Poetry:**
    ```bash
    poetry install
    poetry shell
    ```

3.  **Treine o Modelo (Opcional):**
    *   Se quiser gerar novos arquivos `.keras` e `.pkl`, execute o notebook Jupyter localizado em `notebooks/` ou o script de treino (se houver).
    *   *Nota: O projeto já vem com modelos pré-treinados na pasta `src/models`.*

4.  **Inicie a API:**
    ```bash
    fastapi dev src/api/main.py
    ```

5.  **Acesse o Dashboard:**
    *   Abra o navegador em: `http://127.0.0.1:8000`
    *   Para a documentação da API (Swagger): `http://127.0.0.1:8000/docs`

---

## 🐳 Executando com Docker

Para garantir a reprodutibilidade e escalabilidade, você pode rodar a aplicação em um container:

1.  **Construir a imagem:**
    ```bash
    docker build -t petr4-predictor .
    ```

2.  **Rodar o container:**
    ```bash
    docker run -p 8000:8000 petr4-predictor
    ```

---

## 📊 Métricas e Resultados

O modelo foi avaliado utilizando dados históricos de validação (últimos 5% do dataset), obtendo métricas consistentes para o mercado volátil de renda variável.

*   **Janela de Observação (Lookback):** 20 dias
*   **Target:** Retorno Logarítmico diário
*   **Feature Engineering:** Inclusão de Sazonalidade (Seno/Cosseno de dia e mês) e Volatilidade.

> *Nota: O dashboard exibe um nível de confiança fixo estimado de 89% baseado nos testes de validação de direção de tendência.*

---

## 📂 Estrutura de Pastas

```text
.
├── src
│   ├── api
│   │   ├── client          # Frontend (HTML/CSS/JS)
│   │   ├── endpoints       # Rotas da API (Predict)
│   │   ├── schemas         # Modelos Pydantic (Request/Response)
│   │   ├── services        # Lógica de ML e Coleta de Dados
│   │   └── main.py         # Entrypoint da aplicação
│   ├── models              # Arquivos binários (.keras, .pkl)
│   └── notebooks           # Jupyter Notebooks de estudo e treino
├── Dockerfile
├── pyproject.toml
└── README.md