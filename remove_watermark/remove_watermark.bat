@echo on

call C:\Kwork\SantechParser\venv\Scripts\activate.bat

call C:\Kwork\SantechParser\remove_watermark\python.exe remove_watermark.py

call C:\Kwork\SantechParser\venv\Scripts\deactivate.bat

cmd /k