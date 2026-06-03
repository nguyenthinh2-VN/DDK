import { useState, useEffect, useCallback } from 'react';

const dictionary: Record<string, Record<string, string>> = {
  vi: {
    'dashboard.title': 'Trang chủ',
    'dashboard.welcome': 'Chào mừng {name} đã quay trở lại.',
    'dashboard.total_files': 'Tổng số file upload',
    'dashboard.total_success': 'Tổng số phiếu thành công',
    'dashboard.total_error': 'Tổng số phiếu lỗi',
    'dashboard.recent_scans': 'Danh sách phiếu Scan gần đây',
    'dashboard.table.filename': 'Tên file',
    'dashboard.table.type': 'Loại phiếu',
    'dashboard.table.status': 'Trạng thái',
    'dashboard.table.time': 'Thời gian upload',
    'dashboard.table.loading': 'Đang tải dữ liệu...',
    'dashboard.table.empty': 'Chưa có phiếu scan nào.',
    'scan.detail.title': 'Chi tiết phiếu:',
    'scan.detail.original_img': 'Ảnh Phiếu Gốc',
    'scan.detail.extract_result': 'Kết quả trích xuất',
    'scan.detail.default_mode': 'Mặc định (Tương tác)',
    'scan.detail.paddle_mode': 'Bbox PaddleOCR',
    'scan.detail.form_no': 'Số phiếu',
    'scan.detail.date': 'Ngày tháng',
    'scan.detail.table': 'Bảng chi tiết',
    'scan.detail.no_table': 'Không có dữ liệu bảng.',
    'scan.detail.not_found': 'Không tìm thấy phiếu scan.',
    'layout.menu.dashboard': 'Dashboard',
    'layout.menu.scans': 'Danh sách phiếu (Scan)',
    'layout.menu.upload': 'Upload',
    'layout.header.title': 'Hệ thống xử lý Phiếu tạm ứng',
    'scans.title': 'Danh sách phiếu Scan',
    'scans.desc': 'Quản lý tất cả các phiếu đã được tải lên hệ thống.',
    'scans.btn.upload': 'Upload mới',
    'scans.card.title': 'Tất cả phiếu',
    'scans.confirm.delete': 'Bạn có chắc chắn muốn xoá phiếu này?',
    'scans.alert.delete_fail': 'Xoá thất bại.',
    'upload.title': 'Upload Phiếu',
    'upload.desc': 'Tải lên hình ảnh phiếu tạm ứng để hệ thống tự động nhận dạng. Hỗ trợ upload 1 file (xử lý ngay) hoặc 3-5 file (xử lý nền).',
    'upload.card.title': 'Tải file lên',
    'upload.card.desc': 'Hỗ trợ các định dạng ảnh phổ biến: JPG, PNG, JPEG. (Tối đa 5 file)',
    'upload.drag': 'Nhấn để chọn hoặc kéo thả file vào đây',
    'upload.drag_sub': 'Upload 1 file hoặc chọn từ 3-5 file để xử lý Batch (Max 10MB/file)',
    'upload.btn.remove': 'Bỏ chọn',
    'upload.btn.add': '+ Thêm file',
    'upload.btn.submit.loading': 'Đang tải lên...',
    'upload.btn.submit.single': 'Tải lên và Scan ngay',
    'upload.btn.submit.batch': 'Tải lên Batch (Xử lý nền)',
    'upload.alert.max_files': 'Chỉ được upload tối đa 5 file.',
    'upload.alert.min_batch': 'Batch upload yêu cầu từ 3-5 file, hoặc chỉ 1 file cho upload đơn.',
    'upload.alert.fail': 'Tải lên thất bại.',
  },
  tw: {
    'dashboard.title': '首頁',
    'dashboard.welcome': '歡迎 {name} 回來。',
    'dashboard.total_files': '上傳文件總數',
    'dashboard.total_success': '成功掃描總數',
    'dashboard.total_error': '錯誤總數',
    'dashboard.recent_scans': '最近掃描列表',
    'dashboard.table.filename': '檔案名稱',
    'dashboard.table.type': '表單類型',
    'dashboard.table.status': '狀態',
    'dashboard.table.time': '上傳時間',
    'dashboard.table.loading': '載入中...',
    'dashboard.table.empty': '沒有掃描結果。',
    'scan.detail.title': '表格詳情:',
    'scan.detail.original_img': '原始圖片',
    'scan.detail.extract_result': '提取結果',
    'scan.detail.default_mode': '預設 (互動)',
    'scan.detail.paddle_mode': 'Bbox PaddleOCR',
    'scan.detail.form_no': '表單編號',
    'scan.detail.date': '日期',
    'scan.detail.table': '詳細表格',
    'scan.detail.no_table': '沒有表格資料。',
    'scan.detail.not_found': '找不到掃描結果。',
    'layout.menu.dashboard': '首頁',
    'layout.menu.scans': '掃描列表',
    'layout.menu.upload': '上傳',
    'layout.header.title': '預支單處理系統',
    'scans.title': '掃描列表',
    'scans.desc': '管理所有上傳到系統的表格。',
    'scans.btn.upload': '新上傳',
    'scans.card.title': '所有表格',
    'scans.confirm.delete': '您確定要刪除此表格嗎？',
    'scans.alert.delete_fail': '刪除失敗。',
    'upload.title': '上傳表格',
    'upload.desc': '上傳預支單圖片，系統會自動識別。支持單文件（立即處理）或 3-5 個文件（後台處理）。',
    'upload.card.title': '上傳文件',
    'upload.card.desc': '支持常見圖片格式: JPG, PNG, JPEG. (最多 5 個文件)',
    'upload.drag': '點擊選擇或拖放文件到此處',
    'upload.drag_sub': '上傳 1 個文件或選擇 3-5 個文件進行批量處理 (最大 10MB/文件)',
    'upload.btn.remove': '移除',
    'upload.btn.add': '+ 添加文件',
    'upload.btn.submit.loading': '上傳中...',
    'upload.btn.submit.single': '立即上傳並掃描',
    'upload.btn.submit.batch': '批量上傳 (後台處理)',
    'upload.alert.max_files': '最多只能上傳 5 個文件。',
    'upload.alert.min_batch': '批量上傳需要 3-5 個文件，或僅 1 個文件用於單次上傳。',
    'upload.alert.fail': '上傳失敗。',
  }
};

export function useTranslation() {
  const [lang, setLang] = useState(localStorage.getItem('app_language') || 'vi');

  useEffect(() => {
    const handleStorageChange = () => {
      setLang(localStorage.getItem('app_language') || 'vi');
    };
    
    // Listen for custom event or storage change
    window.addEventListener('storage', handleStorageChange);
    // Add custom event listener for same-window updates
    window.addEventListener('languageChange', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('languageChange', handleStorageChange);
    };
  }, []);

  const t = useCallback((key: string, params?: Record<string, string>) => {
    let text = dictionary[lang]?.[key] || dictionary['vi']?.[key] || key;
    
    if (params) {
      Object.keys(params).forEach(k => {
        text = text.replace(`{${k}}`, params[k]);
      });
    }
    
    return text;
  }, [lang]);

  return { t, lang };
}
