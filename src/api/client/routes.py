# ~/dev/projects/python/tc_fiap_fase4/src/api/client/routes.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# Configurar templates
templates = Jinja2Templates(directory="src/api/client/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Página inicial do cliente
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "titulo": "Tech Challenge FIAP - Previsão PETR4",
            "ano": 2024
        }
    )

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """
    Página sobre o projeto
    """
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "titulo": "Sobre o Projeto"
        }
    )