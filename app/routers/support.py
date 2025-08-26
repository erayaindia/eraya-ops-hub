# app/routers/support.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import datetime as dt

router = APIRouter(prefix="/support", tags=["support"])

DEMO_PATH = Path("app/data/tickets_demo.json")

def _load_demo_tickets():
    """Load demo tickets from file if present, otherwise return a small sample."""
    if DEMO_PATH.exists():
        try:
            return json.loads(DEMO_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    now = dt.datetime.utcnow().isoformat() + "Z"
    return [
        {
            "ticket_id": "TK1001",
            "full_name": "Aarav Sharma",
            "email": "aarav@example.com",
            "channel": "Instagram DM",
            "issue_type": "Order Status",
            "summary": "Where is my order?",
            "status": "Open",
            "priority": "Normal",
            "created_at": now,
        },
        {
            "ticket_id": "TK1002",
            "full_name": "Priya Verma",
            "email": "priya@example.com",
            "channel": "WhatsApp",
            "issue_type": "Customization",
            "summary": "Change back engraving text",
            "status": "Waiting on Customer",
            "priority": "High",
            "created_at": now,
        },
    ]

@router.get("/api/tickets")
async def list_tickets():
    """
    API for the table. 
    Later you can replace _load_demo_tickets() with a real Supabase query.
    """
    return JSONResponse({"ok": True, "items": _load_demo_tickets()})

@router.get("/tickets")
async def support_tickets_page(request: Request):
    """Render the support tickets page using templates."""
    # Import the SUPPORT Supabase service client (since anon key doesn't work)
    from app.services.supa import get_support_service_client
    
    # Get templates from app state to ensure NAV_ITEMS is available
    templates = request.app.state.templates
    
    try:
        # Get the SUPPORT Supabase service client (this works!)
        support_supabase = get_support_service_client()
        supabase_url = support_supabase.supabase_url
        supabase_key = support_supabase.supabase_key
        print(f"✅ Using SUPPORT service client for support tickets")
    except Exception as e:
        print(f"Warning: Could not get SUPPORT Supabase client: {e}")
        # Fallback to AUTH project if SUPPORT fails
        from app.config import SUPABASE_URL, SUPABASE_ANON_KEY
        supabase_url = SUPABASE_URL
        supabase_key = SUPABASE_ANON_KEY
        print(f"⚠️ Falling back to AUTH project credentials")
    
    return templates.TemplateResponse(
        "support_tickets.html",
        {
            "request": request, 
            "title": "Support Tickets",
            "header": "Support Tickets",
            "supabase_url": supabase_url,
            "supabase_key": supabase_key
        }
    )
