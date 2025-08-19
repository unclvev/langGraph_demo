CATALOGS = [
    {
        "intent": "lich_trinh",
        "entities": [
            {"name": "thoi_gian_di", "required": True},
            {"name": "thoi_gian_ve", "required": False},
            {"name": "dia_diem", "required": True},
            {"name": "diem_di", "required": True},
            {"name": "so_nguoi", "required": True},
            {"name": "chi_phi", "required": True},
            {"name": "muc_tieu", "required": False},
        ],
    },
    {
        "intent": "dat_ve_may_bay",
        "entities": [
            {"name": "thoi_gian_di", "required": True},
            {"name": "dia_diem", "required": True},
            {"name": "gia_ve_may_bay", "required": True},
            {"name": "diem_di", "required": True},
            {"name": "hang_ve", "required": True},
            {"name": "hang_bay", "required": False},
            {"name": "so_nguoi", "required": True},
            {"name": "khu_hoi", "required": True},
            {"name": "thoi_gian_ve", "required_if": {"field": "khu_hoi", "value": "khứ hồi"}},
        ],
    },
    {
        "intent": "dat_khach_san",
        "entities": [
            {"name": "dia_diem", "required": True},
            {"name": "checkin", "required": True},
            {"name": "checkout", "required": True},
            {"name": "so_phong", "required": True},
            {"name": "so_nguoi", "required": True},
            {"name": "kieu_loai", "required": True},
            {"name": "gia_khach_san", "required": True},
            {"name": "mo_ta_yeu_cau", "required": False},
        ],
    },
]
