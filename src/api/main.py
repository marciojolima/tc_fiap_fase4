# ~/dev/projects/python/tc_fiap_fase4/src/api/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.client import routes as client_routes
from api.endpoints import predict_petr4, health

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title='Tech Challenge FIAP-6MELT - FASE4',
    description='Api para previsão de preços da ação PETR4.SA (Petrobras)',
    version='1.0.0',
)

# 1. Obtém o diretório onde este arquivo (main.py) está: .../src/api/
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Monta o caminho completo até a pasta static: .../src/api/client/static
static_path = os.path.join(script_dir, "client", "static")

# --- DEBUG: Cole isso no seu código ---
"""print("\n" + "="*30)
print(f"📍 ONDE ESTOU (main.py): {script_dir}")
print(f"📁 TENTANDO ACESSAR:    {static_path}")
print(f"✅ O DIRETORIO EXISTE?  {os.path.isdir(static_path)}")
print(f"📄 CONTEUDO DA PASTA:   {os.listdir(static_path) if os.path.isdir(static_path) else 'NÃO ENCONTRADO'}")
print("="*30 + "\n")"""
# --------------------------------------

# Montar arquivos estáticos (CSS, JS, imagens)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Incluir pagina cliente
app.include_router(client_routes.router)
# Incluir rotas da API
app.include_router(predict_petr4.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# Ativar a instrumentação
# Isso cria automaticamente o endpoint /metrics que o Prometheus vai ler
Instrumentator().instrument(app).expose(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
