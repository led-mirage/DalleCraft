create-version-file version.yaml --outfile version.txt
pyinstaller --onefile --noconsole --paths=./src --add-data "./src/html;html" --name DalleCraft --icon assets/app.ico --splash assets/splash.png --version-file=version.txt src/main.py
