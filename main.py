from flask import Flask
from views import mcp


app = Flask(__name__)
app.secret_key = 'wangyun777444'
app.register_blueprint(mcp)


if __name__ == "__main__":
    app.run(debug=True)
