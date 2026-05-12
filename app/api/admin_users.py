"""
Admin User Management API
========================
Endpoints for managing users, viewing activity, and account stats.
Requires admin (email in ADMIN_EMAILS).
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from app.database import get_db
from app.api.auth_deps import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


def _iso(value):
    return value.isoformat() if value else None


def _table_exists(db: Session, table_name: str) -> bool:
    return table_name in inspect(db.bind).get_table_names()


def _seven_day_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=7)


@router.get("/users/stats")
def get_user_stats(db: Session = Depends(get_db)):
    """
    Get aggregate user statistics.
    Returns: { total_users, active_users, total_saved, total_reports, total_lists }
    """
    if not _table_exists(db, "user_profiles"):
        return {
            "total_users": 0,
            "active_users": 0,
            "total_saved": 0,
            "total_reports": 0,
            "total_lists": 0,
            "waitlist_signups": 0,
            "newsletter_subscribers": 0,
        }

    cutoff = _seven_day_cutoff()
    total_users = db.execute(text("SELECT COUNT(*) FROM user_profiles")).scalar() or 0
    active_users = db.execute(
        text("""
            SELECT COUNT(*)
            FROM user_profiles
            WHERE COALESCE(updated_at, created_at) >= :cutoff
        """),
        {"cutoff": cutoff},
    ).scalar() or 0

    def count_table(table_name: str) -> int:
        if not _table_exists(db, table_name):
            return 0
        return db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_saved": count_table("user_saved_companies"),
        "total_reports": count_table("ai_reports"),
        "total_lists": count_table("user_lists"),
        "waitlist_signups": count_table("waitlist_signups"),
        "newsletter_subscribers": count_table("newsletter_subscribers"),
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """
    List all registered users with their activity stats.
    Returns: { users: [{ id, email, created_at, saved_count, reports_count, lists_count, last_active }] }
    """
    if not _table_exists(db, "user_profiles"):
        return {"users": [], "total": 0}

    query = text("""
        SELECT 
            up.id,
            up.email,
            up.created_at,
            up.updated_at as last_active,
            COALESCE(saved.count, 0) as saved_count,
            COALESCE(reports.count, 0) as reports_count,
            COALESCE(lists.count, 0) as lists_count
        FROM user_profiles up
        LEFT JOIN (
            SELECT user_id, COUNT(*) as count 
            FROM user_saved_companies 
            GROUP BY user_id
        ) saved ON up.id = saved.user_id
        LEFT JOIN (
            SELECT user_id, COUNT(*) as count 
            FROM ai_reports 
            GROUP BY user_id
        ) reports ON up.id = reports.user_id
        LEFT JOIN (
            SELECT user_id, COUNT(*) as count 
            FROM user_lists 
            GROUP BY user_id
        ) lists ON up.id = lists.user_id
        ORDER BY up.created_at DESC
    """)
    
    rows = db.execute(query).fetchall()
    
    users = []
    for row in rows:
        users.append({
            "id": str(row.id),
            "email": row.email,
            "created_at": _iso(row.created_at),
            "last_active": _iso(row.last_active),
            "saved_count": row.saved_count,
            "reports_count": row.reports_count,
            "lists_count": row.lists_count,
        })
    
    return {"users": users, "total": len(users)}


@router.get("/activity")
def list_recent_activity(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Recent user and site activity across user tables, lead captures, and newsletter signups.
    """
    activity = []

    if _table_exists(db, "user_profiles"):
        rows = db.execute(
            text("""
                SELECT id, email, created_at
                FROM user_profiles
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
        activity.extend({
            "type": "user_signup",
            "label": "User signed up",
            "actor": row.email or "Unknown user",
            "detail": str(row.id),
            "created_at": _iso(row.created_at),
        } for row in rows)

    if _table_exists(db, "user_saved_companies"):
        rows = db.execute(
            text("""
                SELECT user_id, company_name, industry, saved_at
                FROM user_saved_companies
                ORDER BY saved_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
        activity.extend({
            "type": "saved_company",
            "label": "Saved company",
            "actor": str(row.user_id),
            "detail": f"{row.company_name or 'Company'} · {row.industry or 'Unknown'}",
            "created_at": _iso(row.saved_at),
        } for row in rows)

    if _table_exists(db, "ai_reports"):
        rows = db.execute(
            text("""
                SELECT user_id, company_name, title, created_at
                FROM ai_reports
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
        activity.extend({
            "type": "ai_report",
            "label": "Generated report",
            "actor": str(row.user_id),
            "detail": row.title or row.company_name or "AI report",
            "created_at": _iso(row.created_at),
        } for row in rows)

    if _table_exists(db, "user_lists"):
        rows = db.execute(
            text("""
                SELECT user_id, name, created_at
                FROM user_lists
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
        activity.extend({
            "type": "user_list",
            "label": "Created list",
            "actor": str(row.user_id),
            "detail": row.name or "User list",
            "created_at": _iso(row.created_at),
        } for row in rows)

    if _table_exists(db, "waitlist_signups"):
        rows = db.execute(
            text("""
                SELECT email, company, source, created_at
                FROM waitlist_signups
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
        activity.extend({
            "type": "waitlist_signup",
            "label": "SCOUT signup",
            "actor": row.email,
            "detail": row.company or row.source or "Waitlist",
            "created_at": _iso(row.created_at),
        } for row in rows)

    if _table_exists(db, "newsletter_subscribers"):
        rows = db.execute(
            text("""
                SELECT email, company, source, created_at
                FROM newsletter_subscribers
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
        activity.extend({
            "type": "newsletter_subscriber",
            "label": "Newsletter subscriber",
            "actor": row.email,
            "detail": row.company or row.source or "Robot Intelligence Brief",
            "created_at": _iso(row.created_at),
        } for row in rows)

    activity.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {"activity": activity[:limit], "total": len(activity)}


@router.get("/users/{user_id}/activity")
def get_user_activity(user_id: str, db: Session = Depends(get_db)):
    """
    Get detailed activity for a specific user.
    Returns: { saved_companies, reports, lists }
    """
    # Saved companies (user_saved_companies has company_id, company_name, industry)
    saved_query = text("""
        SELECT company_id, company_name, industry, saved_at
        FROM user_saved_companies
        WHERE user_id = :user_id
        ORDER BY saved_at DESC
        LIMIT 50
    """)
    saved_rows = db.execute(saved_query, {"user_id": user_id}).fetchall()
    saved_companies = [
        {
            "company_id": row.company_id,
            "name": row.company_name,
            "industry": row.industry,
            "saved_at": row.saved_at.isoformat() if row.saved_at else None
        }
        for row in saved_rows
    ]
    
    # Reports
    reports_query = text("""
        SELECT id, company_id, created_at
        FROM ai_reports
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 50
    """)
    reports_rows = db.execute(reports_query, {"user_id": user_id}).fetchall()
    reports = [
        {
            "id": row.id,
            "company_id": row.company_id,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        for row in reports_rows
    ]
    
    # Lists
    lists_query = text("""
        SELECT id, name, description, created_at
        FROM user_lists
        WHERE user_id = :user_id
        ORDER BY created_at DESC
    """)
    lists_rows = db.execute(lists_query, {"user_id": user_id}).fetchall()
    lists = [
        {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        for row in lists_rows
    ]
    
    return {
        "saved_companies": saved_companies,
        "reports": reports,
        "lists": lists
    }


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    Delete a user and all their data (saved companies, reports, lists).
    WARNING: This is permanent and cannot be undone.
    """
    try:
        # Delete user's saved companies
        db.execute(text("DELETE FROM user_saved_companies WHERE user_id = :user_id"), {"user_id": user_id})
        
        # Delete user's reports
        db.execute(text("DELETE FROM ai_reports WHERE user_id = :user_id"), {"user_id": user_id})
        
        # Delete user's list companies first
        db.execute(text("""
            DELETE FROM user_list_companies 
            WHERE list_id IN (SELECT id FROM user_lists WHERE user_id = :user_id)
        """), {"user_id": user_id})
        
        # Delete user's lists
        db.execute(text("DELETE FROM user_lists WHERE user_id = :user_id"), {"user_id": user_id})
        
        # Delete user profile
        db.execute(text("DELETE FROM user_profiles WHERE id = :user_id"), {"user_id": user_id})
        
        db.commit()
        
        return {"status": "success", "message": f"User {user_id} and all data deleted"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}


