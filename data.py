import sqlite3, bcrypt

# Kết nối tới cơ sở dữ liệu SQLite
conn = sqlite3.connect('thuvien.db')
cur = conn.cursor()

# Xóa bảng nếu đã tồn tại (Chỉ để phát triển, không nên làm trong môi trường sản xuất)
cur.execute('DROP TABLE IF EXISTS nguoi_dung')
cur.execute('DROP TABLE IF EXISTS phan_quyen')
cur.execute('DROP TABLE IF EXISTS quyen_nguoi_dung')
cur.execute('DROP TABLE IF EXISTS thu_thu')

# Tạo bảng Người dùng
cur.execute('''
CREATE TABLE IF NOT EXISTS nguoi_dung (
    ma_nguoi_dung INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    mat_khau TEXT NOT NULL,
    loai INTEGER NOT NULL
)
''')

# Mã hóa mật khẩu
mat_khau = '123456'
hashed_password = bcrypt.hashpw(mat_khau.encode('utf-8'), bcrypt.gensalt())

# Thêm Quản trị viên vào bảng nguoi_dung
cur.execute('''
INSERT INTO nguoi_dung (ten, email, mat_khau, loai) 
VALUES (?, ?, ?, ?)
''', ('Phạm Thị Kim Dung', 'dungkimkim@gmail.com', hashed_password, 1))  # 1 là mã quyền cho Quản trị viên

# Tạo bảng Quyền hạn
cur.execute('''
CREATE TABLE IF NOT EXISTS phan_quyen (
    ma_quyen INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_quyen TEXT NOT NULL
)
''')

# Thêm các quyền hạn vào bảng phan_quyen
quyen = [
    ('Quản trị viên',),
    ('Thủ thư',),
    ('Độc giả',)
    
]
cur.executemany('INSERT INTO phan_quyen (ten_quyen) VALUES (?)', quyen)

# Tạo bảng Độc Giả
cur.execute('''
CREATE TABLE IF NOT EXISTS doc_Gia (
    id_docgia INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_docgia TEXT NOT NULL,
    ngay_sinh DATE,
    so_CMND TEXT NOT NULL,
    so_DT TEXT,
    ngay_HHT DATE,
    dia_Chi TEXT
)
''')

# Tạo bảng Sách
cur.execute('''
CREATE TABLE IF NOT EXISTS sach (
    ma_sach INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_sach TEXT NOT NULL,
    ten_TG TEXT,
    nha_XB TEXT,
    nam_XB INTEGER,
    loai_sach TEXT,
    so_luong INTEGER,
    so_trang INTEGER,
    so_tien INTEGER,  
    vi_tri TEXT      
)
''')

# Tạo bảng Thủ thư
cur.execute('''
CREATE TABLE IF NOT EXISTS thu_thu (
    id_thu_thu INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    email TEXT NOT NULL,
    sdt TEXT,
    ngay_sinh DATE,
    que_quan TEXT
)
''')

# Tạo bảng Mượn sách
cur.execute('''
CREATE TABLE IF NOT EXISTS muon_sach (
    id_muon INTEGER PRIMARY KEY AUTOINCREMENT,
    id_thu_thu INTEGER,
    id_docgia INTEGER,
    ma_sach INTEGER,
    ngay_muon DATE,
    ngay_tra DATE,
    trang_thai TEXT CHECK(trang_thai IN ('Đang Mượn', 'Đã Trả', 'Quá Hạn')),
    tien_phat INTEGER DEFAULT 0,
    FOREIGN KEY (id_docgia) REFERENCES doc_Gia (id_docgia),
    FOREIGN KEY (ma_sach) REFERENCES sach (ma_sach),
    FOREIGN KEY (id_thu_thu) REFERENCES thu_thu (id_thu_thu)
)
''')

# Tạo bảng Liên kết quyền của người dùng (bao gồm thủ thư và quản trị viên)
cur.execute('''
CREATE TABLE IF NOT EXISTS quyen_nguoi_dung (
    ma_nguoi_dung INTEGER,
    ma_quyen INTEGER,
    FOREIGN KEY (ma_nguoi_dung) REFERENCES nguoi_dung (ma_nguoi_dung),
    FOREIGN KEY (ma_quyen) REFERENCES phan_quyen (ma_quyen),
    PRIMARY KEY (ma_nguoi_dung, ma_quyen)
)
''')

# Lưu thay đổi và đóng kết nối
conn.commit()
conn.close()
