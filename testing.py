import sqlite3

db = sqlite3.connect("buzzer.db")

cursor = db.cursor()
cursor.execute("SELECT * FROM ColorPalette WHERE ID=15")
print(cursor.fetchone())