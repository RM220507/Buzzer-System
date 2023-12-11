import sqlite3

db = sqlite3.connect("C:/Users/18RMitcham/OneDrive - Colyton Grammar School/A-Levels/Other/Buzzer System/buzzer.db")
cursor = db.cursor() # type: ignore

print(cursor.execute("SELECT * FROM Teams").fetchall())

db.commit() #type: ignore

db.close() # type: ignore