from flask import Flask
from threading import Thread
import os

app=Flask('')

@app.route('/')
def main():
    return '<h1>Bot is awake</h1>'

def run():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","10000")))

def keep_alive():
    server=Thread(target=run)
    server.start()