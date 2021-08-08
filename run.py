#-*- coding: utf-8 -*-
from flask import Flask, render_template,request,flash,jsonify,url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import redirect,secure_filename
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
    emo_keys=['angry','cry','none','steak','mint','lunch','turn','home1','chicken','damn','home2','siba']
    UPLOAD_FOLDER = os.path.join(os.getcwd(),'static','uploaded')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','xlsx','xls','csv','hwp','doc','docx','ppt','pptx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# socketio 통신 관련
if True:
    socketio = SocketIO(app, cors_allowed_origins='*',async_mode='threading')
    
    @socketio.on('connect',namespace='/chatroom')
    def connect():
        value={'user':'system','msg':'정상적으로 접속되었습니다.','ico':'fox','emo':'none'}
        emit('s_msg',value)

    @socketio.on('login')
    def login(data):
        user=data['user']
        value={'user':'system','msg':f'{user}님 환영합니다.','ico':'fox','emo':'none'}
        emit('s_msg',value)
        
    @socketio.on('c_msg')
    def c_msg(data):
        user=data['user']
        msg=data['msg']
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        raw_msg=unquote(msg)
        if raw_msg=='이모티콘 리스트':
            emit('s_msg',{'user':'system','msg':' | '.join(emo_keys),'ico':'fox','emo':'none'})
        else:
            if '[이모티콘]' in raw_msg:
                for emo in emo_keys:
                    if emo in raw_msg:
                        emit('s_msg',{'user':user,'msg':'이모티콘','ico':'none','emo':emo},broadcast=True)
                        break
                    else:
                        continue
            else:
                emit('s_msg', {'user': user, 'msg': msg,'ico':'none','emo':'none'},broadcast=True)

    @socketio.on('disconnect')
    def disconnect():
        pass


@app.route('/')
def chat():
    now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('index.html')

@app.route('/log')
def log():
    return 'hello'

@app.route('/drive')
def drive():
    file_list=[]
    return render_template('drive.html',file_list=file_list)

@app.route('/upload',methods=['POST'])
def upload():
    file=request.files['file']
    file_path= os.path.join(app.config['UPLOAD_FOLDER'],file.filename)
    return file_path
    # return redirect('/drive')



if __name__ == '__main__':
    socketio.run(app, debug=True)
