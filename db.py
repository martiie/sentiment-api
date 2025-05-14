import psycopg2

def get_connection():
    DATABASE_URL = "postgresql://phothak:NgPzzJ9npCBm0TJUHRlqH3ZyRVhGzQhn@dpg-d0i57kadbo4c73dhtlfg-a.oregon-postgres.render.com/phithak_db"
    connection = psycopg2.connect(DATABASE_URL)
    return connection
