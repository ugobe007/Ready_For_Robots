/**
 * Employer MATCH/POST on `/?visit=candidates`.
 * Step 01 work → 02 named catalog robots → 03 post-job draft.
 * Cal stays on the OEM Jobs desk. Not a buyer list.
 */
import { useMemo, useState } from "react";
import { WorkClassIcon } from "@/components/SiteIcon";
import { classOptionsOrDefault } from "@/lib/robotClassOptions";
import { iconForWorkClass } from "@/lib/siteIcons";
import {
  EMPLOYER_EMPTY_MATCH,
  EMPLOYER_MATCH_CTA,
  EMPLOYER_POST_JOB_CTA,
  EMPLOYER_PROCESS_STEPS,
  EMPLOYER_WORK_TILE_IDS,
  jobsFindHref,
  type EmployerProcessStepId,
} from "@/lib/jobsLanding";
import {
  FIND_JOBS_HEADLINE_CLASS,
  JOBS_EYEBROW_CLASS,
  JOBS_FIND_CTA_CLASS,
  JOBS_PROCESS_NAV_CLASS,
} from "@/lib/jobsWorkflow";
import {
  EMPLOYER_JD_ACCEPT,
  fetchEmployerRobotMatch,
  postEmployerJobDraft,
  readEmployerJdFile,
  type EmployerJdFile,
  type EmployerMatchedRobot,
} from "@/lib/employerRobotMatch";
import {
  saveEmployerPosting,
  listEmployerPostings,
  type EmployerPosting,
} from "@/lib/employerCrm";

const WORK_TILES = classOptionsOrDefault().filter(opt =>
  (EMPLOYER_WORK_TILE_IDS as readonly string[]).includes(opt.id)
);

export default function EmployerMatchWorkspace() {
  const [step, setStep] = useState<EmployerProcessStepId>("work");
  const [workClass, setWorkClass] = useState("");
  const [description, setDescription] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [matching, setMatching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [robots, setRobots] = useState<EmployerMatchedRobot[]>([]);
  const [emptyCopy, setEmptyCopy] = useState<string | null>(null);
  const [checked, setChecked] = useState<string[]>([]);
  const [employer, setEmployer] = useState("");
  const [title, setTitle] = useState("");
  const [workplace, setWorkplace] = useState("");
  const [jd, setJd] = useState<EmployerJdFile | null>(null);
  const [posting, setPosting] = useState<EmployerPosting | null>(null);
  const [postingError, setPostingError] = useState<string | null>(null);
  const [postingBusy, setPostingBusy] = useState(false);
  const saved = useMemo(() => listEmployerPostings(), [posting]);

  async function matchRobots() {
    if (!workClass) {
      setError("Pick the kind of work.");
      return;
    }
    setMatching(true);
    setError(null);
    try {
      const res = await fetchEmployerRobotMatch({
        workClass,
        description,
        jobUrl,
      });
      setRobots(res.robots || []);
      setEmptyCopy(
        res.empty_copy || (res.robot_count ? null : EMPLOYER_EMPTY_MATCH)
      );
      setChecked((res.robots || []).map(r => `${r.vendor_name}|${r.name}`));
      setStep("robots");
    } catch {
      setError("Could not match catalog robots. Try again.");
    } finally {
      setMatching(false);
    }
  }

  async function postJob() {
    const shop = employer.trim();
    const workTitle = title.trim() || description.trim().slice(0, 120);
    if (!shop || !workTitle) {
      setPostingError(
        "Name the employer and the work. We will not invent either."
      );
      return;
    }
    setPostingBusy(true);
    setPostingError(null);
    const shortlisted = robots.filter(r =>
      checked.includes(`${r.vendor_name}|${r.name}`)
    );
    const local: EmployerPosting = {
      id: `${Date.now()}`,
      employer: shop,
      title: workTitle,
      workplace: workplace.trim() || undefined,
      description: description.trim() || jd?.text || undefined,
      work_class: workClass || undefined,
      job_url: jobUrl.trim() || undefined,
      jd_filename: jd?.filename,
      jd_text: jd?.text || undefined,
      persisted: false,
      shortlisted: shortlisted.map(r => ({
        name: r.name,
        vendor_name: r.vendor_name,
        robot_class: r.robot_class,
        vendor_url: r.vendor_url,
      })),
      posted_at: new Date().toISOString(),
    };
    try {
      const res = await postEmployerJobDraft({
        employer: shop,
        title: workTitle,
        workplace: workplace.trim(),
        description: description.trim() || jd?.text || undefined,
        workClass,
        jobUrl: jobUrl.trim(),
        jdFilename: jd?.filename,
        jdText: jd?.text || description.trim() || undefined,
        shortlisted: local.shortlisted,
      });
      local.persisted = Boolean(res.ok && res.persisted);
      local.job_key = res.job_key || null;
      if (!res.ok) {
        setPostingError(
          res.detail ||
            "Could not store this posting. Your shortlist is still here."
        );
      }
    } catch {
      setPostingError(
        "Could not store this posting. Your shortlist is still here."
      );
    }
    saveEmployerPosting(local);
    setPosting(local);
    setPostingBusy(false);
    setStep("post");
  }

  const processAction =
    step === "work"
      ? matchRobots
      : step === "robots"
        ? () => setStep("post")
        : postJob;
  const processLabel =
    step === "work"
      ? EMPLOYER_MATCH_CTA
      : step === "robots"
        ? EMPLOYER_POST_JOB_CTA
        : EMPLOYER_POST_JOB_CTA;

  return (
    <div className="rfr-jobs-page-shell border border-slate-600 bg-[#0b162f]">
      <div className="sticky top-14 z-[60] border-b border-slate-600 bg-[#0b162f]">
        <nav
          aria-label="Employer process"
          className="rfr-jobs-process-bar flex flex-wrap items-stretch"
        >
          {EMPLOYER_PROCESS_STEPS.map(item => {
            const isCurrent = step === item.id;
            return (
              <button
                key={item.id}
                type="button"
                aria-current={isCurrent ? "step" : undefined}
                onClick={() => setStep(item.id)}
                className={`flex min-w-0 flex-1 cursor-pointer items-center justify-between gap-2 px-3 py-3 text-left ${JOBS_PROCESS_NAV_CLASS} ${
                  isCurrent
                    ? "border-b-2 border-emerald-400 bg-emerald-400/5 text-emerald-300"
                    : "border-b-2 border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>
                  {item.n} {item.label}
                </span>
              </button>
            );
          })}
          <button
            type="button"
            onClick={processAction}
            disabled={matching || postingBusy}
            className={`rfr-jobs-process-action m-2 shrink-0 ${JOBS_FIND_CTA_CLASS}`}
          >
            {matching ? "Matching…" : processLabel}
          </button>
        </nav>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,0.34fr)_minmax(0,0.66fr)]">
        <aside className="border-b border-slate-600 px-6 py-6 lg:border-b-0 lg:border-r">
          <p className={JOBS_EYEBROW_CLASS}>Look for robot candidates</p>
          <h1 className={FIND_JOBS_HEADLINE_CLASS}>
            {step === "work"
              ? "What is the work?"
              : step === "robots"
                ? "Matching robots"
                : "Post the job"}
          </h1>
          <p className="mt-3 text-sm leading-snug text-slate-400">
            Named catalog robots only. We will not invent a SKU or an employer
            email.
          </p>
          <a
            href={jobsFindHref()}
            className="mt-6 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400 hover:text-slate-200"
          >
            Looking for jobs instead? Show us your robot →
          </a>
        </aside>
        <section className="min-w-0 px-6 py-6">
          {step === "work" ? (
            <form
              aria-label="Look for robot candidates"
              onSubmit={e => {
                e.preventDefault();
                void matchRobots();
              }}
            >
              <p className={JOBS_EYEBROW_CLASS}>Work</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {WORK_TILES.map(opt => (
                  <button
                    key={opt.id}
                    type="button"
                    data-employer-work={opt.id}
                    aria-pressed={workClass === opt.id}
                    onClick={() => setWorkClass(opt.id)}
                    className={`border px-3 py-3 text-left transition ${
                      workClass === opt.id
                        ? "border-emerald-400 bg-emerald-400/10"
                        : "border-slate-600 bg-[#081126] hover:border-emerald-400/60"
                    }`}
                  >
                    <span className="flex items-start gap-2">
                      {iconForWorkClass(opt.id) ? (
                        <WorkClassIcon classId={opt.id} />
                      ) : null}
                      <span className="min-w-0">
                        <span className="block font-display text-sm font-bold text-slate-100">
                          {opt.label}
                        </span>
                        <span className="mt-1 block text-[12px] leading-snug text-slate-400">
                          {opt.hint}
                        </span>
                      </span>
                    </span>
                  </button>
                ))}
              </div>
              <label
                className={`${JOBS_EYEBROW_CLASS} mt-6 block`}
                htmlFor="work-desc"
              >
                Short description (optional)
              </label>
              <textarea
                id="work-desc"
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={4}
                placeholder="What needs doing, on which site"
                className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500"
              />
              <label
                className={`${JOBS_EYEBROW_CLASS} mt-4 block`}
                htmlFor="job-url"
              >
                Job URL (optional)
              </label>
              <input
                id="job-url"
                type="text"
                value={jobUrl}
                onChange={e => setJobUrl(e.target.value)}
                placeholder="https://…"
                className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 font-mono text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500"
              />
              <label
                className={`${JOBS_EYEBROW_CLASS} mt-4 block`}
                htmlFor="work-jd"
              >
                Job description file (optional)
              </label>
              <input
                id="work-jd"
                type="file"
                accept={EMPLOYER_JD_ACCEPT}
                onChange={e => {
                  const file = e.target.files?.[0];
                  if (!file) {
                    setJd(null);
                    return;
                  }
                  void readEmployerJdFile(file).then(setJd);
                }}
                className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-sm text-slate-100 file:mr-3 file:border-0 file:bg-emerald-400 file:px-3 file:py-1 file:font-mono file:text-[11px] file:font-bold file:uppercase file:text-[#04122a]"
              />
              {jd ? (
                <p className="mt-2 text-[12px] text-emerald-200">
                  {jd.filename}
                  {jd.text
                    ? ` · ${jd.text.trim().split(/\s+/).length} words read`
                    : " · we will store the filename with the posting. Paste details below if the file is PDF or Word."}
                </p>
              ) : (
                <p className="mt-2 text-[12px] text-slate-500">
                  PDF, Word, or txt. We do not invent an employer or an email
                  from the file.
                </p>
              )}
              {error ? (
                <p className="mt-3 border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-300">
                  {error}
                </p>
              ) : null}
              <button
                type="submit"
                disabled={matching}
                className={`${JOBS_FIND_CTA_CLASS} mt-6`}
              >
                {matching ? "Matching…" : EMPLOYER_MATCH_CTA}
              </button>
            </form>
          ) : null}

          {step === "robots" ? (
            <div>
              <p className={JOBS_EYEBROW_CLASS}>
                {robots.length
                  ? `${robots.length} named catalog robots`
                  : "No catalog robots yet"}
              </p>
              {robots.length === 0 ? (
                <div className="mt-4 border border-slate-600 bg-[#081126] p-5">
                  <h2 className="font-display text-lg font-bold text-slate-100">
                    {emptyCopy || EMPLOYER_EMPTY_MATCH}
                  </h2>
                  <p className="mt-2 text-sm text-slate-400">
                    That is a coverage gap, not a reason to invent a robot. Post
                    the job so OEMs looking for work can find it.
                  </p>
                  <button
                    type="button"
                    onClick={() => setStep("post")}
                    className={`${JOBS_FIND_CTA_CLASS} mt-4`}
                  >
                    {EMPLOYER_POST_JOB_CTA}
                  </button>
                </div>
              ) : (
                <>
                  <ol className="mt-4 space-y-3">
                    {robots.map(robot => {
                      const key = `${robot.vendor_name}|${robot.name}`;
                      const on = checked.includes(key);
                      return (
                        <li
                          key={key}
                          className="border border-slate-600 bg-[#081126] px-4 py-3"
                        >
                          <label className="flex cursor-pointer items-start gap-3">
                            <input
                              type="checkbox"
                              checked={on}
                              onChange={() =>
                                setChecked(prev =>
                                  on
                                    ? prev.filter(k => k !== key)
                                    : [...prev, key]
                                )
                              }
                              className="mt-1"
                            />
                            <span>
                              <span className="block font-display text-base font-bold text-slate-100">
                                {robot.name}
                              </span>
                              <span className="mt-0.5 block text-sm text-slate-400">
                                {robot.vendor_name}
                                {robot.robot_class
                                  ? ` · ${robot.robot_class.replace(/_/g, " ")}`
                                  : ""}
                              </span>
                              {robot.description ? (
                                <span className="mt-1 block text-[13px] leading-snug text-slate-300">
                                  {robot.description}
                                </span>
                              ) : null}
                            </span>
                          </label>
                        </li>
                      );
                    })}
                  </ol>
                  <button
                    type="button"
                    onClick={() => setStep("post")}
                    className={`${JOBS_FIND_CTA_CLASS} mt-6`}
                  >
                    {EMPLOYER_POST_JOB_CTA}
                  </button>
                </>
              )}
            </div>
          ) : null}

          {step === "post" ? (
            <div>
              <p className={JOBS_EYEBROW_CLASS}>Your posting</p>
              {posting ? (
                <div className="mt-4 border border-emerald-500/30 bg-emerald-400/5 p-5">
                  <h2 className="font-display text-lg font-bold text-slate-100">
                    {posting.title}
                  </h2>
                  <p className="mt-1 text-sm text-slate-300">
                    {posting.employer}
                  </p>
                  <p className="mt-2 text-[13px] text-slate-400">
                    {posting.persisted
                      ? "Stored so OEMs looking for jobs can find it. No contact invented."
                      : postingError ||
                        "Kept on this device. Sign in later if you want it on your desk."}
                  </p>
                  {posting.jd_filename ? (
                    <p className="mt-2 text-[12px] text-emerald-200">
                      Description file: {posting.jd_filename}
                    </p>
                  ) : null}
                  {posting.shortlisted.length ? (
                    <ul className="mt-3 space-y-1 text-sm text-slate-300">
                      {posting.shortlisted.map(r => (
                        <li key={`${r.vendor_name}|${r.name}`}>
                          {r.name} · {r.vendor_name}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-3 text-sm text-slate-400">
                      No robots shortlisted. OEMs can still find the posting.
                    </p>
                  )}
                </div>
              ) : (
                <form
                  aria-label="Post the job"
                  className="mt-4"
                  onSubmit={e => {
                    e.preventDefault();
                    void postJob();
                  }}
                >
                  <label className={JOBS_EYEBROW_CLASS} htmlFor="employer-name">
                    Employer
                  </label>
                  <input
                    id="employer-name"
                    value={employer}
                    onChange={e => setEmployer(e.target.value)}
                    placeholder="Company that needs the work"
                    className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500"
                  />
                  <label
                    className={`${JOBS_EYEBROW_CLASS} mt-4 block`}
                    htmlFor="job-title"
                  >
                    Work title
                  </label>
                  <input
                    id="job-title"
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder="What the robot would do"
                    className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500"
                  />
                  <label
                    className={`${JOBS_EYEBROW_CLASS} mt-4 block`}
                    htmlFor="workplace"
                  >
                    Workplace (optional)
                  </label>
                  <input
                    id="workplace"
                    value={workplace}
                    onChange={e => setWorkplace(e.target.value)}
                    placeholder="City or site"
                    className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500"
                  />
                  <label
                    className={`${JOBS_EYEBROW_CLASS} mt-4 block`}
                    htmlFor="post-jd"
                  >
                    Job description file
                  </label>
                  <input
                    id="post-jd"
                    type="file"
                    accept={EMPLOYER_JD_ACCEPT}
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (!file) {
                        setJd(null);
                        return;
                      }
                      void readEmployerJdFile(file).then(setJd);
                    }}
                    className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-sm text-slate-100 file:mr-3 file:border-0 file:bg-emerald-400 file:px-3 file:py-1 file:font-mono file:text-[11px] file:font-bold file:uppercase file:text-[#04122a]"
                  />
                  {jd ? (
                    <p className="mt-2 text-[12px] text-emerald-200">
                      {jd.filename}
                      {jd.text ? " · text stored with this posting" : ""}
                    </p>
                  ) : (
                    <p className="mt-2 text-[12px] text-slate-500">
                      PDF, Word, or txt, plus the fields above. No invented
                      employer, no invented email.
                    </p>
                  )}
                  {postingError ? (
                    <p className="mt-3 border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-300">
                      {postingError}
                    </p>
                  ) : null}
                  <button
                    type="submit"
                    disabled={postingBusy}
                    className={`${JOBS_FIND_CTA_CLASS} mt-6`}
                  >
                    {postingBusy ? "Posting…" : EMPLOYER_POST_JOB_CTA}
                  </button>
                </form>
              )}
              {saved.length > 1 ? (
                <div className="mt-8">
                  <p className={JOBS_EYEBROW_CLASS}>Your postings</p>
                  <ul className="mt-3 space-y-2 text-sm text-slate-300">
                    {saved.map(row => (
                      <li key={row.id}>
                        {row.title} · {row.employer}
                        {row.shortlisted.length
                          ? ` · ${row.shortlisted.length} shortlisted`
                          : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
