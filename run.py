from flask import Flask, render_template,request,jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import redirect
import re
import os
from datetime import datetime
from urllib.parse import unquote

def log(now_date,message):
    cur_date=re.search('([\d]+)',re.sub('-','',now_date)).group(1)
    try:
        with open(os.path.join('log',f'{cur_date}.txt'),'a') as fp:
            fp.write(message+'\n')
    except Exception as e:
        print(e)
        with open(os.path.join('log',f'{cur_date}.txt'),'w') as fp:
            fp.write(message+'\n')

def log_read(now_date):
    cur_date=re.search('([\d]+)',re.sub('-','',now_date)).group(1)
    data=list()

    try:
        with open(os.path.join('log',f'{cur_date}.txt'),'r') as fp:
            log_text=fp.readlines()
        log_text=[text for text in log_text if '[Send]' in text]
        for ln in log_text:
            try:
                data.append((re.search('\[Send\] ([\w]+) ',ln).group(1), re.search('msg:([\w\d %]+) timestamp',ln).group(1)))
            except:
                continue
    except:
        data.append(('System','오늘의 첫 메시지입니다.'))
    return data
            
    
# app 호출
if True:
    app = Flask(__name__)
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    app.config['SECRET_KEY'] = 'BPA_chat'

# socketio 통신 관련
if True:
    socketio = SocketIO(app, cors_allowed_origins='*', pingInterval=600000,
                        pingTimeout=600000, async_mode='threading', manage_session=False)
    
    @socketio.on('connect')
    def connect():
        user=request.args.get('user')
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg=(f'[Connected] {user} timestamp:{now}')
        log(now,log_msg)

    @socketio.on('c_msg')
    def c_msg(data):  # 요기서 댓글 텍스트 처리
        user=data['user']
        msg=data['msg']
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg=(f'[Send] {user} msg:{msg} timestamp:{now}')
        emit('s_msg', {'user': user, 'msg': msg}, broadcast=True)
        log(now,unquote(log_msg))

    @socketio.on('disconnect')
    def disconnect():
        pass


@app.route('/')
def chat():
    now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    texts=log_read(now)
    print(texts)
    return render_template('index.html',texts=texts)

@app.route('/log')
def logpage():
    now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    texts=log_read(now)
    return texts

if __name__ == '__main__':
    socketio.run(app, debug=True)
