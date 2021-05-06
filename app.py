#-*- coding:utf-8 -*-
from flask import Flask, render_template, make_response, request, jsonify
from flask import abort, redirect, url_for
from jinja2 import Template

import urllib.request
import zipfile

import os
import json
import werkzeug
from datetime import datetime

app = Flask(__name__)

# FL-Server API

# limited upload file size: 100MB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 100


UPLOAD_DIR = "./resource/"

# stylesheet更新用の関数（システムとは無関係）
@app.context_processor
def add_staticfile():
    def staticfile_cp(fname):
        path = os.path.join(app.root_path, 'static/css', fname)
        mtime =  str(int(os.stat(path).st_mtime))
        return '/static/css/' + fname + '?v=' + str(mtime)
    return dict(staticfile=staticfile_cp)

@app.route('/fl-server')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['post'])
def upload():

    if 'uid' not in request.form['uid']:
        make_response(jsonify({'result': 'user id is required.'}))
    uid = request.form['uid']

    if 'uploadFile' not in request.files:
        return make_response(jsonify({'result': 'uploadFile is required.'}))
    file = request.files['uploadFile']
    filename = file.filename
    if '' == filename:
        return make_response(jsonify({'result': 'filename must not be empty.'}))

    try:
        saveFileName = datetime.now().strftime("%Y%m%d_%H%M%S_") \
            + werkzeug.utils.secure_filename(filename)
        file.save(os.path.join(UPLOAD_DIR+uid, saveFileName))
    except:
        return make_response(jsonify({'response': "error: invalid user id"}))

    return render_template('upload.html', name=filename, uid=uid)


@app.route('/redirect-pat', methods=['post'])
def redirect_pat():
    return redirect('http://authz-blockchain.ctiport.net:8888/pat', code=301)
    # return redirect('https://www.google.com', code=301)


@app.route('/reg-resource')
def reg_resource():
    # RO が AB に登録したいリソースを指定できるように

    # uid を受け取る
    if request.args.get('uid') != "":
        uid = request.args.get('uid')
    else:
        return jsonify({'message': 'forbidden'}), 403
    # PAT を受け取る
    if request.args.get('pat') != "":
        pat = request.args.get('pat')
    else:
        return jsonify({'message': 'forbidden'}), 403

    # リソース一覧を取得
    path = UPLOAD_DIR + uid
    try:
        files = os.listdir(path)
    except:
        return jsonify({'message': 'forbidden'}), 403
    li_files = [f for f in files if os.path.isfile(os.path.join(path, f))]

    # checkbox の value を動的に与える方法がわからなかったので python で毎回 html を生成して解決
    html = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 
    Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">

    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" type="text/css"
            href="/static/css/style.css">
        <link rel="stylesheet" type="text/css"
            href="/static/css/procedure.css">
        <title>FL-Server</title>
    </head>


    <body>
    <h1>FL-Server</h1>
    <p><b>FL-Server User ID: {0}</b></p>
    <h2>Resource List</h2>
    <p>Select <b>one</b> resource to allow <i>tff</i> scope.</p>
    <form action="/reg-resource" method="post">
    """.format(uid)

    html += '<input type="hidden" name="pat" value=' + pat + '><br>\n'
    for i in range(len(li_files)):
        html += '<input type="checkbox" name="check" value=' \
            + li_files[i] + '>' + li_files[i] + '<br>\n'

    html += """
    <br>
    <input type="hidden" name="uid" value={0}>
    <input type="submit" name="register">
    </form>
        <br>
        <br>
        <blockquote>
        <u>Procedure 04</u><br>
        The FL-Submitter registers a resource (i.e., model delta) that wants to protect  using the Authorization Blockchain. (3)<br>
        Here, it is set to be protected so that only actions defined as <i>tff</i> can be executed.
        In this demo, the term <i>tff</i> refers to the act of obtaining model deltas to perform Federated Learning with Tensorflow Federated.
        </p>
        </blockquote>
        <p><img src="/static/images/rreg04.png" width="673" height="400"></p>
    </body>

    </html>
    """.format(uid)

    template = Template(html)

    return template.render()


@app.route('/reg-resource', methods=['post'])
def reg_resource_post():
    # RS は指定されたリソースを AB に登録する
    # ＊注意＊ リソース選択が一つの場合しか実現できていないので，要修正

    # PAT を受け取る
    pat = request.form['pat']
    # 選択したリソース名を受け取る
    checks = request.form.getlist('check')
    # uid を受け取る
    uid = request.form['uid']

    # リソースを AB に登録するリクエストを生成する(authz-blockchain.ctiport.net:8888/rreg)
    rreg_url = 'http://authz-blockchain.ctiport.net:8888/rreg'
    data = {
        'resource_description': {
            'resource_scopes': ['tff'],
            'description': "sample_dataset",
            'icon_uri': "",
            'name': uid + '/' + checks[0],
            'type': ""
        },
        'timestamp': "1595230979",
        'timeSig': "vF9Oyfm+G9qS4/Qfns5MgSZNYjOPlAIZVECh2I5Z7HHgdloy5q7gJoxi7c1S2/ebIQbEMLS05x3+b0WD0VJfcWSUwZMHr3jfXYYwbeZ1TerKpvfp1j21nZ+OEP26bc28rLRAYZsVQ4Ilx7qp+uLfxu9X9x37Qj3n0CI2TEiKYSSYDQ0bftQ/3iWSSoGjsDljh9bKz1eVL911KeUGO+t/9IkB6LtZghdbIlnGISbgrVGoEOtGHi0t8uD2Vh/CRyBe+XnQV3HQtkjddLQitAesKTYunK1Ctia3x7klVjRH9XiJ11q6IbR8gz7rchdHYZe6HP+w/LyWMS5z6M26AXQrVw=="
    }
    headers = {
        'Authorization': 'Bearer {}'.format(pat),
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url=rreg_url, data=json.dumps(
        data).encode("utf-8"), headers=headers)

    # リクエストを投げてレスポンスを得る
    with urllib.request.urlopen(req) as res:
        body = res.read()
        body = body.decode('utf8').replace("'", '"')
        print("body: ", body)
        body = json.loads(body)
        print("body: ", body)
        resource_id = body['response']['resource_id']

    # リソース ID を表示し，ポリシー設定エンドポイントへ誘導する
    html = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 
    Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">

    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" type="text/css"
            href="/static/css/style.css">
        <link rel="stylesheet" type="text/css"
            href="/static/css/procedure.css">
        <title>FL-Server</title>
    </head>

    <body>
        <h1>FL-Server</h1>
        <p><b>FL-Server User ID: {0}</b></p>
        <p>Now that the resource has been registered in the Authorization Blockchain, set the authorization policy.</p>
        <br>
        <p><b>{1}</b> has been successfully registered.</p>
        <p><b>resource_id: {2}</b>
        <br>
        <h2>Go to the policy setting endpoint and set the policy.</h2>
        <form action="/set-policy" method="post">
            <button type="submit" value="set-policy">set policy</button>
            <input type="hidden" name="resource" value={1}>
            <input type="hidden" name="rid" value={2}>
        </form>
        <br>
        <br>
        <blockquote>
        <u>Procedure 05</u><br>
        The registration of the resource to the Authorization Blockchain is completed, and the resource on the corresponding resource server (i.e., FL-Server) is protected by the Authorization Blockchain. (4)<br>
        A unique identifier is assigned to each resource in the Authorization Blockchain.
        In the next page, the FL-Submitter defines the authorization policy for the registered resource.
        </p>
        </blockquote>
        <p><img src="/static/images/rreg05.png" width="673" height="400"></p>
    </body>

    </html>
    """.format(uid, checks[0], resource_id)

    template = Template(html)

    return template.render()


@app.route('/set-policy', methods=['post'])
def set_policy():
    # RO は登録されたリソースにポリシーを設定する
    resource = request.form['resource']
    rid = request.form['rid']
    # RO を authz-blockchain.ctiport.net:8888/policy に誘導する
    param = {'resource': resource, 'rid': rid}
    qs = urllib.parse.urlencode(param)
    return redirect('http://authz-blockchain.ctiport.net:8888/policy?' + qs, code=301)


# --- リソースアクセスフェーズ ---------------------------------------------------- #

@app.route('/resource', methods=['post'])
def req_resource():
    # RPT を検証後，RqP の ACL を作成・更新する
    """
    :req_header Content-Type application/json:
    :req_header Authorization Bearer: RPT
    :req_param string resource_id: 要求するリソースの ID
    :req_param list resource_scopes: 要求するリソースのスコープ
    """
    # ヘッダをチェック
    if not request.headers.get('Content-Type') == 'application/json':
        error_message = {
            'error': 'not supported Content-Type'
        }
        return make_response(json.dumps({'response': error_message}), 400)
    try:
        header_authz = request.headers.get('Authorization')
        bearer = header_authz.split('Bearer ')[-1]

        body = request.get_data().decode('utf8').replace("'", '"')
        body = json.loads(body)
        resource_id = body['resource_id']
        request_scopes = body['request_scopes']

    # rpt がなければ authz-blockchain.ctiport.net:8888/token へ誘導
    except:
        body = request.get_data().decode('utf8').replace("'", '"')
        body = json.loads(body)

        resource_id = body['resource_id']
        request_scopes = body['request_scopes']
        param = {
            'resource_id': resource_id,
            'request_scopes': request_scopes
        }
        qs = urllib.parse.urlencode(param)
        return redirect(url_for('authorize') + '?' + qs, 301)

    # rpt を検証(authz-blockchain.ctiport.net:8888/intro)
    intro_url = "http://authz-blockchain.ctiport.net:8888/intro"
    data = {
        'access_token': bearer
    }
    headers = {
        'Content-Type': 'application/json'
    }
    intro_req = urllib.request.Request(
        url=intro_url, data=json.dumps(data).encode('utf8'), headers=headers)

    # Request to http://authz-blockchain.ctiport.net:8888/intro
    with urllib.request.urlopen(intro_req) as res:
        body = res.read()
        body = body.decode('utf8').replace("'", '"')
        body = json.loads(body)

    # RPT の情報を取り出す
    try:
        active = body['response']['Active']  # RPT がアクティブか否か
        expire = body['response']['Expire']  # RPT の有効期限
        li_permissions = body['response']['Permissions']  # 許可されるパーミッションのリスト
    except:
        err_msg = body['response']
        return make_response(json.dumps({'response': err_msg}), 400)

    print("response: ", body['response'])

    # active に関する処理
    # some process

    # expire に関する処理
    # some process

    # li_permissions (include 'resource_id', 'expire', 'resource_scopes')に関する処理
    # 条件を満たすリソース名の一覧を作成

    # PAT の呼び出し（方法は未定）
    # (ro01, rs) - rid = 08db20ba-2666-5b91-9bef-3d5b7d9138ae
    pat = "0xddb5ab8c5405830359d2af4ec8d4bdf27bc4b8ee7d20f64ec1a71a634e551"
    # (ro02, rs) - rid = 1c1f1d9f-051c-592f-bb06-5ec8cef664ba
    #pat = "0x23e6958b1f555b905ade2f915c8c64453bd9514c4e1750d995f17215cbc4"
    # (ro03, rs) - rid = 7b7f4414-a949-5e48-a669-2f203efe6e3f
    # pat = "0xd0c4ed6f8adf3d7453dc2ece8d66ace20f37550373e653a4802425672ce"

    permitted_resources = []
    for perm in li_permissions:
        # expire に関する処理
        # some process

        # resource_id と resource_scopes に関する処理
        # Step 1. リソース ID とそのスコープを抽出
        rid = perm['ResourceId']
        resource_scopes = perm['ResourceScopes']

        # Step 2. リソーススコープにリクエストスコープが全て含まれていれば，リソース ID からリソース名を呼び出す(from authz-blockchain.ctiport.net)
        flag = True  # リクエストスコープ全体の判定用
        print(request_scopes)
        print(resource_scopes)
        for req_scope in request_scopes:
            _flag = False  # 個別のリクエストスコープ判定用
            for scope in resource_scopes:
                if req_scope == scope:
                    _flag = True
                    break
            if _flag is not True:
                flag = False
                break

        if flag:
            rreg_endpoint = "http://authz-blockchain.ctiport.net:8888/rreg-call"
            data = {
                'resource_id': rid
            }
            headers = {
                'Content-Type': 'application/json',
                'Authorization': "Bearer {}".format(pat)
            }
            rreg_req = urllib.request.Request(
                url=rreg_endpoint,
                data=json.dumps(data).encode('utf8'),
                headers=headers
            )
            # Request to http://authz-blockchain.ctiport.net:8888/rreg-call
            with urllib.request.urlopen(rreg_req) as res:
                body = res.read()
                body = body.decode('utf8').replace("'", '"')
                body = json.loads(body)
                name = body['response']['name']  # リソース名

        # Step 3. リソース名をリストに格納
        permitted_resources.append(name)

    # リソースの zip を作成する
    print("permitted_resources: ", permitted_resources)
    ZIP_DIR = './zipped/'
    FILENAME = resource_id + '.zip'
    ZIP_PATH = ZIP_DIR + FILENAME
    with zipfile.ZipFile(ZIP_PATH, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
        for name in permitted_resources:
            ARC_NAME = name.split('/')[-1]  # ファイル名だけを抽出
            new_zip.write(UPLOAD_DIR+name, arcname=ARC_NAME)

    # Client にダウンロードさせる
    downloadFile = ZIP_PATH
    downloadFileName = FILENAME
    ZIP_MIMETYPE = 'application/json'

    response = make_response()
    response.data = open(downloadFile, 'rb').read()
    response.headers['Content-Disposition'] = 'attachment; filename=' + \
        downloadFileName
    response.mimetype = ZIP_MIMETYPE
    return response


@app.route('/authorize')
def authorize():
    # パラメータの受け取り
    rid = request.args.get('resource_id')
    _scopes = request.args.get('request_scopes')
    _scopes = _scopes.replace("[", "").replace(
        "]", "").replace("'", "").strip()  # 文字列処理
    print("_scopes: ", _scopes)
    try:
        # スコープが複数ある場合
        request_scopes = _scopes.split(",")
    except:
        request_scopes = [_scopes]

    # 認可エンドポイント(/perm)との通信
    perm_url = 'http://authz-blockchain.ctiport.net:8888/perm'
    timestamp = "1595230979"
    timeSig = "vF9Oyfm+G9qS4/Qfns5MgSZNYjOPlAIZVECh2I5Z7HHgdloy5q7gJoxi7c1S2/ebIQbEMLS05x3+b0WD0VJfcWSUwZMHr3jfXYYwbeZ1TerKpvfp1j21nZ+OEP26bc28rLRAYZsVQ4Ilx7qp+uLfxu9X9x37Qj3n0CI2TEiKYSSYDQ0bftQ/3iWSSoGjsDljh9bKz1eVL911KeUGO+t/9IkB6LtZghdbIlnGISbgrVGoEOtGHi0t8uD2Vh/CRyBe+XnQV3HQtkjddLQitAesKTYunK1Ctia3x7klVjRH9XiJ11q6IbR8gz7rchdHYZe6HP+w/LyWMS5z6M26AXQrVw=="
    data = {
        'resource_id': rid,
        'request_scopes': request_scopes,
        'timestamp': timestamp,
        'timeSig': timeSig
    }
    print("data: ", data)
    headers = {
        'Content-Type': 'application/json'
    }
    perm_req = urllib.request.Request(
        url=perm_url, data=json.dumps(data).encode('utf8'), headers=headers)

    # Request to http://authz-blockchain.ctiport.net:8888/perm
    with urllib.request.urlopen(perm_req) as res:
        body = res.read()
        body = body.decode('utf8').replace("'", '"')
        body = json.loads(body)

    try:
        ticket = body['response']['ticket']
    except:
        err_msg = body['response']
        return make_response(json.dumps({'response': err_msg}), 400)
    token_endpoint = "http://authz-blockchain.ctiport.net:8888/token"

    # web client へのレスポンス
    res = {
        'response': {
            'ticket': ticket,
            'token_endpoint': token_endpoint
        }
    }

    return make_response(json.dumps(res), 200)





if __name__ == "__main__":
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=8080)
