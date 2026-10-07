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

DECISION_MAKER_SRC = '''
def compute_decision_maker(*, target_titles, hunter_people, locality, job_function, job_text):
    from app.services.job_decision_maker_agent import pick_candidate, plan_for_job
    people = hunter_people if isinstance(hunter_people, list) else []
    plan = plan_for_job({"action": job_function or "", "robot_compatible_task": job_text or ""})
    if target_titles:
        plan.titles = list(target_titles)
    picked = pick_candidate(plan, people, locality=locality or "")
    return picked
'''

LIBRARY = {
    "job_function": JOB_FUNCTION_SRC,
    "target_titles": TARGET_TITLES_SRC,
    "departments": DEPARTMENTS_SRC,
    "decision_maker": DECISION_MAKER_SRC,
}
