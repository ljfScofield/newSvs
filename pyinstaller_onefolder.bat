
pyinstaller.exe --clean --name=SVS --noconsole --key=ChangeCipherSp.c --icon=xinghan.ico --version-file=versionfile.py main.py

copy /Y .\config.ini .\dist\SVS\config.ini

rmdir /S /Q .\dist\SVS\doc
rmdir /S /Q .\dist\SVS\html
rmdir /S /Q .\dist\SVS\testsuites

mkdir .\dist\SVS\doc
mkdir .\dist\SVS\html
mkdir .\dist\SVS\testsuites

copy  .\doc\*.* .\dist\SVS\doc\
copy  .\testsuites\*.* .\dist\SVS\testsuites\

