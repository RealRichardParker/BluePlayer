from flask import Flask, render_template, flash, redirect, request
import os

app = Flask(__name__)

music = ['music', 'test']
ALLOWED_EXTENSIONS= set(['mp3'])
AZURE_STORAGE_KEY = os.environ['AZURE_STORAGE_KEY']


@app.route("/")
def home():
    return render_template("index.html", data=music)

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            print("no file selected!")
            return redirect(request.url)
        else:
            print(file.filename)
    return render_template("index.html", data=music)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
