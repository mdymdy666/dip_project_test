from datetime import timedelta
from flask import *
from flask_cors import CORS
from config import *
import os
import logging as rel_log
import shutil
import core.main
from core import vehicle_db

app = Flask(__name__, template_folder='./firstend/dist', static_folder='./firstend/dist/static', static_url_path='/static')
cors = CORS(app, supports_credentials=True)
app.config['MAX_CONTENT_PATH'] = 1024*1024

werkzeug_logger = rel_log.getLogger('werkzeug')
werkzeug_logger.setLevel(rel_log.ERROR)


# 跨域
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
    return response


ALLOWED_EXTENSIONS = set(['png', 'jpg'])   # 支持两种图片


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 解决缓存刷新问题
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)


# 处理调用函数
def process_func(img_name, img_path, num):
    if num == 1:
        print('ok')


# 判断上传有效
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def hello_world():
    return send_from_directory('./firstend/dist', 'index.html')


@app.route('/upload/<int:id>', methods=['POST', 'GET'])
def upload_image(id):
    if request.method == 'GET':
        # GET 请求返回前端页面（由 Vue Router 处理）
        return send_from_directory('./firstend/dist', 'index.html')
    
    # POST 请求处理上传
    # print("id", id)
    image = request.files['file']
    if image:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(img_path)

        shutil.copy(img_path, './tmp/ct')
        # pid = os.getpid()
        image_path = os.path.join('./tmp/ct', image.filename)
        # 50 OCR
        if id == 50:
            pid = image.filename
            try:
                ocr_text = core.main.ocr_main(image_path)
                return jsonify({'status': 1,
                                'image_url': 'http://127.0.0.1:5000/tmp/ct/' + pid,
                                'ocr_text': ocr_text
                                })
            except Exception as e:
                print('OCR Error:', str(e))
                return jsonify({'status': 0, 'error': str(e)})
        else:
            pid = core.main.c_main(image_path, id, image.filename.rsplit('.', 1)[1])

            return jsonify({'status': 1,
                            'image_url': 'http://127.0.0.1:5000/tmp/ct/' + pid,
                            'draw_url': 'http://127.0.0.1:5000/tmp/draw/' + pid  # 应该是/tmp/draw/ 是处理后的结果
                            })
    return jsonify({'status': 0})


@app.route('/api/plate/recognize', methods=['POST'])
def recognize_plate():
    image = request.files.get('file')
    if not image:
        return jsonify({'status': 0, 'error': '请上传车牌或车辆图片'})

    img_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(img_path)
    shutil.copy(img_path, './tmp/ct')
    image_path = os.path.join('./tmp/ct', image.filename)

    try:
        result = core.main.plate_main(image_path)
        return jsonify({
            'status': 1,
            'image_url': 'http://127.0.0.1:5000/tmp/ct/' + image.filename,
            'draw_url': 'http://127.0.0.1:5000/tmp/draw/' + result['draw_name'],
            'plates': result['plates'],
            'primary': result['primary'],
        })
    except Exception as e:
        print('Plate Error:', str(e))
        return jsonify({'status': 0, 'error': str(e)})


@app.route('/api/vehicle/init', methods=['GET', 'POST'])
def init_vehicle_database():
    db_path = vehicle_db.init_database()
    return jsonify({'status': 1, 'db_path': db_path, 'summary': vehicle_db.database_summary()})


@app.route('/api/vehicle/by-plate', methods=['GET', 'POST'])
def vehicle_by_plate():
    data = request.get_json(silent=True) or {}
    plate_no = data.get('plate_no') or request.args.get('plate_no')
    if not plate_no:
        return jsonify({'status': 0, 'error': '缺少车牌号'})
    return jsonify({'status': 1, 'data': vehicle_db.lookup_vehicle_with_owner(plate_no)})


@app.route('/api/owner/by-id-card', methods=['GET', 'POST'])
def owner_by_id_card():
    data = request.get_json(silent=True) or {}
    id_card = data.get('id_card') or request.args.get('id_card')
    if not id_card:
        return jsonify({'status': 0, 'error': '缺少身份证号'})
    return jsonify({'status': 1, 'data': vehicle_db.lookup_owner_with_vehicles(id_card)})


@app.route('/api/relationships', methods=['GET'])
def relationships():
    return jsonify({'status': 1, 'data': vehicle_db.list_relationships()})


@app.route('/api/relationships/change-owner', methods=['POST'])
def relationship_change_owner():
    data = request.get_json(silent=True) or {}
    try:
        result = vehicle_db.change_owner(
            data.get('plate_no', ''),
            data.get('id_card', ''),
            data.get('start_date'),
            data.get('event_location', ''),
            data.get('note', '动态变更')
        )
        return jsonify({'status': 1, 'data': result})
    except Exception as e:
        return jsonify({'status': 0, 'error': str(e)})


@app.route("/download", methods=['GET'])
def download_file():
    return send_from_directory('data')


@app.route('/tmp/<path:file>', methods=['GET'])
def show_photo(file):
    if request.method == 'GET':
        if not file is None:
            image_data = open(f'tmp/{file}', 'rb').read()
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/png'
            return response


# 处理 history 模式下的所有路由（必须放在最后）
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory('./firstend/dist', 'index.html')


if __name__ == '__main__':
    files = [
        'uploads', 'tmp/ct', 'tmp/draw',
        'tmp/image', 'tmp/mask', 'tmp/uploads'
    ]
    for ff in files:
        if not os.path.exists(ff):
            os.makedirs(ff)

    vehicle_db.init_database()
    app.run(debug=True)


