from flask import Blueprint, render_template

mcp = Blueprint('main', __name__)


@mcp.route('/', methods=['GET'])
def index():
    return render_template("index.html")
