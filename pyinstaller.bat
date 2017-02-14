
pyinstaller.exe --onefile --clean --name=SVS --noconsole --key=ChangeCipherSp.c --icon=xinghan.ico --version-file=versionfile.py main.py

copy /Y .\config.ini .\dist\config.ini

rmdir /S /Q .\dist\html
rmdir /S /Q .\dist\testsuites

mkdir .\dist\html
mkdir .\dist\testsuites
copy  .\testsuites\*.* .\dist\testsuites\

