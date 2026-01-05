# FIAP Tech Challenge - Fase 4: Predição de Ações com LSTM

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16-orange?style=for-the-badge&logo=tensorflow)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)

## 📄 Sobre o Projeto

Este projeto corresponde à **Fase 4** do **Tech Challenge** da Pós-Graduação em **Machine Learning Engineering** da FIAP.

O objetivo é desenvolver uma **pipeline completa de Machine Learning (End-to-End)** para prever o **preço de fechamento** das ações da **Petrobras (PETR4.SA)**, utilizando uma Rede Neural Recorrente do tipo **LSTM (Long Short-Term Memory)**, capaz de capturar dependências temporais em séries financeiras.

O projeto prioriza **transparência e interpretabilidade**, apresentando ao usuário final não apenas o valor previsto, mas também os **indicadores técnicos e macroeconômicos** que influenciam a decisão do modelo.

---

## 📓 Notebook principal do projeto

Toda a implementação do modelo de *Machine Learning* com **LSTM** — incluindo coleta de dados, pré-processamento, engenharia de features, treinamento, avaliação e validação — está documentada de forma detalhada no notebook abaixo:

➡️ [Acessar notebook comentado](./notebook/TC_FASE4.ipynb)

---

## 🎯 Funcionalidades Principais

- **Pipeline de Dados Automatizado:**  
  Coleta dados históricos e indicadores macroeconômicos, como Câmbio (USD/BRL), Petróleo Brent, B3 e Selic.

- **Engenharia de Features:**  
  Cálculo de indicadores técnicos (RSI, MACD, Bandas de Bollinger, Médias Móveis), volatilidade, retornos e correlações com ativos externos.

- **Modelo LSTM:**  
  Rede neural treinada para prever o **Retorno Logarítmico Diário**, garantindo estacionariedade e maior estabilidade numérica.

- **Dashboard Interativo:**  
  Interface web que exibe:
  - Cotação atual e dados de mercado, dispensando a entrada manual de históricos.
  - Painel de indicadores técnicos e macroeconômicos.
  - Explicação da metodologia adotada.
  - Tabela com projeções futuras de preço.

- **API RESTful:**  
  Backend desenvolvido com **FastAPI**, responsável por realizar inferência e servir o modelo treinado.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12  
- **Gerenciamento de Dependências:** Poetry  
- **Machine Learning:** TensorFlow/Keras, Scikit-learn  
- **Processamento de Dados:** Pandas, NumPy, YFinance  
- **Backend:** FastAPI, Uvicorn  
- **Frontend:** HTML5, CSS3, JavaScript  
- **Containerização:** Docker (pronto para deploy)

---

## 🧠 Arquitetura da Solução

1. **Coleta & Pré-processamento**
   - Normalização dos dados com `MinMaxScaler`
   - Criação de janelas deslizantes (*sliding windows*) de 20 dias

2. **Modelagem com LSTM**
   - Camadas LSTM empilhadas
   - Dropout para mitigação de overfitting
   - Camada Dense para regressão

3. **Avaliação**
   - Métricas utilizadas: **MAE** e **RMSE**
   - Validação com os últimos 5% do conjunto de dados

4. **Persistência**
   - Modelo salvo no formato `.keras`
   - Scalers serializados em `.pkl`

5. **Inferência via API**
   - Endpoint `/api/predict`
   - Coleta automática dos dados mais recentes
   - Retorno da previsão convertida para o valor real em reais (R$)

---

## 📊 Métricas e Resultados

- **Lookback:** 20 dias  
- **Target:** Retorno Logarítmico Diário  
- **Feature Engineering:** Sazonalidade (seno/cosseno) e volatilidade

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
```
## ⚙️ Instalação e Execução

Siga os passos abaixo para executar o projeto localmente.

### Pré-requisitos
-   [Git](https://git-scm.com/)
-   [Docker](https://www.docker.com/products/docker-desktop/)
-   [Python 3.12](https://www.python.org/) (para execução sem Docker)
-   [Poetry](https://python-poetry.org/)


### Clone o repositório e altere para o caminho raiz do projeto:
    ```bash
    git clone https://github.com/marciojolima/tc_fiap_fase4.git
    cd tc_fiap_fase4
    ```
### Opção: Poetry

Para executar a API localmente utilizando Poetry.

Certifique-se que o prompt esteja na pasta raiz do projeto

**Instale as dependências:**
    ```bash
    poetry install
    ```

**Inicie o servidor da API:**
    ```bash
    poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
    ```

### Opção 3: Pip

Certifique-se que o prompt esteja na pasta raiz do projeto

1.  **Crie um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Inicie o servidor da API:**

    ```bash
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
    ```


## Conclusão

Neste projeto, foi desenvolvida uma solução completa de *Machine Learning* para previsão de preços de ações, contemplando todas as etapas do ciclo de vida de um modelo, desde a coleta e preparação dos dados até o deploy em uma API funcional.

A utilização de redes neurais do tipo **LSTM**, aliada a uma engenharia de features robusta e à modelagem baseada em retorno logarítmico, permitiu capturar padrões temporais relevantes em um contexto de alta volatilidade, como o mercado financeiro.

Além do aspecto preditivo, o projeto também se preocupa com a **transparência e interpretabilidade**, fornecendo ao usuário final indicadores técnicos e macroeconômicos que auxiliam na compreensão das previsões geradas.

Para o futuro, destacam-se a incorporação de novas fontes de dados, o aprimoramento do monitoramento em produção e a avaliação contínua do modelo para adaptação a mudanças no regime de mercado.

## 👥 Autores

**Turma 6MELT - FIAP**

* Luca Poiti - RM365678
* Gabriel Jordan - RM365606
* Luciana Ferreira - RM366171
* Marcio Lima - RM365919