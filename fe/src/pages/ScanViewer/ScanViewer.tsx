import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { AlertCircle } from "lucide-react";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";
import "./ScanViewer.css";

interface ScanResult {
  id: string;
  original_filename: string;
  image_path: string;
  processed_image_path?: string;
  status: string;
  document_type: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ocr_json: any;
  html_content: string;
  created_at: string;
}

const WarningIcon = ({ score }: { score?: number }) => {
  if (score === undefined || score === null || score >= 0.8) return null;
  return (
    <span title={`Độ tin cậy thấp: ${(score * 100).toFixed(1)}%`} className="inline-flex items-center ml-2 text-destructive">
      <AlertCircle className="w-4 h-4" />
    </span>
  );
};

export default function ScanViewer() {
  const { id } = useParams();
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [hoveredBbox, setHoveredBbox] = useState<number[] | null>(null);

  // Dimensions for bbox scaling
  const [imgNaturalSize, setImgNaturalSize] = useState({ w: 1, h: 1 });
  const [imgRenderSize, setImgRenderSize] = useState({ w: 1, h: 1 });

  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!imgRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          setImgRenderSize({ w: entry.contentRect.width, h: entry.contentRect.height });
        }
      }
    });
    observer.observe(imgRef.current);
    return () => observer.disconnect();
  }, [scan]);

  const { t } = useTranslation();

  useEffect(() => {
    const fetchScan = async () => {
      try {
        const res = await axiosClient.get(`/api/scan/${id}`);
        setScan(res.data);
      } catch (error) {
        console.error("Failed to fetch scan details", error);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchScan();
  }, [id]);

  if (loading) return <div className="p-8">{t('dashboard.table.loading')}</div>;
  if (!scan) return <div className="p-8">{t('scan.detail.not_found')}</div>;

  const ocrJson = scan.ocr_json || {};
  const tableBbox = ocrJson.table_bbox;
  const tableScore = ocrJson.table_score;
  const bboxImageUrl = ocrJson.bbox_image_url;

  // Calculate scaled box coordinates
  // box = [x_min, y_min, x_max, y_max]
  const renderBbox = (box: number[] | null) => {
    if (!box) return null;
    const scaleX = imgRenderSize.w / imgNaturalSize.w;
    const scaleY = imgRenderSize.h / imgNaturalSize.h;

    const left = box[0] * scaleX;
    const top = box[1] * scaleY;
    const width = (box[2] - box[0]) * scaleX;
    const height = (box[3] - box[1]) * scaleY;

    return (
      <div
        className="absolute border-2 border-primary bg-primary/20 pointer-events-none transition-all duration-200"
        style={{ left, top, width, height }}
      />
    );
  };

  const API_URL = "http://127.0.0.1:8000"; // Should come from config
  // Use bbox_image_url for Paddle layout image if available, else original image
  const defaultImageUrl = scan.image_path.startsWith("http") ? scan.image_path : `${API_URL}/${scan.image_path}`;
  const paddleBboxUrl = bboxImageUrl ? (bboxImageUrl.startsWith("http") ? bboxImageUrl : `${API_URL}${bboxImageUrl}`) : defaultImageUrl;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] overflow-hidden">
      <div className="mb-4">
        <h1 className="text-2xl font-bold tracking-tight">{t('scan.detail.title')} {scan.original_filename}</h1>
        <div className="flex gap-2 mt-2">
          <Badge variant={scan.status === 'completed' ? 'default' : 'secondary'}>
            {scan.status.toUpperCase()}
          </Badge>
          <Badge variant="outline">{scan.document_type}</Badge>
        </div>
      </div>

      <div className="flex-1 grid md:grid-cols-2 gap-6 min-h-0">
        {/* LEFT PANEL: Image Viewer */}
        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="py-3 px-4 border-b flex-shrink-0">
            <CardTitle className="text-sm">{t('scan.detail.original_img')}</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0 flex flex-col overflow-hidden bg-muted/30">
            <Tabs defaultValue="default" className="flex flex-col h-full overflow-hidden">
              <div className="px-4 py-2 border-b flex-shrink-0">
                <TabsList>
                  <TabsTrigger value="default">{t('scan.detail.default_mode')}</TabsTrigger>
                  <TabsTrigger value="paddle" disabled={!bboxImageUrl}>{t('scan.detail.paddle_mode')}</TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="default" className="flex-1 overflow-auto m-0 p-4 data-[state=active]:flex data-[state=active]:items-start data-[state=active]:justify-center">
                <div className="relative inline-block max-w-full">
                  <img
                    ref={imgRef}
                    src={defaultImageUrl}
                    alt="Original document"
                    className="max-w-full h-auto shadow-md"
                    onLoad={(e) => {
                      const img = e.currentTarget;
                      setImgNaturalSize({ w: img.naturalWidth, h: img.naturalHeight });
                      setImgRenderSize({ w: img.width, h: img.height });
                    }}
                  />
                  {renderBbox(hoveredBbox)}
                </div>
              </TabsContent>

              <TabsContent value="paddle" className="flex-1 overflow-auto m-0 p-4 data-[state=active]:flex data-[state=active]:items-start data-[state=active]:justify-center">
                <img
                  src={paddleBboxUrl}
                  alt="PaddleOCR BBox Result"
                  className="max-w-full h-auto shadow-md"
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* RIGHT PANEL: Data Viewer */}
        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="py-3 px-4 border-b flex-shrink-0">
            <CardTitle className="text-sm">{t('scan.detail.extract_result')}</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto p-4 space-y-4">

            {/* Header: Số phiếu + Ngày */}
            <div className="grid grid-cols-2 gap-3">
              <div
                className="bg-card border rounded p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                onMouseEnter={() => setHoveredBbox(ocrJson.form_no_bbox || null)}
                onMouseLeave={() => setHoveredBbox(null)}
              >
                <div className="text-sm text-muted-foreground mb-1">{t('scan.detail.form_no')}</div>
                <div className="font-semibold flex items-center">
                  {ocrJson.form_no || "N/A"}
                  {ocrJson.form_no_score !== undefined && <WarningIcon score={ocrJson.form_no_score} />}
                </div>
              </div>

              <div
                className="bg-card border rounded p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                onMouseEnter={() => setHoveredBbox(ocrJson.ngay_bbox || null)}
                onMouseLeave={() => setHoveredBbox(null)}
              >
                <div className="text-sm text-muted-foreground mb-1">{t('scan.detail.date')}</div>
                <div className="font-semibold flex items-center">
                  {ocrJson.ngay || "N/A"}
                  {ocrJson.ngay_score !== undefined && <WarningIcon score={ocrJson.ngay_score} />}
                </div>
              </div>
            </div>

            {/* Bảng chi tiết phiếu - thiết kế giống mẫu gốc */}
            <div
              className="border rounded-md overflow-hidden"
              onMouseEnter={() => setHoveredBbox(tableBbox || null)}
              onMouseLeave={() => setHoveredBbox(null)}
            >
              <div className="flex items-center justify-between px-3 py-2 bg-muted/40 border-b">
                <h3 className="text-sm font-semibold flex items-center gap-1">
                  {t('scan.detail.table')}
                  <WarningIcon score={tableScore} />
                </h3>
              </div>

              <div className="overflow-x-auto">
                {/* Hàng 1: Info fields - 單位 / Họ tên / Số thẻ / Chủ quản */}
                <table
                  className="w-full border-collapse text-base hover:bg-muted/10 transition-colors cursor-pointer"
                  onMouseEnter={(e) => { e.stopPropagation(); setHoveredBbox(ocrJson.info_bbox || tableBbox || null); }}
                  onMouseLeave={(e) => { e.stopPropagation(); setHoveredBbox(tableBbox || null); }}
                >
                  <thead>
                    <tr className="bg-muted/20">
                      <th className="border px-3 py-2 text-left w-1/4">
                        <div className="font-bold text-sm text-center">單位</div>
                        <div className="text-sm text-muted-foreground text-center">Đơn vị:</div>
                      </th>
                      <th className="border px-3 py-2 text-left w-1/4">
                        <div className="font-bold text-sm text-center">姓名</div>
                        <div className="text-sm text-muted-foreground text-center">Họ tên:</div>
                      </th>
                      <th className="border px-3 py-2 text-left w-1/4">
                        <div className="font-bold text-sm text-center">卡號</div>
                        <div className="text-sm text-muted-foreground text-center">Số thẻ:</div>
                      </th>
                      <th className="border px-3 py-2 text-left w-1/4">
                        <div className="font-bold text-sm text-center">主管</div>
                        <div className="text-sm text-muted-foreground text-center">Chủ quản:</div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border px-3 py-3 font-medium">{ocrJson.info?.don_vi || ""}</td>
                      <td className="border px-3 py-3 font-medium">{ocrJson.info?.ho_ten || ""}</td>
                      <td className="border px-3 py-3 font-medium">{ocrJson.info?.so_the || ""}</td>
                      <td className="border px-3 py-3 font-medium">{ocrJson.info?.chu_quan || ""}</td>
                    </tr>
                  </tbody>
                </table>

                {/* Line items table */}
                <table className="w-full border-collapse text-base">
                  <thead>
                    <tr className="bg-muted/20">
                      <th className="border px-3 py-2 text-center w-10">
                        <div className="font-bold text-sm">序號</div>
                        <div className="text-sm text-muted-foreground">STT</div>
                      </th>
                      <th className="border px-3 py-2 text-center">
                        <div className="font-bold text-sm">項目</div>
                        <div className="text-sm text-muted-foreground">Hạng mục</div>
                      </th>
                      <th className="border px-3 py-2 text-center">
                        <div className="font-bold text-sm">用途說明</div>
                        <div className="text-sm text-muted-foreground">Mục đích sử dụng</div>
                      </th>
                      <th className="border px-3 py-2 text-center">
                        <div className="font-bold text-sm">數量單價</div>
                        <div className="text-sm text-muted-foreground">Số lượng x Đơn giá</div>
                      </th>
                      <th className="border px-3 py-2 text-center">
                        <div className="font-bold text-sm">金額</div>
                        <div className="text-sm text-muted-foreground">Số tiền</div>
                      </th>
                      <th className="border px-3 py-2 text-center">
                        <div className="font-bold text-sm">單據號碼</div>
                        <div className="text-sm text-muted-foreground">Số chứng từ</div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {(ocrJson.line_items || []).length === 0 ? (
                      <tr>
                        <td colSpan={6} className="border px-3 py-4 text-center text-muted-foreground italic text-xs">
                          {t('scan.detail.no_table')}
                        </td>
                      </tr>
                    ) : (
                      (ocrJson.line_items || []).map((item: Record<string, string>, idx: number) => (
                        <tr key={idx} className="hover:bg-muted/20">
                          <td className="border px-3 py-3 text-center">{idx + 1}</td>
                          <td className="border px-3 py-3 text-center">{item.hang_muc || ""}</td>
                          <td className="border px-3 py-3 text-center">{item.muc_dich || ""}</td>
                          <td className="border px-3 py-3 text-center">{item.so_luong_don_gia || ""}</td>
                          <td className="border px-3 py-3 text-center font-medium">{item.so_tien || ""}</td>
                          <td className="border px-3 py-3 text-center">{item.so_chung_tu || ""}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>

                {/* Footer rows */}
                <table className="w-full border-collapse text-base">
                  <tbody>
                    <tr className="bg-muted/10">
                      <td className="border px-3 py-3 w-1/4">
                        <div className="text-sm font-bold text-center">預支金額</div>
                        <div className="text-sm text-muted-foreground text-center">Số tiền tạm ứng</div>
                        <div className="font-semibold mt-1 text-center">{ocrJson.footer?.so_tien_tam_ung || ""}</div>
                      </td>
                      <td className="border px-3 py-3 w-1/4">
                        <div className="text-sm font-bold text-center">簽收</div>
                        <div className="text-sm text-muted-foreground text-center">Ký nhận</div>
                        <div className="mt-1">{ocrJson.footer?.ky_nhan || ""}</div>
                      </td>
                      <td className="border px-3 py-3 w-1/4">
                        <div className="text-sm font-bold text-center">實支</div>
                        <div className="text-sm text-muted-foreground text-center">Thực chi</div>
                        <div className="mt-1 text-center">{ocrJson.footer?.thuc_chi || ""}</div>
                      </td>
                      <td className="border px-3 py-3 w-1/4">
                        <div className="text-xs text-center">[ ] 補 Bố sung</div>
                        <div className="text-xs text-center">[ ] 退 Trả lại</div>
                      </td>
                    </tr>
                    <tr className="bg-muted/10">
                      <td className="border px-3 py-3">
                        <div className="text-sm font-bold text-center">總經理</div>
                        <div className="text-sm text-muted-foreground text-center">Tổng Giám Đốc</div>
                        <div className="mt-1 text-center">{ocrJson.footer?.tong_giam_doc || ""}</div>
                      </td>
                      <td className="border px-3 py-3">
                        <div className="text-sm font-bold text-center">出納</div>
                        <div className="text-sm text-muted-foreground text-center">Thủ quỹ</div>
                        <div className="mt-1 text-center">{ocrJson.footer?.thu_quy_1 || ""}</div>
                      </td>
                      <td className="border px-3 py-3">
                        <div className="text-sm font-bold text-center">會計</div>
                        <div className="text-sm text-muted-foreground text-center">Kế toán</div>
                        <div className="mt-1 text-center">{ocrJson.footer?.ke_toan || ""}</div>
                      </td>
                      <td className="border px-3 py-3">
                        <div className="text-sm font-bold text-center">出納</div>
                        <div className="text-sm text-muted-foreground text-center">Thủ quỹ</div>
                        <div className="mt-1 text-center">{ocrJson.footer?.thu_quy_2 || ""}</div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </CardContent>
        </Card>
      </div>
    </div>
  );
}
