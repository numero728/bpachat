from flask import Flask, render_template,request,flash,jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import redirect
import re
import os
from datetime import datetime
from urllib.parse import unquote
import sys

# app 호출
if True:
    app = Flask(__name__)
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    app.config['SECRET_KEY'] = 'BPA_chat'

# socketio 통신 관련
if True:
    socketio = SocketIO(app, cors_allowed_origins='*', pingInterval=600000,
                        pingTimeout=600000)
    
    @socketio.on('connect')
    def connect():
        value=jsonify({'user':'system','msg':'정상적으로 접속되었습니다.'})
        emit('s_msg',value,broadcast=True)

    @socketio.on('login')
    def login(data):
        user=data['user']
        value=jsonify({'user':'system','msg':f'{user}님 환영합니다.'})
        emit('s_msg',value)
        
    @socketio.on('c_msg')
    def c_msg(data):
        user=data['user']
        msg=data['msg']
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        emit('s_msg', {'user': user, 'msg': msg}, broadcast=True)

    @socketio.on('disconnect')
    def disconnect():
        pass


@app.route('/')
def chat():
    now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('index.html')

@app.route('/log')
def logpage():
    now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return now

if __name__ == '__main__':
    socketio.run(app, debug=True)
