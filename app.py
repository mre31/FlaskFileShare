from flask import Flask, request, send_file, render_template, make_response, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta
import threading
import time
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix
import glob
import json

app = Flask(__name__)

# Proxy fix ayarlarını güncelle
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1,
    x_prefix=1,
    x_for=1
)

# HTTPS'i zorla
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Chunk boyutu için sınır (95MB)
CHUNK_SIZE = 95 * 1024 * 1024

# Geçici chunk'ları saklamak için klasör
TEMP_FOLDER = 'temp_chunks'
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# Dosya boyutu sınırını kaldır
app.config['MAX_CONTENT_LENGTH'] = None

# Directory for uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# JSON dosyası için sabit yol
FILES_DB = 'files_db.json'

# Dosya bilgilerini saklamak için dictionary
files = {}

# JSON dosyasından dosya bilgilerini yükle
def load_files_db():
    global files
    try:
        if os.path.exists(FILES_DB):
            with open(FILES_DB, 'r') as f:
                saved_files = json.load(f)
                # Tarihleri string'den datetime'a çevir
                for file_id, info in saved_files.items():
                    if 'expiry' in info:
                        info['expiry'] = datetime.fromisoformat(info['expiry'])
                files = saved_files
                print(f"Loaded {len(files)} files from database")
    except Exception as e:
        print(f"Error loading files database: {str(e)}")
        files = {}

# Dosya bilgilerini JSON'a kaydet
def save_files_db():
    try:
        # Tarihleri string'e çevir
        files_to_save = {}
        for file_id, info in files.items():
            files_to_save[file_id] = info.copy()
            if 'expiry' in files_to_save[file_id]:
                files_to_save[file_id]['expiry'] = info['expiry'].isoformat()
        
        with open(FILES_DB, 'w') as f:
            json.dump(files_to_save, f, indent=4)
        print(f"Saved {len(files)} files to database")
    except Exception as e:
        print(f"Error saving files database: {str(e)}")

# Temizleme fonksiyonu
def cleanup_old_files():
    while True:
        current_time = datetime.now()
        files_to_delete = []
        
        # Süresi dolan dosyaları bul
        for file_id, file_info in list(files.items()):
            if current_time > file_info['expiry']:
                try:
                    os.remove(file_info['path'])
                    files_to_delete.append(file_id)
                    print(f"Deleted expired file: {file_info['original_name']}")
                except Exception as e:
                    print(f"Error deleting file {file_id}: {str(e)}")
        
        # Silinen dosyaları dictionary'den kaldır
        for file_id in files_to_delete:
            del files[file_id]
        
        # Değişiklikler varsa JSON'ı güncelle
        if files_to_delete:
            save_files_db()
            print(f"Cleaned up {len(files_to_delete)} expired files")
        
        # Temp klasörünü temizle
        try:
            current_time = time.time()
            for temp_file in os.listdir(TEMP_FOLDER):
                temp_path = os.path.join(TEMP_FOLDER, temp_file)
                # 1 saatten eski temp dosyalarını sil
                if os.path.getctime(temp_path) < current_time - 3600:
                    os.remove(temp_path)
                    print(f"Deleted old temp file: {temp_file}")
        except Exception as e:
            print(f"Error cleaning temp folder: {str(e)}")
        
        time.sleep(3600)  # Her saat kontrol et

# Uygulama başladığında dosya bilgilerini yükle
load_files_db()

# Temizleme işlemini arka planda başlat
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file_id' in request.form or 'file_id' in request.args:
            # Chunk upload'dan gelen istek
            file_id = request.form.get('file_id') or request.args.get('file_id')
            if file_id in files:
                # Download linki oluştur - direct parametresi olmadan
                download_link = request.host_url + f'download/{file_id}'
                return render_template('upload_success.html', download_link=download_link)
            return 'File not found', 404
        
        if 'file' not in request.files:
            return 'No file selected', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        # Create unique file ID
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
        
        # Save file with stream to handle large files
        file.save(file_path)
        
        # Store file information
        files[file_id] = {
            'path': file_path,
            'original_name': filename,
            'expiry': datetime.now() + timedelta(days=1)
        }
        save_files_db()
        
        # Create download link - protokolü değiştirmeye gerek yok
        download_link = request.host_url + f'download/{file_id}'
        return render_template('upload_success.html', download_link=download_link)
    
    # GET isteği için
    if 'file_id' in request.args:
        file_id = request.args.get('file_id')
        if file_id in files:
            download_link = request.host_url + f'download/{file_id}'
            return render_template('upload_success.html', download_link=download_link)
        return 'File not found', 404
    
    return render_template('upload.html')

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in files:
        return 'File not found', 404
    
    file_info = files[file_id]
    
    # Doğrudan indirme yerine download sayfasına yönlendir
    if request.args.get('direct') != 'true':
        download_url = request.host_url + f'download/{file_id}?direct=true'
        return render_template('download.html', 
                             download_url=download_url,
                             filename=file_info['original_name'])
    
    # Range header'ı varsa partial content gönder
    range_header = request.headers.get('Range')
    if range_header:
        try:
            file_size = os.path.getsize(file_info['path'])
            byte_range = range_header.replace('bytes=', '').split('-')
            start = int(byte_range[0])
            end = int(byte_range[1]) if byte_range[1] else file_size - 1
            
            with open(file_info['path'], 'rb') as f:
                f.seek(start)
                data = f.read(end - start + 1)
                
            response = make_response(data)
            response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = str(end - start + 1)
            response.status_code = 206
            return response
        except Exception as e:
            print(f"Range request error: {str(e)}")
    
    # Normal download
    response = send_file(
        file_info['path'],
        as_attachment=True,
        download_name=file_info['original_name']
    )
    response.headers['Accept-Ranges'] = 'bytes'
    return response

@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        chunk_number = int(request.form['chunk'])
        total_chunks = int(request.form['total'])
        file_id = request.form['fileId']
        original_filename = request.form['filename']
        
        # Chunk'ı RAM'de işle
        chunk_data = file.read()
        
        # Chunk'ı diske yaz
        chunk_path = os.path.join(TEMP_FOLDER, f"{file_id}_chunk_{chunk_number}")
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        
        # Son chunk mu kontrol et
        if chunk_number == total_chunks - 1:
            # Tüm chunk'ları kontrol et
            chunk_paths = []
            missing_chunks = []
            
            # Önce mevcut chunk'ları kontrol et
            for i in range(total_chunks):
                chunk_file = os.path.join(TEMP_FOLDER, f"{file_id}_chunk_{i}")
                if os.path.exists(chunk_file):
                    chunk_paths.append(chunk_file)
                else:
                    missing_chunks.append(i)
            
            # Tüm chunk'lar tamam mı?
            if len(chunk_paths) == total_chunks:
                try:
                    # Dosyayı birleştir
                    final_filename = secure_filename(original_filename)
                    final_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{final_filename}")
                    
                    # Chunk'ları sıralı birleştir
                    with open(final_path, 'wb') as final_file:
                        for i in range(total_chunks):
                            chunk_path = os.path.join(TEMP_FOLDER, f"{file_id}_chunk_{i}")
                            with open(chunk_path, 'rb') as chunk:
                                final_file.write(chunk.read())
                            # Her chunk'ı hemen sil
                            os.remove(chunk_path)
                    
                    # Dosya bilgilerini kaydet
                    files[file_id] = {
                        'path': final_path,
                        'original_name': final_filename,
                        'expiry': datetime.now() + timedelta(days=1)
                    }
                    save_files_db()
                    
                    return jsonify({
                        'success': True,
                        'is_final': True,
                        'download_link': request.host_url + f'download/{file_id}',
                        'file_id': file_id
                    })
                    
                except Exception as e:
                    print(f"Error merging chunks: {str(e)}")
                    # Hata durumunda temizlik yap
                    for path in chunk_paths:
                        try:
                            os.remove(path)
                        except:
                            pass
                    return jsonify({'error': 'Failed to merge chunks'}), 500
            else:
                return jsonify({
                    'success': False,
                    'is_final': True,
                    'error': 'Missing chunks',
                    'missing': missing_chunks,
                    'total': total_chunks,
                    'received': len(chunk_paths)
                })
        
        # Ara chunk yanıtı
        return jsonify({
            'success': True,
            'is_final': False,
            'chunk': chunk_number,
            'total': total_chunks
        })
        
    except Exception as e:
        print(f"Upload chunk error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.after_request
def after_request(response):
    # Mevcut CORS başlıkları
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    
    # Güvenlik başlıkları
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy ekle
    response.headers['Content-Security-Policy'] = "upgrade-insecure-requests"
    
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Development mode için:
    # app.run(debug=True)
    
    # Production mode için Waitress:
    serve(app, 
          host='0.0.0.0', 
          port=5000, 
          threads=6,
          url_scheme='https',  # HTTPS şemasını belirt
          _quiet=True)  # Gereksiz logları kapat 