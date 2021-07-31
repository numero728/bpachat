# coding=UTF-8

#====================================================================
# 환경 설정
if True:
    # -------------------------------------------------------------------
    # 모듈 import
    if True:
        from fabric.contrib.files import exists
        from fabric.api import env, local, run, sudo
        import os
        import json
        import re

    # -------------------------------------------------------------------
    # deploy.json 파일로부터 환경변수 파라미터 호출
    if True:
        PROJECT_DIR         =   os.path.dirname(os.path.abspath(__file__))
        
        envs                =   json.load(open(os.path.join(PROJECT_DIR,'deploy.json')))

        REPO_URL            =   envs['REPO_URL']
        PROJECT_NAME        =   envs['PROJECT_NAME']
        REMOTE_HOST         =   envs['REMOTE_HOST']
        REMOTE_HOST_SSH     =   envs['REMOTE_HOST_SSH']
        REMOTE_USER         =   envs['REMOTE_USER']
        KEY_FILE            =   envs['KEY_FILE']
        REMOTE_PASSWD       =   envs['REMOTE_PASSWD']
        REMOTE_PORT         =   envs['REMOTE_PORT']

    # -------------------------------------------------------------------
    # 환경변수 설정
    if True:
        env.user            =   REMOTE_USER
        env.hosts           =   [REMOTE_HOST_SSH]
        env.use_ssh_config  =   True
        env.key_filename    =   os.path.join('..',KEY_FILE)
        env.password        =   REMOTE_PASSWD
        env.port            =   REMOTE_PORT

    # -------------------------------------------------------------------
    # 원격지의 프로젝트 폴더 주소 설정
    if True:
        PROJECT_FOLDER      =   f'/home/{env.user}/{PROJECT_NAME}'

    # -------------------------------------------------------------------
    # 필요 apt 패키지 설정
    if True:
        # packages.txt 읽기
        with open(os.path.join(PROJECT_DIR,'packages.txt'),'r') as fp:
            packages=fp.readlines()
        apt_requirements=[re.sub('\n','',ln) for ln in packages]

    # -------------------------------------------------------------------
    # 필요 파이썬 패키지 설정
    if True:
        # requirements.txt 읽기
        with open(os.path.join(PROJECT_DIR,'requirements.txt'),'r') as fp:
            requirements=fp.readlines()
        pip_requirements=[re.sub('\n','',ln) for ln in requirements]

#====================================================================
# 최초 배포
if True:
    def new_server():
        setup()
        deploy()

# -------------------------------------------------------------------
# setup
def setup():
    # os 업데이트
    _get_latest_apt()

    # apt 패키지 설치
    _install_apt_requirements(apt_requirements)

    # flask 구동 필요한 가상환경 구축
    _make_virtualenv()

# -------------------------------------------------------------------
# deploy
def deploy():
    _get_latest_source()
    _update_virtualenv()
    _make_virtualhost()
    _grant_apache2()
    _restart_apache2()

# -------------------------------------------------------------------
# 최신 버전 apt로 업데이트
def _get_latest_apt():
    # 업데이트 여부 확인
    update_or_not = input('would you update?: [y/n]')
    if update_or_not == 'y':
        sudo('apt-get update && apt-get -y upgrade')

# -------------------------------------------------------------------
# apt 패키지 설치
def _install_apt_requirements(apt_requirements):
    reqs = ''
    # 설치할 패키지 리스트 -> 하나의 문자열로 변환
    for req in apt_requirements:
        reqs += (' ' + req)
    sudo(f'apt-get -y install {reqs}')

# -------------------------------------------------------------------
# 가상환경 생성
def _make_virtualenv():
    # 현재 디렉토리에 대해 소유권 선언
    sudo(f'chown {REMOTE_USER} ~/')

    # 기존 가상환경 존재하는지 확인
    # 기존 가상환경 없으면 신규로 생성
    if not exists('~/.virtualenvs'):
        # 가상환경 디렉토리 생성
        run('mkdir ~/.virtualenvs')

        # 루트 권한으로 pip 통해 virtualenv, virtualenvwrapper 설치
        sudo('pip3 install virtualenv virtualenvwrapper')
        
        # .bashrc에 가상환경 관련 PATH 등 설정
        script = '''"# python virtualenv settings
                    export WORKON_HOME=~/.virtualenvs
                    export VIRTUALENVWRAPPER_PYTHON="$(command \\which python3)"  # location of python3
                    source /usr/local/bin/virtualenvwrapper.sh"'''
        
        # .bashrc 실행
        run(f'echo {script} >> ~/.bashrc')
        
# -------------------------------------------------------------------
# 방화벽 허용      
def _ufw_allow():
    sudo("ufw allow 'Apache Full'")
    sudo("ufw reload")

# -------------------------------------------------------------------
# 아파치 서버 환경 설정
def _make_virtualhost():
    # apache2 conf 설정할 내용
    script = f"""'<VirtualHost *:80>
    ServerName {REMOTE_HOST}
    <Directory /home/{REMOTE_USER}/{PROJECT_NAME}>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    WSGIDaemonProcess {PROJECT_NAME} python-home=/home/{REMOTE_USER}/.virtualenvs/{PROJECT_NAME} python-path=/home/{REMOTE_USER}/{PROJECT_NAME}
    WSGIProcessGroup {PROJECT_NAME}
    WSGIScriptAlias / /home/{REMOTE_USER}/{PROJECT_NAME}/wsgi.py
    
    ErrorLog ${{APACHE_LOG_DIR}}/error.log
    CustomLog ${{APACHE_LOG_DIR}}/access.log combined
    
    </VirtualHost>'"""

    # sudo 명령으로 conf 설정
    sudo(f'echo {script} > /etc/apache2/sites-available/{PROJECT_NAME}.conf')

    # 프로젝트 활성화
    sudo(f'a2ensite {PROJECT_NAME}.conf')

    # 디폴트 비활성화
    run(f"echo '{REMOTE_PASSWD}' | sudo -S a2dissite /etc/apache2/sites-available/000-default.conf")

# -------------------------------------------------------------------
# 아파치 서버 권한 설정
def _grant_apache2():
    # PROJECT_NAME 디렉토리의 소유권 www-data로 이전
    # www-data: 아파치 데몬(웹사이트 구동하는 owner)
    sudo(f'chown -R :www-data ~/{PROJECT_NAME}')
    
    # PROJECT_NAME의 권한 조정
    sudo(f'chmod -R 775 ~/{PROJECT_NAME}')

# -------------------------------------------------------------------
# 아파치 재시동
def _restart_apache2():
    sudo('service apache2 restart')

# -------------------------------------------------------------------
# 최신 버전의 저장소 내용으로 업데이트
def _get_latest_source():
    # .git 파일 유무 확인
    # .git 파일 있으면 fetch로 업데이트 
    if exists(PROJECT_FOLDER + '/.git'):
        # PROJECT_FOLDER로 이동하여 최신 내용으로 업데이트
        run(f'cd {PROJECT_FOLDER} && git fetch')
    
    # .git 파일 없으면 clone로 불러오기
    else:
        run(f'git clone {REPO_URL} {PROJECT_FOLDER}')

    # local에서 가장 최근의 commit의 해시 조회
    current_commit = local("git log -n 1 --format=%H", capture=True)

    # PROJECT_FOLDER의 내용들을 가장 최근의 commit 버전으로 업데이트
    run(f'cd {PROJECT_FOLDER} && git reset --hard {current_commit}')

# -------------------------------------------------------------------
# 가상환경 업데이트
def _update_virtualenv():
    # 가상환경 폴더 안에 PROJECT_NAME 이름의 폴더 유무 확인
    VIRTUALENV_FOLDER = PROJECT_FOLDER + f'/../.virtualenvs/{PROJECT_NAME}'
    
    # 폴더 존재하지 않는 경우
    if not exists(VIRTUALENV_FOLDER + '/bin/pip'):
        # 가상환경 신규로 생성
        run(f'cd /home/{REMOTE_USER}/.virtualenvs && virtualenv {PROJECT_NAME}')
    
    # 가상환경에서 사용할 파이썬 패키지 설치
    run(f'{VIRTUALENV_FOLDER}/bin/pip install -r {PROJECT_FOLDER}/requirements.txt')

# -------------------------------------------------------------------
