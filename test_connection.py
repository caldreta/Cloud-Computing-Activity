from sqlalchemy import text
from database import engine

with engine.connect() as conn:
    print("Connected:", conn.execute(text("select version()")).scalar())
    print("games:", conn.execute(text("select count(*) from games")).scalar())
    print("game_modes:", conn.execute(text("select count(*) from game_modes")).scalar())
    for row in conn.execute(text("select id, name, title from characters order by id limit 3")):
        print(row)