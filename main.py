from flask import Flask
from views import mcp


app = Flask(__name__)
app.register_blueprint(mcp)


if __name__ == "__main__":
    app.run(debug=True)
