from flask import Flask
import os
app = Flask(__name__)


@app.route("/")
def home():
    return os.getenv('AZURE_STORAGE_KEY', 'NO KEY')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
