import asyncio
import threading
from flask import Blueprint, render_template, jsonify, session, request

from client import MCPClient


atgent = Blueprint('atgent', __name__)
sessions = {}
_loop = None
_thread_loop = None


def get_event_loop():
    global _loop, _thread_loop
    if _loop is None or _loop.is_closed():

        def run_loop():
            global _loop
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            _loop.run_forever()

        _loop_thread = threading.Thread(target=run_loop, daemon=True)
        _loop_thread.start()

        while _loop is None:
            pass

    return _loop


def run_async(coro):
    loop = get_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


@atgent.route('/', methods=['GET'])
def index():
    if "session_id" not in session:
        import uuid

        session['session_id'] = str(uuid.uuid4())
    return render_template("index.html")


@atgent.route('/atgent/connect', methods=['POST'])
def connect():
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'message': 'Session not found'}), 400

        if session_id in sessions:
            print("[Server] -> sessions: ", sessions)
            return jsonify({'success': True, 'message': 'Already connected to MCP server'})

        client = MCPClient()
        run_async(client.connect_to_server('server.py'))
        tools_response = run_async(client.client_session.list_tools())
        tools = tools_response.tools

        sessions[session_id] = client
        print("[Server] -> sessions: ", sessions)

        return jsonify(
            {
                'success': True,
                'message': f'Connected to MCP server successfully!\n\nAvailable tools: {", ".join([tool.name for tool in tools])}',
            }
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'Connection failed: {str(e)}'}), 500


@atgent.route('/atgent/query', methods=['POST'])
def query():
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'message': 'Session not found'}), 400

        if session_id not in sessions:
            return jsonify({'success': False, 'message': 'Not connected to MCP server. Please connect first.'}), 400

        client = sessions[session_id]
        data = request.get_json()
        query = data.get('query', '').strip()

        result = run_async(client.process_query(query))

        return jsonify({'success': True, 'message': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Send failed: {str(e)}'}), 500
