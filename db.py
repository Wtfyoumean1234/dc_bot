import os
import psycopg2
from psycopg2.extras import RealDictCursor
#from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

ALLOWED_COLUMNS={"hour", "minute", "notmsg", "worktime", "endtime", "anno", "count"}

DB_URL = os.getenv("DATABASE_URL")

_conn=None

def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        if DB_URL is None:
            raise RuntimeError("DATABASE_URL not set")
        _conn=psycopg2.connect(DB_URL,cursor_factory=RealDictCursor)
    return _conn

def init_db():
    conn=get_conn()
    cur=conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usr_interval(
                usr_id BIGINT PRIMARY KEY,
                hour INTEGER NOT NULL DEFAULT 1,
                minute INTEGER NOT NULL DEFAULT 0,
                notmsg TEXT NOT NULL DEFAULT '去讀書拉小學生',
                worktime INTEGER NOT NULL DEFAULT 23,
                endtime INTEGER NOT NULL DEFAULT 8,
                anno BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
    )
    conn.commit()

def init_usr(usr_id,data):
    conn=get_conn()
    cur=conn.cursor()
    cur.execute(
        """
        INSERT INTO usr_interval (usr_id, hour, minute, notmsg, worktime, endtime, anno)
        VALUES (%(usr_id)s, %(hour)s, %(minute)s, %(notmsg)s, %(worktime)s, %(endtime)s, %(anno)s)
        """,
        {
            "usr_id":usr_id,
            **data
        }
    )
    conn.commit()

def getdata(usr_id):
    conn=get_conn()
    cur=conn.cursor()
    cur.execute("SELECT * FROM usr_interval WHERE usr_id=%s",(usr_id,))
    row=cur.fetchone()
    conn.commit()
    return row

def change_partial_data(usr_id,data:dict):
    conn=get_conn()
    cur=conn.cursor()
    cols=list()
    params=list()
    for k,v in data.items():
        if k not in ALLOWED_COLUMNS:
            raise ValueError("invalid column name")
        cols.append(f"{k}=%s")
        params.append(v)
    params.append(usr_id)
    cols=",".join(cols)
    cur.execute(f"UPDATE usr_interval SET {cols} WHERE usr_id=%s",params)
    conn.commit()

def change_all_data(usr_id,data:dict):
    conn=get_conn()
    cur=conn.cursor()
    cur.execute("UPDATE usr_interval SET hour=%(hour)s, minute=%(minute)s, notmsg=%(notmsg)s, worktime=%(worktime)s, endtime=%(endtime)s, anno=%(anno)s WHERE usr_id=%(usr_id)s",
                {"usr_id":usr_id,**data})

    conn.commit()
