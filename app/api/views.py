"""
Frontend View Routes

Server-side rendered pages using Jinja2 templates.
All pages use the premium dark theme UI.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import os

# Set up templates directory
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

view_router = APIRouter()


@view_router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Main dashboard page.
    Shows portfolio overview, recent transactions, and active policies.
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "active_page": "dashboard"}
    )


@view_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Login page.
    Handles authentication via OAuth2 password flow.
    """
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@view_router.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request):
    """
    Portfolio page.
    Shows multi-chain asset breakdown and wallet addresses.
    """
    return templates.TemplateResponse(
        "portfolio.html",
        {"request": request, "active_page": "portfolio"}
    )


@view_router.get("/transactions", response_class=HTMLResponse)
async def transactions(request: Request):
    """
    Transactions page.
    Shows transaction history and allows creating new transactions.
    """
    return templates.TemplateResponse(
        "transactions.html",
        {"request": request, "active_page": "transactions"}
    )


@view_router.get("/policies", response_class=HTMLResponse)
async def policies(request: Request):
    """
    Policies page.
    Manage transaction rules and security policies.
    """
    return templates.TemplateResponse(
        "policies.html",
        {"request": request, "active_page": "policies"}
    )


@view_router.get("/concierge", response_class=HTMLResponse)
async def concierge(request: Request):
    """
    AI Concierge page.
    Chat interface for AI-powered crypto assistance.
    """
    return templates.TemplateResponse(
        "concierge.html",
        {"request": request, "active_page": "concierge"}
    )


@view_router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """
    Settings page.
    Security configuration, MPC status, inheritance, guardians.
    """
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "active_page": "settings"}
    )
