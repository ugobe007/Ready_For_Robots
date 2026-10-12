-- Delete guard for Robot Jobs data.  Run once in the Supabase SQL editor.
--
-- Why: on 2026-10-11 an agent-written cleanup script deleted ~14,500 rows from
-- robot_jobs (and job_evidence by cascade) with no archive and no undo.
--
-- What this does:
--   1. ARCHIVE  — every deleted row from robot_jobs / job_evidence /
--                 robot_job_matches / signals / companies is copied (as JSON)
--                 into rfr_deleted_rows before it disappears.
--   2. BRAKE    — a single statement may not delete more than 200 rows from
--                 robot_jobs or signals, or 50 from companies, unless the
--                 session explicitly opts in:
--                     begin;
--                     set local rfr.allow_bulk_delete = 'on';
--                     delete from robot_jobs where ...;
--                     commit;
--                 An agent running a "cleanup" script gets an error instead of a wipe.
--   3. UNDO     — select restore_deleted_robot_jobs();  puts archived jobs back.
--
-- Safe to re-run.

create table if not exists rfr_deleted_rows (
    id           bigserial primary key,
    table_name   text        not null,
    row_pk       text        not null,
    row_data     jsonb       not null,
    deleted_at   timestamptz not null default now(),
    deleted_by   text        not null default current_user,
    app_name     text        default current_setting('application_name', true),
    restored_at  timestamptz
);
create index if not exists rfr_deleted_rows_table_idx on rfr_deleted_rows (table_name, deleted_at desc);
create index if not exists rfr_deleted_rows_open_idx on rfr_deleted_rows (table_name) where restored_at is null;

-- 1. ARCHIVE (row-level, BEFORE delete so cascades are captured too)
create or replace function rfr_archive_deleted_row() returns trigger
language plpgsql as $$
begin
    insert into rfr_deleted_rows (table_name, row_pk, row_data)
    values (tg_table_name, coalesce(to_jsonb(old)->>'id', ''), to_jsonb(old));
    return old;
end $$;

-- 2. BRAKE (statement-level, AFTER delete; raising rolls the whole statement back)
create or replace function rfr_bulk_delete_brake() returns trigger
language plpgsql as $$
declare
    n     bigint;
    limit_rows bigint := coalesce(nullif(tg_argv[0], '')::bigint, 200);
begin
    select count(*) into n from deleted_rows;
    if n > limit_rows and coalesce(current_setting('rfr.allow_bulk_delete', true), '') <> 'on' then
        raise exception
            'rfr delete guard: refusing to delete % rows from % in one statement (limit %). '
            'If this is intentional: begin; set local rfr.allow_bulk_delete = ''on''; <delete>; commit;',
            n, tg_table_name, limit_rows
            using errcode = 'P0001';
    end if;
    return null;
end $$;

do $$
declare
    t text;
    lim text;
begin
    foreach t in array array['robot_jobs', 'job_evidence', 'robot_job_matches', 'signals', 'companies'] loop
        if to_regclass('public.' || t) is null then
            raise notice 'skip %: table not found', t;
            continue;
        end if;
        execute format('drop trigger if exists rfr_archive_on_delete on %I', t);
        execute format(
            'create trigger rfr_archive_on_delete before delete on %I '
            'for each row execute function rfr_archive_deleted_row()', t);

        lim := case t when 'companies' then '50' when 'job_evidence' then '2000'
                      when 'robot_job_matches' then '5000' else '200' end;
        execute format('drop trigger if exists rfr_bulk_delete_brake on %I', t);
        execute format(
            'create trigger rfr_bulk_delete_brake after delete on %I '
            'referencing old table as deleted_rows for each statement '
            'execute function rfr_bulk_delete_brake(%L)', t, lim);
    end loop;
end $$;

-- 3. UNDO
create or replace function restore_deleted_robot_jobs(since timestamptz default now() - interval '30 days')
returns bigint language plpgsql as $$
declare
    restored bigint := 0;
    n bigint;
begin
    insert into robot_jobs
    select (jsonb_populate_record(null::robot_jobs, d.row_data)).*
    from rfr_deleted_rows d
    where d.table_name = 'robot_jobs' and d.restored_at is null and d.deleted_at >= since
    on conflict (job_key) do nothing;
    get diagnostics restored = row_count;

    insert into job_evidence
    select (jsonb_populate_record(null::job_evidence, d.row_data)).*
    from rfr_deleted_rows d
    where d.table_name = 'job_evidence' and d.restored_at is null and d.deleted_at >= since
      and (d.row_data->>'robot_job_id' is null
           or exists (select 1 from robot_jobs r where r.id = (d.row_data->>'robot_job_id')::uuid))
    on conflict (id) do nothing;
    get diagnostics n = row_count;
    raise notice 'restored % robot_jobs, % job_evidence', restored, n;

    update rfr_deleted_rows set restored_at = now()
    where table_name in ('robot_jobs', 'job_evidence') and restored_at is null and deleted_at >= since;
    return restored;
end $$;

-- Check:  select table_name, count(*) from rfr_deleted_rows group by 1;
