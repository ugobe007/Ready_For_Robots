"""
SQLAlchemy ORM hooks: keep companies.automation_profile in sync when signals or core fields change.
"""
from __future__ import annotations

import logging

from sqlalchemy import event
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import get_history

logger = logging.getLogger(__name__)


def _refresh_company_profile(session: Session, company_id: int) -> None:
    if not company_id:
        return
    from app.models.company import Company
    from app.services.automation_profile import build_automation_profile_dict_from_company

    c = (
        session.query(Company)
        .options(joinedload(Company.signals))
        .filter(Company.id == company_id)
        .first()
    )
    if not c:
        return
    try:
        c.automation_profile = build_automation_profile_dict_from_company(c)
    except Exception as exc:
        logger.warning("Could not refresh automation_profile for company %s: %s", company_id, exc)


def _on_signal_mutate(mapper, connection, target) -> None:
    sess = Session.object_session(target)
    if sess is not None:
        _refresh_company_profile(sess, target.company_id)


def _on_company_after_insert(mapper, connection, target) -> None:
    sess = Session.object_session(target)
    if sess is not None:
        _refresh_company_profile(sess, target.id)


def _on_company_after_update(mapper, connection, target) -> None:
    # Avoid loops: only when name/industry change, not when only automation_profile is written.
    if get_history(target, "name").has_changes() or get_history(target, "industry").has_changes():
        sess = Session.object_session(target)
        if sess is not None:
            _refresh_company_profile(sess, target.id)


_events_registered = False


def register_db_events() -> None:
    global _events_registered
    if _events_registered:
        return
    _events_registered = True

    from app.models.company import Company
    from app.models.signal import Signal

    event.listen(Signal, "after_insert", _on_signal_mutate)
    event.listen(Signal, "after_update", _on_signal_mutate)
    event.listen(Signal, "after_delete", _on_signal_mutate)
    event.listen(Company, "after_insert", _on_company_after_insert)
    event.listen(Company, "after_update", _on_company_after_update)
