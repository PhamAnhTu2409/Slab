#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
from cell import CELL, CELL_auto

app = Flask(__name__)
CORS(app)  # Cho phép frontend kết nối

# Thư mục upload
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return jsonify({
        "message": "🔬 SlabMaker API",
        "version": "1.0",
        "endpoints": {
            "/process": "POST - Xử lý tạo surface",
            "/health": "GET - Kiểm tra server"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "SlabMaker API"})

@app.route('/process', methods=['POST'])
def process_slab():
    """
    API xử lý tạo surface từ file cấu trúc
    """
    try:
        # Kiểm tra file
        if 'file' not in request.files:
            return jsonify({"error": "Không có file được upload"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Không có file được chọn"}), 400
        
        # Lấy thông số từ form
        miller_index = [
            int(request.form.get('h', 1)),
            int(request.form.get('k', 1)), 
            int(request.form.get('l', 1))
        ]
        vacuum = float(request.form.get('vacuum', 15.0))
        layers = int(request.form.get('layers', 1))
        output_format = request.form.get('format', 'poscar')  # poscar or qe
        
        # Lưu file tạm
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, file.filename)
        file.save(input_path)
        
        # Xử lý log
        logs = []
        
        def log_message(message, type="info"):
            logs.append({"message": message, "type": type})
            print(f"[{type.upper()}] {message}")
        
        log_message("🔄 Bắt đầu xử lý...")
        log_message(f"📁 File: {file.filename}")
        log_message(f"📐 Chỉ số Miller: {miller_index}")
        log_message(f"📏 Chân không: {vacuum} Å")
        log_message(f"📊 Số lớp: {layers}")
        
        # Đọc cấu trúc
        try:
            log_message("🔍 Đang đọc file cấu trúc...")
            bulk = CELL_auto(input_path)
            log_message(f"✅ Đã đọc cấu trúc: {bulk.nat} nguyên tử, {bulk.ntyp} loại nguyên tử")
            log_message(f"🧪 Nguyên tố: {', '.join(bulk.typ_name)}")
        except Exception as e:
            log_message(f"❌ Lỗi đọc file: {str(e)}", "error")
            return jsonify({"error": f"Lỗi đọc file: {str(e)}", "logs": logs}), 400
        
        # Tạo surface
        try:
            log_message(f"🔧 Đang tạo surface {miller_index}...")
            slab = bulk.makeslab(
                miller_index=miller_index,
                vacuum=vacuum,
                layer=layers
            )
            log_message("✅ Đã tạo surface thành công")
        except Exception as e:
            log_message(f"❌ Lỗi tạo surface: {str(e)}", "error")
            return jsonify({"error": f"Lỗi tạo surface: {str(e)}", "logs": logs}), 400
        
        # Thông tin kết quả
        results = {
            "natoms": slab.nat,
            "ntypes": slab.ntyp,
            "elements": slab.typ_name,
            "cell_vectors": slab.cell.tolist(),
            "vacuum_thickness": slab.get_vac() if hasattr(slab, 'get_vac') else vacuum,
            "slab_thickness": abs(slab.cell[2,2]) - (slab.get_vac() if hasattr(slab, 'get_vac') else vacuum)
        }
        
        # Tính diện tích surface
        try:
            area = np.linalg.norm(np.cross(slab.cell[0], slab.cell[1]))
            results["surface_area"] = area
            log_message(f"📐 Diện tích surface: {area:.2f} Å²")
        except:
            results["surface_area"] = 0.0
            log_message("⚠️ Không thể tính diện tích surface", "warning")
        
        log_message(f"📊 Số nguyên tử surface: {slab.nat}")
        log_message(f"🧪 Loại nguyên tử: {slab.ntyp}")
        
        # Tạo file kết quả
        output_filename = f"surface_{miller_index[0]}{miller_index[1]}{miller_index[2]}"
        
        if output_format == 'poscar':
            output_path = os.path.join(temp_dir, f"{output_filename}.vasp")
            slab.print_poscar(output_path)
            log_message(f"💾 Đã lưu POSCAR: {output_filename}.vasp")
        else:
            output_path = os.path.join(temp_dir, f"{output_filename}.in")
            slab.print_pwinput(output_path)
            log_message(f"💾 Đã lưu QE input: {output_filename}.in")
        
        # Đọc nội dung file kết quả
        with open(output_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        log_message("🎉 Hoàn thành xử lý!")
        
        # Trả về kết quả
        return jsonify({
            "success": True,
            "results": results,
            "logs": logs,
            "file_content": file_content,
            "filename": os.path.basename(output_path),
            "format": output_format
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Lỗi hệ thống: {str(e)}",
            "logs": logs if 'logs' in locals() else []
        }), 500

@app.route('/download', methods=['POST'])
def download_file():
    """
    API download file kết quả
    """
    try:
        data = request.json
        file_content = data.get('content', '')
        filename = data.get('filename', 'surface.vasp')
        
        # Tạo file tạm
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({"error": f"Lỗi download: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)