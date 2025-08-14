from flask import Flask
from views import atgent


app = Flask(__name__)
app.secret_key = 'atgent'
app.register_blueprint(atgent)


if __name__ == "__main__":
    app.run()
