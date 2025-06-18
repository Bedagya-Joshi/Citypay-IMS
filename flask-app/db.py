import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="citypay_ims",
        user="citypay_ims",
        password="C!typ@y123#"
    )
    return conn