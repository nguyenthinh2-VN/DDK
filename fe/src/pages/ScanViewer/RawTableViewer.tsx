/**
 * RawTableViewer - Hiển thị bảng HTML thô từ PaddleOCR.
 *
 * Nhận `html_content` từ BE (đã là block_content sạch) và render trực tiếp.
 * Không parse lại - tránh lỗi \n và thiếu dòng.
 */
import "./RawTableViewer.css";

interface RawTableViewerProps {
  htmlContent: string; // scan.html_content từ API
}

export default function RawTableViewer({ htmlContent }: RawTableViewerProps) {
  if (!htmlContent) {
    return (
      <div className="p-6 text-center text-muted-foreground italic text-sm">
        Chưa có dữ liệu bảng từ OCR.
      </div>
    );
  }

  return (
    <div className="raw-table-wrapper overflow-x-auto">
      <div
        className="raw-table-content"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    </div>
  );
}
