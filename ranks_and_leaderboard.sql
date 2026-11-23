-- Run this once in the Supabase SQL editor.

-- 1. Ranks: a player's rank comes from their overall level.
create table if not exists ranks (
  id        smallint primary key,
  name      text not null unique,
  min_level integer not null unique check (min_level >= 1)
);

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

-- 2. Leaderboard: one row per active player with total EXP, overall level,
--    rank and place. Equal EXP shares the same place.
--    The 100 below is EXP per level and must match EXP_PER_LEVEL in rules.py.
create or replace view leaderboard as
with totals as (
  select u.id as user_id,
         u.username,
         coalesce(sum(up.exp), 0)::int as total_exp
  from users u
  left join user_progress up on up.user_id = u.id
  where u.is_active
  group by u.id, u.username
),
leveled as (
  select t.*, 1 + t.total_exp / 100 as level from totals t
)
select rank() over (order by l.total_exp desc) as place,
       l.user_id,
       l.username,
       l.total_exp,
       l.level,
       r.name as rank_name
from leveled l
join lateral (
  select name from ranks
  where min_level <= l.level
  order by min_level desc
  limit 1
) r on true;

-- 3. Keep both off Supabase's public (anon) API. Only the backend reads them.
alter table ranks enable row level security;
revoke all on leaderboard from anon, authenticated;
