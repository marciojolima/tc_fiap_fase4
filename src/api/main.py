# ~/dev/projects/python/tc_fiap_fase4/src/api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.endpoints import predict_petr4
from api.client import routes as client_routes

app = FastAPI(
    title='Tech Challenge FIAP-6MELT - FASE4',
    description='Api para previsão de preços da ação PETR4.SA (Petrobras)',
    version='1.0.0',
)

# Montar arquivos estáticos (CSS, JS, imagens)
app.mount("/static", StaticFiles(directory="src/api/client/static"), name="static")

# Incluir rotas da API
app.include_router(predict_petr4.router, prefix="/api", tags=["Predição"])

# Incluir rotas do cliente (front-end)
app.include_router(client_routes.router, tags=["Cliente"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)