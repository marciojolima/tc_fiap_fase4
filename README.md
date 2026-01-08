# FIAP Tech Challenge - Fase 4: Predição de Ações com LSTM

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16-orange?style=for-the-badge&logo=tensorflow)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)

## 📄 Sobre o Projeto

Este projeto corresponde à **Fase 4** do **Tech Challenge** da Pós-Graduação em **Machine Learning Engineering** da FIAP.

O objetivo é desenvolver uma **pipeline completa de Machine Learning (End-to-End)** para prever o **preço de fechamento** das ações da **Petrobras (PETR4.SA)**, utilizando uma Rede Neural Recorrente do tipo **LSTM (Long Short-Term Memory)**, capaz de capturar dependências temporais em séries financeiras.

O projeto prioriza **transparência e interpretabilidade**, apresentando ao usuário final não apenas o valor previsto, mas também os **indicadores técnicos e macroeconômicos** que influenciam a decisão do modelo.

## 📑 Tabela de Conteúdo

- [Notebook Principal](#-notebook-principal-do-projeto)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Tecnologias Utilizadas](#️-tecnologias-utilizadas)
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Métricas e Resultados](#-métricas-e-resultados)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Instalação e Execução](#️-instalação-e-execução)
- [Como Acessar a Aplicação](#como-acessar-a-aplicação)
- [Monitoramento e Observabilidade](#-monitoramento-e-observabilidade)
- [Conclusão](#conclusão)
- [Autores](#-autores)

---

## 📓 Notebook Principal do Projeto

Toda a implementação do modelo de *Machine Learning* com **LSTM** — incluindo coleta de dados, pré-processamento, engenharia de features, treinamento, avaliação e validação — está documentada de forma detalhada no notebook abaixo:

➡️ [Acessar notebook comentado](./notebook/TC_FASE4.ipynb)

---

## 🎯 Funcionalidades Principais

- **Pipeline de Dados Automatizado:**  
  Coleta dados históricos e indicadores macroeconômicos, como Câmbio (USD/BRL), Petróleo Brent, Ibovespa e Selic.

- **Engenharia de Features:**  
  Cálculo de indicadores técnicos (RSI, MACD, Bandas de Bollinger, Médias Móveis), volatilidade, retornos e correlações com ativos externos.

- **Modelo LSTM:**  
  Rede neural treinada para prever o **Retorno Logarítmico Diário**, garantindo estacionariedade e maior estabilidade numérica.

- **Dashboard Interativo:**  
  Interface web que exibe:
  - Cotação atual e dados de mercado (sem necessidade de entrada manual de históricos).
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
- **Processamento de Dados:** Pandas, NumPy, yfinance  
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
-   [Python 3.12](https://www.python.org/) exatamente esta versão para compatibilidade com o treino do modelo
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

### Opção: Pip

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

3.  **Instale o projeto:**
```bash
pip install -e .
```

4.  **Inicie o servidor da API:**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Opção: Docker

Certifique-se que o prompt esteja na pasta raiz do projeto

1.  **Inicie o container**
```bash
docker compose up --build
```

2.  **Abra o navegador e digite na barra de endereços**
```bash
http://localhost:8000
```

---

## 📈 Monitoramento e Observabilidade

Para garantir a confiabilidade e escalabilidade do modelo em produção, o projeto implementa uma stack completa de monitoramento baseada em **Prometheus** (coleta de métricas) e **Grafana** (visualização).

A solução monitora tanto a saúde da infraestrutura (latência, throughput) quanto a performance do modelo de Machine Learning (drift de preço, confiança e viés).

### 🛠️ Acessando a Stack de Monitoramento

Uma vez que os containers estejam rodando (`docker-compose up`), os serviços estarão disponíveis nas seguintes portas:

| Serviço | URL | Descrição | Credenciais Padrão |
| :--- | :--- | :--- | :--- |
| **API Swagger** | `http://localhost:8000/docs` | Interface para testar o modelo e gerar tráfego. | N/A |
| **Prometheus** | `http://localhost:9090` | Banco de dados de séries temporais e explorador de métricas. | N/A |
| **Grafana** | `http://localhost:3000` | Dashboards visuais para análise de MLOps. | `admin` / `admin` |

---

### 🚀 Guia de Validação do Monitoramento

Como o ambiente é iniciado "limpo", é necessário gerar tráfego para que as métricas sejam populadas. Siga o fluxo abaixo para validar a observabilidade:

#### 1. Simulação de Carga (Geração de Dados)
O Prometheus coleta dados baseados em eventos. Para visualizar gráficos, é necessário realizar inferências na API.
1. Acesse o **Swagger UI** (`http://localhost:8000/docs`).
2. Utilize o endpoint `POST /api/predict`.
3. Clique em **Try it out** e depois em **Execute** repetidas vezes (sugere-se 10 a 20 requisições variando ou não os parâmetros).
   > *Isso gerará o histórico necessário para alimentar os histogramas e contadores de MLOps.*

#### 2. Verificação da Coleta (Prometheus)
Para garantir que a API está exportando as métricas corretamente:
1. Acesse o **Prometheus** (`http://localhost:9090`).
2. Na barra de busca, digite a métrica de negócio: `model_last_confidence_score`.
3. Clique em **Execute**.
   > *Se um valor (ex: 0.55) for retornado, a comunicação entre os containers está ativa.*

#### 3. Visualização (Grafana)
Para criar ou visualizar os Dashboards de performance:
1. Acesse o **Grafana** (`http://localhost:3000`) e faça login (`admin`/`admin`).
2. Adicione a fonte de dados (**Data Source**):
   * Selecione **Prometheus**.
   * **Connection URL:** Utilize o endereço interno da rede Docker: `http://prometheus:9090` (Não use localhost aqui).
   * Clique em **Save & Test**.
3. Crie um novo Dashboard e adicione painéis utilizando as métricas listadas abaixo.

---

### 📊 Métricas Customizadas de Negócio

Além das métricas padrão de HTTP, o modelo expõe as seguintes métricas de MLOps para rastreamento de performance e deriva (Drift):

| Métrica | Tipo | Descrição | Uso no Grafana |
| :--- | :--- | :--- | :--- |
| `model_prediction_price_brl` | **Histogram** | Distribuição dos preços previstos (R$). | Monitorar **Model Drift** (Se a distribuição mudar drasticamente, o modelo pode estar descalibrado). |
| `model_last_confidence_score` | **Gauge** | Nível de confiança da última inferência. | Alertar se a confiança média cair abaixo de um limiar seguro. |
| `model_prediction_direction_total` | **Counter** | Contagem de previsões de "Alta" vs "Baixa". | Identificar **Viés (Bias)** do modelo (ex: modelo só prevê alta). |
| `model_input_current_price` | **Gauge** | Preço real do ativo no momento da requisição. | Comparar em um gráfico de linha: *Preço Real (Input)* vs *Preço Previsto (Output)*. |


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