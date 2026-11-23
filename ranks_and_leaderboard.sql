-- Run this once in the Supabase SQL editor. It is safe to run again.
--
-- How the tables connect:
--   ranks (name, min_level, image)
--     ^  users.rank_id  (foreign key)
--   users (total_exp, rank_id)       <- kept up to date by triggers
--     ^  user_progress.user_id       (one row per game mode, holds the EXP)
-- Whenever user_progress changes, the database adds the EXP up, stores it in
-- users.total_exp and stores the matching rank in users.rank_id.
-- Changing a rank's min_level re-ranks every player automatically.
-- The API and the website only read the result. Nothing is worked out in the browser.

-- ============ 1. RANKS ============
create table if not exists ranks (
  id        smallint primary key,
  name      text not null unique,
  min_level integer not null unique check (min_level >= 1),
  image     text                      -- file in the site's images/ folder, e.g. 'ranks/iron.png'
);
alter table ranks add column if not exists image text;

insert into ranks (id, name, min_level) values
  (1,  'Iron',        1),
  (2,  'Bronze',      11),
  (3,  'Silver',      16),
  (4,  'Gold',        21),
  (5,  'Platinum',    26),
  (6,  'Emerald',     31),
  (7,  'Diamond',     36),
  (8,  'Master',      41),
  (9,  'Grandmaster', 46),
  (10, 'Challenger',  51)
on conflict (id) do update
  set name = excluded.name, min_level = excluded.min_level;

-- ============ 2. ADMIN ROLE (used by admin.py) ============
alter table users add column if not exists role text not null default 'user';
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'users_role_check') then
    alter table users add constraint users_role_check check (role in ('user', 'admin'));
  end if;
end $$;

-- ============ 3. FAVORITE CHAMPIONS (used by favorites.py) ============
create table if not exists user_character_stats (
  user_id         integer not null references users(id) on delete cascade,
  character_id    integer not null references characters(id) on delete cascade,
  times_correct   integer not null default 0 check (times_correct >= 0),
  last_correct_at timestamptz not null default now(),
  primary key (user_id, character_id)
);

-- ============ 4. USERS -> RANKS LINK ============
alter table users add column if not exists total_exp integer not null default 0 check (total_exp >= 0);
alter table users add column if not exists rank_id smallint references ranks(id);

-- The rank for an amount of EXP: the highest rank whose min_level has been reached.
-- The 100 is EXP per level and must match EXP_PER_LEVEL in rules.py.
create or replace function rank_id_for_exp(p_total_exp integer)
returns smallint language sql stable as $$
  select id from ranks
  where min_level <= 1 + p_total_exp / 100
  order by min_level desc
  limit 1
$$;

-- Adds up a player's EXP and stores it with their rank.
create or replace function refresh_user_standing(p_user_id bigint)
returns void language plpgsql as $$
declare
  t integer;
begin
  select coalesce(sum(exp), 0) into t from user_progress where user_id = p_user_id;
  update users set total_exp = t, rank_id = rank_id_for_exp(t) where id = p_user_id;
end $$;

-- When a player's EXP changes, refresh their standing.
create or replace function trg_progress_changed()
returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then
    perform refresh_user_standing(old.user_id);
  else
    perform refresh_user_standing(new.user_id);
  end if;
  return null;
end $$;

drop trigger if exists user_progress_standing on user_progress;
create trigger user_progress_standing
  after insert or update or delete on user_progress
  for each row execute function trg_progress_changed();

-- New accounts start in the lowest rank.
create or replace function trg_user_default_rank()
returns trigger language plpgsql as $$
begin
  if new.rank_id is null then
    new.rank_id := rank_id_for_exp(coalesce(new.total_exp, 0));
  end if;
  return new;
end $$;

drop trigger if exists user_default_rank on users;
create trigger user_default_rank
  before insert on users
  for each row execute function trg_user_default_rank();

-- Editing the ranks table (a new threshold, a new rank) re-ranks everyone.
create or replace function trg_ranks_changed()
returns trigger language plpgsql as $$
begin
  update users set rank_id = rank_id_for_exp(total_exp);
  return null;
end $$;

drop trigger if exists ranks_rerank on ranks;
create trigger ranks_rerank
  after insert or update of min_level or delete on ranks
  for each statement execute function trg_ranks_changed();

-- Fill in total_exp and rank_id for every existing account.
select refresh_user_standing(id) from users;
alter table users alter column rank_id set not null;

-- ============ 5. LEADERBOARD VIEW ============
-- One row per active player, ranked by EXP. Equal EXP shares the same place.
drop view if exists leaderboard;
create view leaderboard as
select rank() over (order by u.total_exp desc) as place,
       u.id           as user_id,
       u.username,
       u.total_exp,
       1 + u.total_exp / 100 as level,
       r.name         as rank_name,
       r.image        as rank_image,
       nx.name        as next_rank_name,
       nx.min_level   as next_rank_level
from users u
join ranks r on r.id = u.rank_id
left join lateral (
  select name, min_level from ranks
  where min_level > r.min_level
  order by min_level
  limit 1
) nx on true
where u.is_active;

-- ============ 6. KEEP NEW OBJECTS OFF SUPABASE'S PUBLIC API ============
alter table ranks enable row level security;
alter table user_character_stats enable row level security;
revoke all on leaderboard from anon, authenticated;

-- ============ 7. RANK IMAGES (run after you add the files to images/ranks/) ============
-- Change the file names to match yours.
-- update ranks set image = 'ranks/' || lower(name) || '.png';
