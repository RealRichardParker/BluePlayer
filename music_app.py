from flask import Flask, request, render_template
import os
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", data=os.getenv('AZURE_STORAGE_KEY', 'NO KEY'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
