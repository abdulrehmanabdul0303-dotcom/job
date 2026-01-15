@echo off
set PATH=C:\Users\REHMAN\AppData\Local\Programs\Python\Python311;C:\Users\REHMAN\AppData\Local\Programs\Python\Python311\Scripts;%PATH%
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
