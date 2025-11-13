@echo off
REM Start VnCoreNLP server

set VNCORENLP_DIR=models\vncorenlp
set JAR_FILE=VnCoreNLP-1.2.jar
set PORT=9000

echo Starting VnCoreNLP server on port %PORT%...

java -Xmx2g -jar "%VNCORENLP_DIR%\%JAR_FILE%" -p %PORT% -annotators wseg

echo VnCoreNLP server stopped
pause