from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime, timedelta
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'user_id' not in session or session['user_role'] != 'Quản trị viên':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        ten = request.form['ten']
        email = request.form['email']
        mat_khau = request.form['mat_khau']
        loai = int(request.form['loai'])  # Phân loại người dùng

        conn = sqlite3.connect('thuvien.db')
        cur = conn.cursor()
        
        hashed_password = bcrypt.hashpw(mat_khau.encode('utf-8'), bcrypt.gensalt())
        try:
            cur.execute('INSERT INTO nguoi_dung (ten, email, mat_khau, loai) VALUES (?, ?, ?, ?)', (ten, email, hashed_password, loai))
            conn.commit()
            flash('Người dùng đã được thêm thành công!', 'success')
        except sqlite3.IntegrityError:
            flash('Email đã tồn tại!', 'error')
        
        conn.close()
        return redirect(url_for('user_management'))
    
    return render_template('add_user.html')

# Sửa người dùng
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user_id' not in session or session['user_role'] != 'Quản trị viên':
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    
    if request.method == 'POST':
        ten = request.form['ten']
        email = request.form['email']
        loai = int(request.form['loai'])
        
        cur.execute('UPDATE nguoi_dung SET ten = ?, email = ?, loai = ? WHERE ma_nguoi_dung = ?', (ten, email, loai, user_id))
        conn.commit()
        conn.close()
        
        flash('Người dùng đã được cập nhật thành công!', 'success')
        return redirect(url_for('user_management'))
    
    cur.execute('SELECT * FROM nguoi_dung WHERE ma_nguoi_dung = ?', (user_id,))
    user = cur.fetchone()
    conn.close()
    
    return render_template('edit_user.html', user=user)

# Xóa người dùng
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session['user_role'] != 'Quản trị viên':
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    
    cur.execute('DELETE FROM nguoi_dung WHERE ma_nguoi_dung = ?', (user_id,))
    conn.commit()
    conn.close()
    
    flash('Người dùng đã được xóa thành công!', 'success')
    return redirect(url_for('user_management'))

# # Phân quyền cho người dùng
# @app.route('/assign_role/<int:user_id>', methods=['GET', 'POST'])
# def assign_role(user_id):
#     if request.method == 'POST':
#         roles = request.form.getlist('roles')
        
#         conn = sqlite3.connect('thuvien.db')
#         cur = conn.cursor()
#         cur.execute('DELETE FROM quyen_nguoi_dung WHERE ma_nguoi_dung = ?', (user_id,))
#         for role_id in roles:
#             cur.execute('''
#             INSERT INTO quyen_nguoi_dung (ma_nguoi_dung, ma_quyen)
#             VALUES (?, ?)
#             ''', (user_id, role_id))
#         conn.commit()
#         conn.close()
#         return redirect(url_for('user_management'))
    
#     conn = sqlite3.connect('thuvien.db')
#     cur = conn.cursor()
#     cur.execute('SELECT * FROM phan_quyen')
#     all_roles = cur.fetchall()
#     cur.execute('SELECT ma_quyen FROM quyen_nguoi_dung WHERE ma_nguoi_dung = ?', (user_id,))
#     user_roles = [role[0] for role in cur.fetchall()]
#     conn.close()
#     return render_template('assign_role.html', roles=all_roles, user_roles=user_roles, user_id=user_id)

@app.route('/user_management', methods=['GET'])
def user_management():
    query = request.args.get('query', '').lower()  # Chuyển từ khóa tìm kiếm thành chữ thường
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()

    # Truy vấn có điều kiện nếu có từ khóa tìm kiếm
    if query:
        cur.execute('SELECT * FROM nguoi_dung WHERE LOWER(ten) LIKE ? OR LOWER(email) LIKE ?', 
                    (f'%{query}%', f'%{query}%'))
    else:
        cur.execute('SELECT * FROM nguoi_dung')

    users = cur.fetchall()

    # Phân trang
    page = request.args.get('page', 1, type=int)  # Lấy số trang hiện tại từ query parameters
    per_page = 5  # Số lượng người dùng trên mỗi trang
    
    total_users = len(users)  # Tổng số người dùng
    total_pages = (total_users + per_page - 1) // per_page  # Tổng số trang
    
    start = (page - 1) * per_page  # Vị trí bắt đầu
    end = start + per_page  # Vị trí kết thúc
    users_to_display = users[start:end]  # Danh sách người dùng cần hiển thị

    conn.close()
    message = request.args.get('message')
    
    return render_template('user_management.html', users=users_to_display, message=message, 
                           query=query, page=page, total_pages=total_pages, total_users=total_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        mat_khau = request.form['mat_khau']
        
        # Kiểm tra xem email và mật khẩu có bị bỏ trống không
        if not email or not mat_khau:
            flash('Email và mật khẩu không được để trống.', 'error')
            return render_template('login.html')
        
        conn = sqlite3.connect('thuvien.db')
        cur = conn.cursor()
        
        # Kiểm tra email và lấy thông tin người dùng
        cur.execute('SELECT * FROM nguoi_dung WHERE email = ?', (email,))
        user = cur.fetchone()
        
        if user:
            hashed_password = user[3]  # Mật khẩu đã mã hóa
            if bcrypt.checkpw(mat_khau.encode('utf-8'), hashed_password):
                user_id = user[0]
                user_loai = user[4]  # Lấy loại quyền từ cột 'loai'
                
                # Truy vấn quyền người dùng dựa trên 'loai'
                cur.execute('SELECT ten_quyen FROM phan_quyen WHERE ma_quyen = ?', (user_loai,))
                user_role = cur.fetchone()

                if user_role:
                    session['user_id'] = user_id
                    session['user_role'] = user_role[0]  # Lưu quyền của người dùng trong session
                    conn.close()

                    # Điều hướng dựa trên quyền của người dùng
                    if user_role[0] == 'Quản trị viên':
                        return redirect(url_for('admin_dashboard'))
                    elif user_role[0] == 'Thủ thư':
                        return redirect(url_for('librarian_dashboard'))
                    elif user_role[0] == 'Độc giả':
                        return redirect(url_for('member_dashboard'))
                    else:
                        flash('Người dùng không có quyền hợp lệ', 'error')
                else:
                    flash('Người dùng không có quyền hợp lệ', 'error')
            else:
                flash('Mật khẩu không chính xác', 'error')
        else:
            flash('Email không tồn tại', 'error')
        
        conn.close()
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    return redirect(url_for('login'))


# Trang quản trị viên
@app.route('/admin_dashboard')
def admin_dashboard():
    # Kiểm tra nếu người dùng đã đăng nhập và có quyền Quản trị viên
    if 'user_id' not in session or session.get('user_role') != 'Quản trị viên':
        return redirect(url_for('login'))
    
    return render_template('admin_dashboard.html')  # Hiển thị trang quản trị viên

# Trang thủ thư
@app.route('/librarian_dashboard')
def librarian_dashboard():
    # Kiểm tra nếu người dùng đã đăng nhập và có quyền Thủ thư
    if 'user_id' not in session or session.get('user_role') != 'Thủ thư':
        return redirect(url_for('login'))
    
    return render_template('librarian_dashboard.html')  # Hiển thị trang thủ thư

# Trang độc giả
@app.route('/member_dashboard')
def member_dashboard():
    # Kiểm tra nếu người dùng đã đăng nhập và có quyền Độc giả
    if 'user_id' not in session or session.get('user_role') != 'Độc giả':
        return redirect(url_for('login'))
    
    return render_template('member_dashboard.html')  # Hiển thị trang độc giả


def get_db_connection():
    conn = sqlite3.connect('thuvien.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/books', methods=['GET'])
def books():
    search_query = request.args.get('query', '').lower()  # Chuyển query về chữ thường
    conn = get_db_connection()

    if search_query:
        # Nếu có từ khóa tìm kiếm, lọc sách theo các tiêu chí không phân biệt hoa thường
        query = f"""
            SELECT * FROM sach
            WHERE LOWER(ten_sach) LIKE ? OR LOWER(ten_TG) LIKE ? OR LOWER(nha_XB) LIKE ? 
            OR LOWER(nam_XB) LIKE ? OR LOWER(loai_sach) LIKE ? OR so_tien LIKE ? OR vi_tri LIKE ?
        """
        books = conn.execute(query, [
            f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', 
            f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'
        ]).fetchall()
    else:
        # Nếu không có tìm kiếm, hiển thị toàn bộ sách
        books = conn.execute('SELECT * FROM sach').fetchall()

    # Phân trang
    page = request.args.get('page', 1, type=int)  # Lấy số trang hiện tại từ query parameters
    per_page = 5  # Số lượng sách trên mỗi trang

    total_books = len(books)  # Tổng số sách
    total_pages = (total_books + per_page - 1) // per_page  # Tổng số trang

    start = (page - 1) * per_page  # Vị trí bắt đầu
    end = start + per_page  # Vị trí kết thúc
    books_to_display = books[start:end]  # Danh sách sách cần hiển thị

    conn.close()
    
    return render_template('books.html', books=books_to_display, query=search_query,
                           page=page, total_pages=total_pages, total_books=total_books)

# Trang thêm sách
@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    message = ''
    if request.method == 'POST':
        ten_sach = request.form['ten_sach']
        ten_TG = request.form['ten_TG']
        nha_XB = request.form['nha_XB']
        nam_XB = request.form['nam_XB']
        loai_sach = request.form['loai_sach']
        so_luong = request.form['so_luong']
        so_trang = request.form['so_trang']
        so_tien = request.form['so_tien']  # Thêm trường số tiền
        vi_tri = request.form['vi_tri']      # Thêm trường vị trí
        
        conn = sqlite3.connect('thuvien.db')
        cur = conn.cursor()

        try:
            cur.execute(''' 
                INSERT INTO sach (ten_sach, ten_TG, nha_XB, nam_XB, loai_sach, so_luong, so_trang, so_tien, vi_tri)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ten_sach, ten_TG, nha_XB, nam_XB, loai_sach, so_luong, so_trang, so_tien, vi_tri))
            conn.commit()
            message = 'Thêm sách thành công!'
        except Exception as e:
            message = f'Đã xảy ra lỗi: {e}'
        finally:
            conn.close()
    
    return render_template('add_book.html', message=message)

# Xoá Sách
@app.route('/books/delete/<int:book_id>')
def delete_book(book_id):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM sach WHERE ma_sach = ?', (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('books'))

# Sửa Sách
@app.route('/edit_book/<int:book_id>', methods=['GET'])
def edit_book(book_id):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM sach WHERE ma_sach = ?', (book_id,))
    book = cur.fetchone()
    conn.close()
    
    if book:
        return render_template('edit_book.html', book=book)
    else:
        return 'Sách không tồn tại', 404

# Cập nhật sách
@app.route('/update_book/<int:book_id>', methods=['POST'])
def update_book(book_id):
    ten_sach = request.form['ten_sach']
    ten_TG = request.form['ten_TG']
    nha_XB = request.form['nha_XB']
    nam_XB = request.form['nam_XB']
    loai_sach = request.form['loai_sach']
    so_luong = request.form['so_luong']
    so_trang = request.form['so_trang']
    so_tien = request.form['so_tien']  # Thêm trường số tiền
    vi_tri = request.form['vi_tri']      # Thêm trường vị trí
    
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    cur.execute('''
        UPDATE sach
        SET ten_sach = ?, ten_TG = ?, nha_XB = ?, nam_XB = ?, loai_sach = ?, so_luong = ?, so_trang = ?, so_tien = ?, vi_tri = ?
        WHERE ma_sach = ?
    ''', (ten_sach, ten_TG, nha_XB, nam_XB, loai_sach, so_luong, so_trang, so_tien, vi_tri, book_id))
    
    conn.commit()
    conn.close()
    
    # Chuyển hướng về trang sửa sách với thông báo
    return redirect(url_for('edit_book', book_id=book_id, _anchor='message', message='Cập nhật thông tin sách thành công'))

@app.route('/members', methods=['GET'])
def members():
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    
    query = request.args.get('query')  # Lấy giá trị tìm kiếm từ query parameters
    page = request.args.get('page', 1, type=int)  # Lấy số trang hiện tại từ query parameters
    per_page = 5  # Số lượng thành viên trên mỗi trang

    if query:
        # Tìm kiếm theo tên độc giả hoặc số CMND
        cur.execute("SELECT * FROM doc_Gia WHERE LOWER(ten_docgia) LIKE LOWER(?) OR LOWER(so_CMND) LIKE LOWER(?)", 
                    ('%' + query + '%', '%' + query + '%'))
        members = cur.fetchall()
    else:
        cur.execute('SELECT * FROM doc_Gia')
        members = cur.fetchall()

    # Tính toán phân trang
    total_members = len(members)  # Tổng số thành viên
    total_pages = (total_members + per_page - 1) // per_page  # Tổng số trang
    start = (page - 1) * per_page  # Vị trí bắt đầu
    end = start + per_page  # Vị trí kết thúc
    members_to_display = members[start:end]  # Danh sách thành viên cần hiển thị

    # Đóng kết nối
    conn.close()
    
    # Lấy thông báo từ query parameters
    message = request.args.get('message')
    
    return render_template('members.html', members=members_to_display, message=message, 
                           page=page, total_pages=total_pages, total_members=total_members)


@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    message = ''
    if request.method == 'POST':
        # Lấy thông tin từ form
        ten_docgia = request.form['ten_docgia']
        ngay_sinh = request.form['ngay_sinh']
        so_CMND = request.form['so_CMND']
        so_DT = request.form['so_DT']
        ngay_HHT = request.form['ngay_HHT']
        dia_Chi = request.form['dia_Chi']

        # Kiểm tra độ dài số CMND và số điện thoại
        if len(so_CMND) != 12:
            message = 'Số CMND phải có 12 số.'
            return render_template('add_members.html', message=message)

        if len(so_DT) != 10:
            message = 'Số điện thoại phải có 10 số.'
            return render_template('add_members.html', message=message)

        # Kết nối tới cơ sở dữ liệu và kiểm tra trùng
        conn = sqlite3.connect('thuvien.db')
        cur = conn.cursor()

        try:
            # Kiểm tra xem số CMND đã tồn tại chưa
            cur.execute('SELECT COUNT(*) FROM doc_Gia WHERE so_CMND = ?', (so_CMND,))
            if cur.fetchone()[0] > 0:
                message = 'Số CMND này đã tồn tại.'
                return render_template( 'add_members.html', message=message)

            # Kiểm tra xem số điện thoại đã tồn tại chưa
            cur.execute('SELECT COUNT(*) FROM doc_Gia WHERE so_DT = ?', (so_DT,))
            if cur.fetchone()[0] > 0:
                message = 'Số điện thoại này đã tồn tại.'
                return render_template('add_members.html', message=message)

            # Thêm độc giả
            cur.execute(''' 
                INSERT INTO doc_Gia (ten_docgia, ngay_sinh, so_CMND, so_DT, ngay_HHT, dia_Chi)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ten_docgia, ngay_sinh, so_CMND, so_DT, ngay_HHT, dia_Chi))
            conn.commit()
            message = 'Thêm độc giả thành công!'
        except Exception as e:
            message = f'Đã xảy ra lỗi: {e}'
        finally:
            conn.close()

    return render_template('add_members.html', message=message)

@app.route('/members/delete/<int:id_docgia>')
def delete_member(id_docgia):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM doc_Gia WHERE id_docgia = ?', (id_docgia,))
    conn.commit()
    conn.close()
    return redirect(url_for('members'))

# Sửa Độc Giả
@app.route('/edit_member/<int:id_docgia>', methods=['GET'])
def edit_member(id_docgia):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM doc_Gia WHERE id_docgia = ?', (id_docgia,))
    member = cur.fetchone()
    conn.close()
    
    if member:
        return render_template('edit_members.html', member=member)
    else:
        return 'Độc giả không tồn tại', 404
# Update độc giả
@app.route('/update_member/<int:id_docgia>', methods=['POST'])
def update_member(id_docgia):
    ten_docgia = request.form['ten_docgia']
    ngay_sinh = request.form['ngay_sinh']
    so_CMND = request.form['so_CMND']
    so_DT = request.form['so_DT']
    ngay_HHT = request.form['ngay_HHT']
    dia_Chi = request.form['dia_Chi']
    
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    cur.execute('''
        UPDATE doc_Gia
        SET ten_docgia = ?, ngay_sinh = ?, so_CMND = ?, so_DT = ?, ngay_HHT = ?, dia_Chi = ?
        WHERE id_docgia = ?
    ''', (ten_docgia, ngay_sinh, so_CMND, so_DT, ngay_HHT, dia_Chi, id_docgia))
    
    conn.commit()
    conn.close()
    
    # Chuyển hướng về trang sửa thông tin độc giả với thông báo
    return redirect(url_for('edit_member', id_docgia=id_docgia, _anchor='message', message='Cập nhật thông tin độc giả thành công'))


# Thêm phiếu mượn
@app.route('/add_borrow', methods=['GET', 'POST'])
@app.route('/add_borrow/<int:book_id>', methods=['GET', 'POST'])
def add_borrow(book_id=None):
    ma_sach = None
    if book_id is not None:
        ma_sach = book_id  # Lấy mã sách tự động nếu có book_id

    if request.method == 'POST':
        id_thu_thu = request.form['id_thu_thu']
        id_docgia = request.form['id_docgia']
        ma_sach = request.form['ma_sach']  # Lấy mã sách từ form
        ngay_muon = request.form['ngay_muon']
        
        # Tính ngày trả (giả sử 60 ngày sau ngày mượn)
        ngay_tra = (datetime.strptime(ngay_muon, '%Y-%m-%d') + timedelta(days=60)).date()
        
        # Xác định trạng thái của phiếu mượn
        ngay_hien_tai = datetime.now().date()
        if ngay_hien_tai > ngay_tra:
            trang_thai = 'Quá Hạn'
            so_ngay_qua_han = (ngay_hien_tai - ngay_tra).days
            tien_phat = so_ngay_qua_han * 5000  # 5.000 VNĐ mỗi ngày
        else:
            trang_thai = 'Đang Mượn'
            tien_phat = 0
        
        conn = sqlite3.connect('thuvien.db')
        cur = conn.cursor()
        
        try:
            # Thêm phiếu mượn vào cơ sở dữ liệu
            cur.execute('''INSERT INTO muon_sach (id_thu_thu, id_docgia, ma_sach, ngay_muon, ngay_tra, trang_thai, tien_phat)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (id_thu_thu, id_docgia, ma_sach, ngay_muon, ngay_tra, trang_thai, tien_phat))
            conn.commit()
            
            # Giảm số lượng sách trong bảng sách
            cur.execute('''UPDATE sach SET so_luong = so_luong - 1 WHERE ma_sach = ?''', (ma_sach,))
            conn.commit()

            flash('Thêm phiếu mượn thành công!')  # Sử dụng flash để gửi thông báo
            return redirect(url_for('list_borrows'))  # Chuyển hướng đến danh sách phiếu mượn
        except Exception as e:
            flash(f'Đã xảy ra lỗi: {e}')  # Ghi lại lỗi
        finally:
            conn.close()
    
    return render_template('add_borrow.html', ma_sach=ma_sach)


@app.route('/list_borrows', methods=['GET'])
def list_borrows():
    query = request.args.get('query', '').lower()  # Chuyển query về chữ thường
    message = request.args.get('message', '')  # Khởi tạo biến message từ query parameters
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()

    # Tìm kiếm phiếu mượn
    if query:
        cur.execute(''' 
            SELECT * FROM muon_sach 
            WHERE LOWER(id_docgia) LIKE ? OR LOWER(ma_sach) LIKE ? OR LOWER(trang_thai) LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    else:
        cur.execute('SELECT * FROM muon_sach')

    borrows = cur.fetchall()
    
    # Phân trang
    page = request.args.get('page', 1, type=int)  # Lấy số trang hiện tại từ query parameters
    per_page = 5  # Số lượng phiếu mượn trên mỗi trang
    total_borrows = len(borrows)  # Tổng số phiếu mượn
    total_pages = (total_borrows + per_page - 1) // per_page  # Tổng số trang
    start = (page - 1) * per_page  # Vị trí bắt đầu
    end = start + per_page  # Vị trí kết thúc
    borrows_to_display = borrows[start:end]  # Danh sách phiếu mượn cần hiển thị
    
    # Cập nhật trạng thái cho mỗi phiếu mượn
    updated_borrows = []
    for borrow in borrows_to_display:
        id_muon = borrow[0]
        status = check_borrow_status(id_muon)
        updated_borrows.append(borrow + (status,))

    conn.close()

    return render_template('list_borrows.html', borrows=updated_borrows, query=query, message=message,
                           page=page, total_pages=total_pages, total_borrows=total_borrows)

# Chỉnh sửa phiếu mượn
@app.route('/edit_borrow/<int:id_muon>', methods=['GET', 'POST'])
def edit_borrow(id_muon):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()

    # Lấy thông tin phiếu mượn dựa trên id_muon
    cur.execute('SELECT * FROM muon_sach WHERE id_muon = ?', (id_muon,))
    borrow = cur.fetchone()

    if request.method == 'POST':
        id_thu_thu = request.form['id_thu_thu']
        id_docgia = request.form['id_docgia']
        ma_sach = request.form['ma_sach']
        ngay_muon = request.form['ngay_muon']
        ngay_tra = request.form['ngay_tra']

        # Cập nhật phiếu mượn
        cur.execute(''' 
            UPDATE muon_sach 
            SET id_thu_thu = ?, id_docgia = ?, ma_sach = ?, ngay_muon = ?, ngay_tra = ?
            WHERE id_muon = ? 
        ''', (id_thu_thu, id_docgia, ma_sach, ngay_muon, ngay_tra, id_muon))

        conn.commit()
        conn.close()

        return redirect(url_for('list_borrows', message='Cập nhật phiếu mượn thành công'))

    conn.close()
    return render_template('edit_borrow.html', borrow=borrow)

# Xóa phiếu mượn
@app.route('/delete_borrow/<int:id_muon>', methods=['POST'])
def delete_borrow(id_muon):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()

    # Xoá phiếu mượn dựa trên id_muon
    cur.execute('DELETE FROM muon_sach WHERE id_muon = ?', (id_muon,))
    conn.commit()
    conn.close()

    return redirect(url_for('list_borrows', message='Đã xoá phiếu mượn thành công'))

# Trả sách
@app.route('/return_borrow/<int:id_muon>', methods=['POST'])
def return_borrow(id_muon):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    
    try:
        # Cập nhật trạng thái phiếu mượn và tiền phạt nếu cần
        cur.execute('''UPDATE muon_sach SET trang_thai = 'Đã Trả', ngay_tra = ? WHERE id_muon = ?''',
                    (datetime.now().date(), id_muon))
        conn.commit()
        
        # Lấy mã sách từ phiếu mượn
        cur.execute('SELECT ma_sach FROM muon_sach WHERE id_muon = ?', (id_muon,))
        ma_sach = cur.fetchone()
        
        if ma_sach:
            # Tăng số lượng sách trong bảng sách
            cur.execute('''UPDATE sach SET so_luong = so_luong + 1 WHERE ma_sach = ?''', (ma_sach[0],))
            conn.commit()
        
        message = 'Trả sách thành công!'
    except Exception as e:
        message = f'Đã xảy ra lỗi: {e}'
    finally:
        conn.close()
    
    return redirect(url_for('list_borrows', message=message))

def check_borrow_status(id_muon):
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    cur.execute('SELECT ngay_muon, ngay_tra, ngay_tra FROM muon_sach WHERE id_muon = ?', (id_muon,))
    record = cur.fetchone()
    
    if record:
        ngay_muon, ngay_tra, ngay_tra = record
        ngay_hien_tai = datetime.now().date()
        
        if ngay_tra:
            return "Đã trả"
        
        if ngay_hien_tai <= datetime.strptime(ngay_tra, '%Y-%m-%d').date():
            return "Đang mượn"
        else:
            return "Quá hạn"
    
    conn.close()
    return "Không tìm thấy dữ liệu"

@app.route('/librarians', methods=['GET'])
def librarians():
    if session.get('user_role') != 'Quản trị viên':
        return "Bạn không có quyền truy cập trang này.", 403
    
    query = request.args.get('query', '').lower()  # Chuyển từ khóa tìm kiếm thành chữ thường
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    
    # Truy vấn có điều kiện nếu có từ khóa tìm kiếm
    if query:
        cur.execute('''
            SELECT id_thu_thu, ten, email, sdt, ngay_sinh, que_quan 
            FROM thu_thu 
            WHERE LOWER(ten) LIKE ? OR LOWER(email) LIKE ? OR LOWER(sdt) LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    else:
        cur.execute('SELECT id_thu_thu, ten, email, sdt, ngay_sinh, que_quan FROM thu_thu')

    librarians = cur.fetchall()
    
    # Phân trang
    page = request.args.get('page', 1, type=int)  # Lấy số trang hiện tại từ query parameters
    per_page = 5  # Số lượng thủ thư trên mỗi trang
    
    total_librarians = len(librarians)  # Tổng số thủ thư
    total_pages = (total_librarians + per_page - 1) // per_page  # Tổng số trang
    
    start = (page - 1) * per_page  # Vị trí bắt đầu
    end = start + per_page  # Vị trí kết thúc
    librarians_to_display = librarians[start:end]  # Danh sách thủ thư cần hiển thị

    conn.close()

    return render_template('librarians.html', librarians=librarians_to_display, 
                           query=query, page=page, total_pages=total_pages, total_librarians=total_librarians)

# Thêm thủ thư
@app.route('/librarians/add', methods=['GET', 'POST'])
def add_librarian():
    if session.get('user_role') != 'Quản trị viên':
        return "Bạn không có quyền truy cập trang này.", 403
    if request.method == 'POST':
        ten = request.form['ten']
        email = request.form['email']
        sdt = request.form['sdt']
        ngay_sinh = request.form['ngay_sinh']
        que_quan = request.form['que_quan']
        
        conn = sqlite3.connect('thuvien.db')
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO thu_thu (ten, email, sdt, ngay_sinh, que_quan)
                VALUES (?, ?, ?, ?, ?)
            ''', (ten, email, sdt, ngay_sinh, que_quan))
            conn.commit()
            message = 'Thêm thủ thư thành công!'
        except Exception as e:
            message = f'Đã xảy ra lỗi: {e}'
        finally:
            conn.close()
        
        return redirect(url_for('librarians', message=message))
    
    return render_template('add_librarians.html')

# Xoá thủ thư
@app.route('/librarians/delete/<int:id_thu_thu>')
def delete_librarian(id_thu_thu):
    if session.get('user_role') != 'Quản trị viên':
        return "Bạn không có quyền truy cập trang này.", 403
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM thu_thu WHERE id_thu_thu = ?', (id_thu_thu,))
        conn.commit()
        message = 'Xóa thủ thư thành công!'
    except Exception as e:
        message = f'Đã xảy ra lỗi: {e}'
    finally:
        conn.close()
    
    return redirect(url_for('librarians', message=message))

# Sửa thủ thư
@app.route('/edit_librarian/<int:id_thu_thu>', methods=['GET', 'POST'])
def edit_librarian(id_thu_thu):
    if session.get('user_role') != 'Quản trị viên':
        return "Bạn không có quyền truy cập trang này.", 403
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    
    if request.method == 'POST':
        ten = request.form['ten']
        email = request.form['email']
        sdt = request.form['sdt']
        ngay_sinh = request.form['ngay_sinh']
        que_quan = request.form['que_quan']
        
        try:
            cur.execute('''
                UPDATE thu_thu
                SET ten = ?, email = ?, sdt = ?, ngay_sinh = ?, que_quan = ?
                WHERE id_thu_thu = ?
            ''', (ten, email, sdt, ngay_sinh, que_quan, id_thu_thu))
            conn.commit()
            message = 'Cập nhật thông tin thủ thư thành công!'
        except Exception as e:
            message = f'Đã xảy ra lỗi: {e}'
        finally:
            conn.close()
        
        return redirect(url_for('librarians', message=message))
    
    cur.execute('SELECT * FROM thu_thu WHERE id_thu_thu = ?', (id_thu_thu,))
    librarian = cur.fetchone()
    conn.close()
    
    return render_template('edit_librarians.html', librarian=librarian)

@app.route('/admins')
def admins():
    conn = get_db_connection()
    admins = conn.execute('SELECT * FROM quan_tri_vien').fetchall()
    conn.close()
    return render_template('admins.html', admins=admins)

@app.route('/generate_statistics', methods=['GET'])
def generate_statistics():
    statistic_type = request.args.get('statistic_type')
    statistics = None

    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect('thuvien.db')
    cur = conn.cursor()
    # Logic để tính toán thống kê dựa trên statistic_type
    if statistic_type == 'total_books':
        # Truy vấn tổng số sách
        cur.execute('SELECT COUNT(*) FROM sach')
        statistics = cur.fetchone()[0]
    elif statistic_type == 'total_members':
        # Truy vấn tổng số độc giả
        cur.execute('SELECT COUNT(*) FROM doc_Gia')
        statistics = cur.fetchone()[0]
    elif statistic_type == 'total_borrows':
        # Truy vấn tổng số phiếu mượn
        cur.execute('SELECT COUNT(*) FROM muon_sach')
        statistics = cur.fetchone()[0]
    elif statistic_type == 'books_by_genre':
        # Số lượng sách theo thể loại
        cur.execute('SELECT loai_sach, COUNT(*) FROM sach GROUP BY loai_sach')
        statistics = cur.fetchall()
    elif statistic_type == 'books_by_author':
        # Số lượng sách theo tác giả
        cur.execute('SELECT ten_TG, COUNT(*) FROM sach GROUP BY ten_TG')
        statistics = cur.fetchall()
    elif statistic_type == 'overdue_books':
        # Số lượng sách quá hạn
        cur.execute('SELECT COUNT(*) FROM muon_sach WHERE trang_thai = "Quá Hạn"')
        statistics = cur.fetchone()[0]
    # Đóng kết nối
    conn.close()

    # Render kết quả thống kê
    return render_template('statistics.html', statistics=statistics, statistic_type=statistic_type)



if __name__ == '__main__':
    app.run(debug=True)
