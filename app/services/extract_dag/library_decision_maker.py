"""Reviewed deterministic functions for the job decision-maker graph.

These are the functions a writer model would emit and a reviewer would
accept. Runtime is code, not a chat completion. Names are never invented.
"""

JOB_FUNCTION_SRC = '''
def compute_job_function(*, job_text, action):
    from app.services.job_decision_maker_agent import function_for_job
    return function_for_job({"action": action or "", "robot_compatible_task": job_text or ""})
'''

TARGET_TITLES_SRC = '''
def compute_target_titles(*, job_function, job_text):
    from app.services.job_decision_maker_agent import plan_for_job
    plan = plan_for_job({"action": job_function or "", "robot_compatible_task": job_text or ""})
    return list(plan.titles)
'''

DEPARTMENTS_SRC = '''
def compute_departments(*, job_function):
    from app.services.job_decision_maker_agent import hunter_departments_for_function
    return hunter_departments_for_function(job_function or "operations")
'''

PAGE_PERSON_SRC = '''
def compute_page_person(*, page_name, page_title):
    name = (page_name or "").strip()
    if not name:
        return None
    return {
        "name": name,
        "title": (page_title or "").strip(),
        "source": "page",
        "confidence": 99,
    }
'''

LEADERSHIP_PEOPLE_SRC = '''
def compute_leadership_people(*, leadership_pages):
    from app.services.employer_leadership import people_from_pages
    pages = leadership_pages if isinstance(leadership_pages, list) else []
    return people_from_pages(pages)
'''

LEADERSHIP_PERSON_SRC = '''
def compute_leadership_person(*, leadership_people, target_titles, locality, job_function, job_text):
    from app.services.job_decision_maker_agent import pick_candidate, plan_for_job
    plan = plan_for_job({"action": job_function or "", "robot_compatible_task": job_text or ""})
    if target_titles:
        plan.titles = list(target_titles)
    people = leadership_people if isinstance(leadership_people, list) else []
    picked = pick_candidate(plan, people, locality=locality or "")
    if not picked:
        return None
    return picked
'''

DECISION_MAKER_SRC = '''
def compute_decision_maker(*, target_titles, hunter_people, page_person, leadership_person, locality, job_function, job_text):
    from app.services.job_decision_maker_agent import pick_candidate, plan_for_job, score_candidate
    plan = plan_for_job({"action": job_function or "", "robot_compatible_task": job_text or ""})
    if target_titles:
        plan.titles = list(target_titles)
    if isinstance(page_person, dict) and page_person.get("name"):
        ranked = score_candidate(plan, page_person, locality=locality or "")
        if ranked:
            picked = dict(page_person)
            picked["match_score"] = ranked[0]
            picked["match_why"] = ranked[1]
            picked["target_titles"] = list(plan.titles)
            picked["job_function"] = plan.function
            return picked
    if isinstance(leadership_person, dict) and leadership_person.get("name"):
        return leadership_person
    people = hunter_people if isinstance(hunter_people, list) else []
    picked = pick_candidate(plan, people, locality=locality or "")
    if not picked:
        return None
    return picked
'''

LIBRARY = {
    "job_function": JOB_FUNCTION_SRC,
    "target_titles": TARGET_TITLES_SRC,
    "departments": DEPARTMENTS_SRC,
    "page_person": PAGE_PERSON_SRC,
    "leadership_people": LEADERSHIP_PEOPLE_SRC,
    "leadership_person": LEADERSHIP_PERSON_SRC,
    "decision_maker": DECISION_MAKER_SRC,
}
