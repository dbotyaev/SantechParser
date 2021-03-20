@echo on

call C:\Kwork\SantechParser\venv\Scripts\activate.bat

call C:\Kwork\SantechParser\img_replace\python.exe img_replace.py

call C:\Kwork\SantechParser\venv\Scripts\deactivate.bat

cmd /k