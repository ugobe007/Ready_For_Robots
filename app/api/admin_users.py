"""
Admin User Management API
========================
Endpoints for managing users, viewing activity, and account stats.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """
    List all registered users with their activity stats.
    Returns: { users: [{ id, email, created_at, saved_count, reports_count, lists_count, last_active }] }
    """
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
            FROM user_reports 
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
            "id": row.id,
            "email": row.email,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "last_active": row.last_active.isoformat() if row.last_active else None,
            "saved_count": row.saved_count,
            "reports_count": row.reports_count,
            "lists_count": row.lists_count,
        })
    
    return {"users": users, "total": len(users)}


@router.get("/users/{user_id}/activity")
def get_user_activity(user_id: str, db: Session = Depends(get_db)):
    """
    Get detailed activity for a specific user.
    Returns: { saved_companies, reports, lists }
    """
    # Saved companies
    saved_query = text("""
        SELECT c.id, c.company_name, c.industry, usc.created_at
        FROM user_saved_companies usc
        JOIN companies c ON c.id = usc.company_id
        WHERE usc.user_id = :user_id
        ORDER BY usc.created_at DESC
        LIMIT 50
    """)
    saved_rows = db.execute(saved_query, {"user_id": user_id}).fetchall()
    saved_companies = [
        {
            "company_id": row.id,
            "name": row.company_name,
            "industry": row.industry,
            "saved_at": row.created_at.isoformat() if row.created_at else None
        }
        for row in saved_rows
    ]
    
    # Reports
    reports_query = text("""
        SELECT id, company_id, created_at
        FROM user_reports
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
        db.execute(text("DELETE FROM user_reports WHERE user_id = :user_id"), {"user_id": user_id})
        
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


@router.get("/users/stats")
def get_user_stats(db: Session = Depends(get_db)):
    """
    Get aggregate user statistics.
    Returns: { total_users, active_users, total_saved, total_reports, total_lists }
    """
    stats_query = text("""
        SELECT 
            COUNT(DISTINCT up.id) as total_users,
            COUNT(DISTINCT CASE WHEN up.updated_at > NOW() - INTERVAL '7 days' THEN up.id END) as active_users,
            COUNT(DISTINCT usc.id) as total_saved,
            COUNT(DISTINCT ur.id) as total_reports,
            COUNT(DISTINCT ul.id) as total_lists
        FROM user_profiles up
        LEFT JOIN user_saved_companies usc ON up.id = usc.user_id
        LEFT JOIN user_reports ur ON up.id = ur.user_id
        LEFT JOIN user_lists ul ON up.id = ul.user_id
    """)
    
    row = db.execute(stats_query).fetchone()
    
    return {
        "total_users": row.total_users or 0,
        "active_users": row.active_users or 0,
        "total_saved": row.total_saved or 0,
        "total_reports": row.total_reports or 0,
        "total_lists": row.total_lists or 0
    }
