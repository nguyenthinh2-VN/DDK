import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { AlertCircle, Pencil, Save, X, Stamp, Ban, CheckCircle2, Trash2 } from "lucide-react";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import "./ScanViewer.css";

const getFileUrl = (filePath?: string) => {
  if (!filePath) return "";
  if (filePath.startsWith("http")) return filePath;
  const base = axiosClient.defaults.baseURL || window.location.origin;
  return new URL(filePath, base).toString();
};

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
  workflow_status: string;
  current_assignee_role?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  approvals?: any[];
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

  const { user } = useAuth();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [mySignatures, setMySignatures] = useState<any[]>([]);
  const [showSignatureSelector, setShowSignatureSelector] = useState(false);
  const [activeSignRole, setActiveSignRole] = useState<string>("");
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectNote, setRejectNote] = useState("");
  const { toast } = useToast();

  // ── Edit Mode States ────────────────────────────────
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [editedJson, setEditedJson] = useState<any>(null);
  const [saveMessage, setSaveMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

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
    observer.observe(imgRef.current);
    return () => observer.disconnect();
  }, [scan]);

  const { t } = useTranslation();

  useEffect(() => {
    const fetchSignatures = async () => {
      try {
        const res = await axiosClient.get("/api/signatures/me");
        setMySignatures(res.data || []);
      } catch (error) {
        console.error("No active signature", error);
      }
    };
    if (user) fetchSignatures();
  }, [user]);

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

  // ── Edit Mode Handlers ──────────────────────────────

  const handleStartEdit = () => {
    if (!scan) return;
    // Deep clone ocr_json để không mutate trực tiếp state gốc
    setEditedJson(JSON.parse(JSON.stringify(scan.ocr_json || {})));
    setIsEditing(true);
    setSaveMessage(null);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedJson(null);
    setSaveMessage(null);
  };

  // Cập nhật field cấp 1 (form_no, ngay)
  const handleFieldChange = (field: string, value: string) => {
    setEditedJson((prev: Record<string, unknown>) => ({ ...prev, [field]: value }));
  };

  // Cập nhật field trong info object (don_vi, ho_ten, so_the, chu_quan)
  const handleInfoChange = (field: string, value: string) => {
    setEditedJson((prev: Record<string, unknown>) => ({
      ...prev,
      info: { ...(prev.info as Record<string, string>), [field]: value },
    }));
  };

  // Cập nhật field trong footer object
  const handleFooterChange = (field: string, value: string) => {
    setEditedJson((prev: Record<string, unknown>) => ({
      ...prev,
      footer: { ...(prev.footer as Record<string, string>), [field]: value },
    }));
  };

  // Cập nhật một ô trong line_items (mở rộng: index + field)
  const handleUpdateRow = (index: number, field: string, value: string) => {
    setEditedJson((prev: Record<string, unknown>) => {
      const items = [...((prev.line_items as Record<string, string>[]) || [])];
      items[index] = { ...items[index], [field]: value };
      return { ...prev, line_items: items };
    });
  };

  // Hàm mở rộng - thêm dòng mới (chưa hiển thị nút nhưng logic đã sẵn sàng)
  // const handleAddRow = () => {
  //   setEditedJson((prev: Record<string, unknown>) => {
  //     const items = [...((prev.line_items as Record<string, string>[]) || [])];
  //     items.push({ hang_muc: "", muc_dich: "", so_luong_don_gia: "", so_tien: "", so_chung_tu: "" });
  //     return { ...prev, line_items: items };
  //   });
  // };

  // Hàm mở rộng - xóa dòng (chưa hiển thị nút nhưng logic đã sẵn sàng)
  // const handleDeleteRow = (index: number) => {
  //   setEditedJson((prev: Record<string, unknown>) => {
  //     const items = [...((prev.line_items as Record<string, string>[]) || [])];
  //     items.splice(index, 1);
  //     return { ...prev, line_items: items };
  //   });
  // };

  const handleSave = async () => {
    if (!scan || !editedJson) return;
    setIsSaving(true);
    setSaveMessage(null);
    try {
      const res = await axiosClient.put(`/api/scan/${scan.id}/json`, {
        ocr_json: editedJson,
      });
      setScan(res.data);
      setIsEditing(false);
      setEditedJson(null);
      setSaveMessage({ type: "success", text: t("scan.detail.save_success") });
      // Tự động ẩn thông báo thành công sau 3 giây
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error("Failed to save OCR JSON", error);
      setSaveMessage({ type: "error", text: t("scan.detail.save_fail") });
    } finally {
      setIsSaving(false);
    }
  };

  const handleStartSigning = (role: string) => {
    if (mySignatures.length === 0) {
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: t('signature.require_upload'),
      });
      return;
    }
    setActiveSignRole(role);
    setShowSignatureSelector(true);
  };

  const handleSelectSignature = async (signatureId: string) => {
    setShowSignatureSelector(false);
    if (!scan) return;
    try {
      const res = await axiosClient.post(`/api/scan/${scan.id}/signature`, {
        signature_id: signatureId
      });
      setScan(res.data);
      toast({
        title: "Thành công",
        description: t('signature.apply_success'),
      });
    } catch (error: any) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: error.response?.data?.detail || t('signature.apply_fail'),
      });
    }
  };

  const handleRemoveDraftSignature = async () => {
    if (!scan) return;
    try {
      const res = await axiosClient.delete(`/api/scan/${scan.id}/signature`);
      setScan(res.data);
    } catch (error: any) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: error.response?.data?.detail || t('signature.remove_fail'),
      });
    }
  };

  const handleApprove = async () => {
    if (!scan) return;
    try {
      const res = await axiosClient.post(`/api/scan/${scan.id}/approve`, {
        signature_id: null
      });
      setScan(res.data);
      toast({
        title: "Thành công",
        description: t('signature.approve_success'),
      });
    } catch (error: any) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: error.response?.data?.detail || t('signature.approve_fail'),
      });
    }
  };

  const handleReject = async () => {
    if (!scan || !rejectNote.trim()) return;
    try {
      const res = await axiosClient.post(`/api/scan/${scan.id}/reject`, {
        note: rejectNote
      });
      setScan(res.data);
      setShowRejectDialog(false);
      setRejectNote("");
      toast({
        title: "Thành công",
        description: t('signature.reject_success'),
      });
    } catch (error: any) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: error.response?.data?.detail || t('signature.reject_fail'),
      });
    }
  };



  const renderSignature = (roleName: string, fallbackName: string) => {
    if (!scan || !scan.approvals) return fallbackName;
    const approval = scan.approvals.find((a: any) => a.role === roleName && (a.action === "APPROVED" || a.action === "DRAFT"));
    if (approval && approval.signature) {
      const url = getFileUrl(approval.signature.processed_file_path);
      return (
        <div className="relative">
          <img src={url} alt="Signature" className="max-h-12 object-contain mx-auto" />
          {approval.action === "DRAFT" && (
            <span className="absolute -top-3 -right-3 text-[9px] bg-yellow-100 text-yellow-800 border border-yellow-200 px-1 py-0.5 rounded">Nháp</span>
          )}
        </div>
      );
    }
    return fallbackName;
  };

  const hasDraftSignature = (roleName: string) => {
    if (!scan || !scan.approvals) return false;
    return !!scan.approvals.find((a: any) => a.role === roleName && a.action === "DRAFT");
  };

  // ── Render ──────────────────────────────────────────

  if (loading) return <div className="p-8">{t('dashboard.table.loading')}</div>;
  if (!scan) return <div className="p-8">{t('scan.detail.not_found')}</div>;

  // Dữ liệu hiển thị: nếu đang edit thì dùng editedJson, nếu không thì dùng ocr_json gốc
  const displayJson = isEditing ? editedJson : (scan.ocr_json || {});
  const tableBbox = (scan.ocr_json || {}).table_bbox;
  const tableScore = (scan.ocr_json || {}).table_score;
  const bboxImageUrl = (scan.ocr_json || {}).bbox_image_url;

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

  // Use bbox_image_url for Paddle layout image if available, else original image
  const defaultImageUrl = getFileUrl(scan.image_path);
  const paddleBboxUrl = bboxImageUrl ? getFileUrl(bboxImageUrl) : defaultImageUrl;
  const wfStatus = scan.workflow_status || "DRAFT";

  const getBadgeColor = (status: string) => {
    const s = status.toUpperCase();
    if (s === "COMPLETED") return "bg-green-500 hover:bg-green-600 text-white border-transparent";
    if (s === "REJECTED" || s === "FAILED") return "bg-red-500 hover:bg-red-600 text-white border-transparent";
    if (s === "PROCESSING" || s === "PENDING" || s === "DRAFT" || s.startsWith("PENDING_")) return "bg-yellow-500 hover:bg-yellow-600 text-white border-transparent text-gray-900";
    return "bg-gray-500 hover:bg-gray-600 text-white border-transparent";
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] overflow-hidden">
      <div className="mb-4">
        <h1 className="text-2xl font-bold tracking-tight">{t('scan.detail.title')} {scan.original_filename}</h1>
        <div className="flex gap-2 mt-2">
          <Badge className={getBadgeColor(scan.status)}>
            OCR: {scan.status.toUpperCase()}
          </Badge>
          <Badge className={getBadgeColor(wfStatus)}>
            WF: {wfStatus}
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
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">{t('scan.detail.extract_result')}</CardTitle>
              <div className="flex items-center gap-2">
                {saveMessage && (
                  <span className={`text-xs px-2 py-1 rounded ${saveMessage.type === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                    {saveMessage.text}
                  </span>
                )}
                {scan.current_assignee_role === user?.role && wfStatus !== "DRAFT" && !isEditing && (
                  <Button variant="destructive" size="sm" onClick={() => setShowRejectDialog(true)}>
                    <Ban className="w-3.5 h-3.5 mr-1.5" /> Từ chối
                  </Button>
                )}
                {!isEditing ? (
                  <Button
                    id="btn-edit-ocr"
                    variant="outline"
                    size="sm"
                    onClick={handleStartEdit}
                    disabled={scan.status !== "completed" || wfStatus === "COMPLETED"}
                  >
                    <Pencil className="w-3.5 h-3.5 mr-1.5" />
                    {t('scan.detail.btn_edit')}
                  </Button>
                ) : (
                  <>
                    <Button
                      id="btn-cancel-edit"
                      variant="ghost"
                      size="sm"
                      onClick={handleCancelEdit}
                      disabled={isSaving}
                    >
                      <X className="w-3.5 h-3.5 mr-1.5" />
                      {t('scan.detail.btn_cancel')}
                    </Button>
                    <Button
                      id="btn-save-ocr"
                      size="sm"
                      onClick={handleSave}
                      disabled={isSaving}
                    >
                      <Save className="w-3.5 h-3.5 mr-1.5" />
                      {isSaving ? t('scan.detail.btn_saving') : t('scan.detail.btn_save')}
                    </Button>
                  </>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto p-4 space-y-4">

            {/* Header: Số phiếu + Ngày */}
            <div className="grid grid-cols-2 gap-3">
              <div
                className="bg-card border rounded p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                onMouseEnter={() => setHoveredBbox((scan.ocr_json || {}).form_no_bbox || null)}
                onMouseLeave={() => setHoveredBbox(null)}
              >
                <div className="text-sm text-muted-foreground mb-1">{t('scan.detail.form_no')}</div>
                {isEditing ? (
                  <Input
                    id="edit-form-no"
                    value={displayJson.form_no || ""}
                    onChange={(e) => handleFieldChange("form_no", e.target.value)}
                    className="h-10 text-base font-semibold"
                  />
                ) : (
                  <div className="font-semibold flex items-center">
                    {displayJson.form_no || "N/A"}
                    {(scan.ocr_json || {}).form_no_score !== undefined && <WarningIcon score={(scan.ocr_json || {}).form_no_score} />}
                  </div>
                )}
              </div>

              <div
                className="bg-card border rounded p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                onMouseEnter={() => setHoveredBbox((scan.ocr_json || {}).ngay_bbox || null)}
                onMouseLeave={() => setHoveredBbox(null)}
              >
                <div className="text-sm text-muted-foreground mb-1">{t('scan.detail.date')}</div>
                {isEditing ? (
                  <Input
                    id="edit-ngay"
                    value={displayJson.ngay || ""}
                    onChange={(e) => handleFieldChange("ngay", e.target.value)}
                    className="h-10 text-base font-semibold"
                  />
                ) : (
                  <div className="font-semibold flex items-center">
                    {displayJson.ngay || "N/A"}
                    {(scan.ocr_json || {}).ngay_score !== undefined && <WarningIcon score={(scan.ocr_json || {}).ngay_score} />}
                  </div>
                )}
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
                  onMouseEnter={(e) => { e.stopPropagation(); setHoveredBbox((scan.ocr_json || {}).info_bbox || tableBbox || null); }}
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
                      <td className="border px-3 py-3 font-medium">
                        {isEditing ? (
                          <Input id="edit-don-vi" value={displayJson.info?.don_vi || ""} onChange={(e) => handleInfoChange("don_vi", e.target.value)} className="h-10 text-base" />
                        ) : (displayJson.info?.don_vi || "")}
                      </td>
                      <td className="border px-3 py-3 font-medium">
                        {isEditing ? (
                          <Input id="edit-ho-ten" value={displayJson.info?.ho_ten || ""} onChange={(e) => handleInfoChange("ho_ten", e.target.value)} className="h-10 text-base" />
                        ) : (displayJson.info?.ho_ten || "")}
                      </td>
                      <td className="border px-3 py-3 font-medium">
                        {isEditing ? (
                          <Input id="edit-so-the" value={displayJson.info?.so_the || ""} onChange={(e) => handleInfoChange("so_the", e.target.value)} className="h-10 text-base" />
                        ) : (displayJson.info?.so_the || "")}
                      </td>
                      <td className="border px-3 py-3 font-medium">
                        {isEditing ? (
                          <Input id="edit-chu-quan" value={displayJson.info?.chu_quan || ""} onChange={(e) => handleInfoChange("chu_quan", e.target.value)} className="h-10 text-base" />
                        ) : (displayJson.info?.chu_quan || "")}
                      </td>
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
                    {(displayJson.line_items || []).length === 0 ? (
                      <tr>
                        <td colSpan={6} className="border px-3 py-4 text-center text-muted-foreground italic text-xs">
                          {t('scan.detail.no_table')}
                        </td>
                      </tr>
                    ) : (
                      (displayJson.line_items || []).map((item: Record<string, string>, idx: number) => (
                        <tr key={idx} className="hover:bg-muted/20">
                          <td className="border px-3 py-3 text-center">{idx + 1}</td>
                          <td className="border px-3 py-3 text-center">
                            {isEditing ? (
                              <Input value={item.hang_muc || ""} onChange={(e) => handleUpdateRow(idx, "hang_muc", e.target.value)} className="h-10 text-base text-center" />
                            ) : (item.hang_muc || "")}
                          </td>
                          <td className="border px-3 py-3 text-center">
                            {isEditing ? (
                              <textarea
                                value={item.muc_dich || ""}
                                onChange={(e) => handleUpdateRow(idx, "muc_dich", e.target.value)}
                                className="w-full min-h-[3rem] rounded-md border border-input bg-background px-3 py-2 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring text-center resize-y"
                                rows={3}
                              />
                            ) : (item.muc_dich || "")}
                          </td>
                          <td className="border px-3 py-3 text-center">
                            {isEditing ? (
                              <Input value={item.so_luong_don_gia || ""} onChange={(e) => handleUpdateRow(idx, "so_luong_don_gia", e.target.value)} className="h-10 text-base text-center" />
                            ) : (item.so_luong_don_gia || "")}
                          </td>
                          <td className="border px-3 py-3 text-center font-medium">
                            {isEditing ? (
                              <Input value={item.so_tien || ""} onChange={(e) => handleUpdateRow(idx, "so_tien", e.target.value)} className="h-10 text-base text-center font-medium" />
                            ) : (item.so_tien || "")}
                          </td>
                          <td className="border px-3 py-3 text-center">
                            {isEditing ? (
                              <Input value={item.so_chung_tu || ""} onChange={(e) => handleUpdateRow(idx, "so_chung_tu", e.target.value)} className="h-10 text-base text-center" />
                            ) : (item.so_chung_tu || "")}
                          </td>
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
                        {isEditing ? (
                          <Input
                            id="edit-so-tien-tam-ung"
                            value={displayJson.footer?.so_tien_tam_ung || ""}
                            onChange={(e) => handleFooterChange("so_tien_tam_ung", e.target.value)}
                            className="h-10 text-base mt-1 text-center font-semibold"
                          />
                        ) : (
                          <div className="font-semibold mt-1 text-center">{displayJson.footer?.so_tien_tam_ung || ""}</div>
                        )}
                      </td>
                      <td className="border px-3 py-3 w-1/4">
                        <div className="text-sm font-bold text-center">簽收</div>
                        <div className="text-sm text-muted-foreground text-center">Ký nhận</div>
                        <div className="mt-2 min-h-[3rem] flex items-center justify-center text-center">{renderSignature("EMPLOYEE", displayJson.footer?.ky_nhan || "")}</div>
                        {hasDraftSignature("EMPLOYEE") ? (
                          <div className="flex gap-1 mt-2">
                            <Button variant="outline" size="sm" className="w-1/2 text-xs px-1 text-red-600" onClick={handleRemoveDraftSignature} disabled={wfStatus !== "DRAFT" || user?.role !== "EMPLOYEE"}>
                              <Trash2 className="w-3 h-3 mr-1" /> Xóa
                            </Button>
                            <Button size="sm" className="w-1/2 text-xs px-1" onClick={handleApprove} disabled={wfStatus !== "DRAFT" || user?.role !== "EMPLOYEE"}>
                              <CheckCircle2 className="w-3 h-3 mr-1" /> Trình
                            </Button>
                          </div>
                        ) : (
                          <Button variant="outline" size="sm" className="w-full mt-2 text-xs" onClick={() => handleStartSigning("EMPLOYEE")} disabled={wfStatus !== "DRAFT" || user?.role !== "EMPLOYEE"}>
                            <Stamp className="w-3.5 h-3.5 mr-1" /> Ký (Trình)
                          </Button>
                        )}
                      </td>
                      <td className="border px-3 py-3 w-1/4">
                        <div className="text-sm font-bold text-center">實支</div>
                        <div className="text-sm text-muted-foreground text-center">Thực chi</div>
                        {isEditing ? (
                          <Input
                            id="edit-thuc-chi"
                            value={displayJson.footer?.thuc_chi || ""}
                            onChange={(e) => handleFooterChange("thuc_chi", e.target.value)}
                            className="h-10 text-base mt-1 text-center"
                          />
                        ) : (
                          <div className="mt-1 text-center">{displayJson.footer?.thuc_chi || ""}</div>
                        )}
                      </td>
                      <td className="border px-3 py-3 w-1/4">
                        <div className="text-xs text-center">[ ] 補 Bố sung</div>
                        <div className="text-xs text-center">[ ] 退 Trả lại</div>
                      </td>
                    </tr>
                    <tr className="bg-muted/10">
                      <td className="border px-3 py-4">
                        <div className="text-sm font-bold text-center">總經理</div>
                        <div className="text-sm text-muted-foreground text-center">Tổng Giám Đốc</div>
                        <div className="mt-2 min-h-[3rem] flex items-center justify-center text-center">{renderSignature("CEO", displayJson.footer?.tong_giam_doc || "")}</div>
                        {hasDraftSignature("CEO") ? (
                          <div className="flex gap-1 mt-2">
                            <Button variant="outline" size="sm" className="w-1/2 text-xs px-1 text-red-600" onClick={handleRemoveDraftSignature} disabled={wfStatus !== "PENDING_CEO" || user?.role !== "CEO"}>
                              <Trash2 className="w-3 h-3 mr-1" /> Xóa
                            </Button>
                            <Button size="sm" className="w-1/2 text-xs px-1" onClick={handleApprove} disabled={wfStatus !== "PENDING_CEO" || user?.role !== "CEO"}>
                              <CheckCircle2 className="w-3 h-3 mr-1" /> Khóa
                            </Button>
                          </div>
                        ) : (
                          <Button variant="outline" size="sm" className="w-full mt-2 text-xs" onClick={() => handleStartSigning("CEO")} disabled={wfStatus !== "PENDING_CEO" || user?.role !== "CEO"}>
                            <Stamp className="w-3.5 h-3.5 mr-1" /> Ký duyệt
                          </Button>
                        )}
                      </td>
                      <td className="border px-3 py-4">
                        <div className="text-sm font-bold text-center">出納</div>
                        <div className="text-sm text-muted-foreground text-center">Thủ quỹ</div>
                        <div className="mt-2 min-h-[3rem] flex items-center justify-center text-center">{renderSignature("TREASURY", displayJson.footer?.thu_quy_1 || "")}</div>
                        {hasDraftSignature("TREASURY") ? (
                          <div className="flex gap-1 mt-2">
                            <Button variant="outline" size="sm" className="w-1/2 text-xs px-1 text-red-600" onClick={handleRemoveDraftSignature} disabled={wfStatus !== "PENDING_TREASURY" || user?.role !== "TREASURY"}>
                              <Trash2 className="w-3 h-3 mr-1" /> Xóa
                            </Button>
                            <Button size="sm" className="w-1/2 text-xs px-1" onClick={handleApprove} disabled={wfStatus !== "PENDING_TREASURY" || user?.role !== "TREASURY"}>
                              <CheckCircle2 className="w-3 h-3 mr-1" /> Khóa
                            </Button>
                          </div>
                        ) : (
                          <Button variant="outline" size="sm" className="w-full mt-2 text-xs" onClick={() => handleStartSigning("TREASURY")} disabled={wfStatus !== "PENDING_TREASURY" || user?.role !== "TREASURY"}>
                            <Stamp className="w-3.5 h-3.5 mr-1" /> Ký duyệt
                          </Button>
                        )}
                      </td>
                      <td className="border px-3 py-4">
                        <div className="text-sm font-bold text-center">會計</div>
                        <div className="text-sm text-muted-foreground text-center">Kế toán</div>
                        <div className="mt-2 min-h-[3rem] flex items-center justify-center text-center">{renderSignature("ACCOUNTING", displayJson.footer?.ke_toan || "")}</div>
                        {hasDraftSignature("ACCOUNTING") ? (
                          <div className="flex gap-1 mt-2">
                            <Button variant="outline" size="sm" className="w-1/2 text-xs px-1 text-red-600" onClick={handleRemoveDraftSignature} disabled={wfStatus !== "PENDING_ACCOUNTING" || user?.role !== "ACCOUNTING"}>
                              <Trash2 className="w-3 h-3 mr-1" /> Xóa
                            </Button>
                            <Button size="sm" className="w-1/2 text-xs px-1" onClick={handleApprove} disabled={wfStatus !== "PENDING_ACCOUNTING" || user?.role !== "ACCOUNTING"}>
                              <CheckCircle2 className="w-3 h-3 mr-1" /> Khóa
                            </Button>
                          </div>
                        ) : (
                          <Button variant="outline" size="sm" className="w-full mt-2 text-xs" onClick={() => handleStartSigning("ACCOUNTING")} disabled={wfStatus !== "PENDING_ACCOUNTING" || user?.role !== "ACCOUNTING"}>
                            <Stamp className="w-3.5 h-3.5 mr-1" /> Ký duyệt
                          </Button>
                        )}
                      </td>
                      <td className="border px-3 py-4">
                        <div className="text-sm font-bold text-center">出納</div>
                        <div className="text-sm text-muted-foreground text-center">Thủ quỹ (Phụ)</div>
                        <div className="mt-2 min-h-[3rem] flex items-center justify-center text-center">{renderSignature("SUB_TREASURY", displayJson.footer?.thu_quy_2 || "")}</div>
                        {hasDraftSignature("SUB_TREASURY") ? (
                          <div className="flex gap-1 mt-2">
                            <Button variant="outline" size="sm" className="w-1/2 text-xs px-1 text-red-600" onClick={handleRemoveDraftSignature} disabled={wfStatus !== "PENDING_SUB_TREASURY" || user?.role !== "SUB_TREASURY"}>
                              <Trash2 className="w-3 h-3 mr-1" /> Xóa
                            </Button>
                            <Button size="sm" className="w-1/2 text-xs px-1" onClick={handleApprove} disabled={wfStatus !== "PENDING_SUB_TREASURY" || user?.role !== "SUB_TREASURY"}>
                              <CheckCircle2 className="w-3 h-3 mr-1" /> Khóa
                            </Button>
                          </div>
                        ) : (
                          <Button variant="outline" size="sm" className="w-full mt-2 text-xs" onClick={() => handleStartSigning("SUB_TREASURY")} disabled={wfStatus !== "PENDING_SUB_TREASURY" || user?.role !== "SUB_TREASURY"}>
                            <Stamp className="w-3.5 h-3.5 mr-1" /> (Phụ)
                          </Button>
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </CardContent>
        </Card>
      </div>

      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('signature.reject_prompt')}</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <textarea
              className="w-full min-h-[100px] p-3 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="..."
              value={rejectNote}
              onChange={(e) => setRejectNote(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)}>{t('scan.detail.btn_cancel')}</Button>
            <Button variant="destructive" onClick={handleReject} disabled={!rejectNote.trim()}>Xác nhận từ chối</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showSignatureSelector} onOpenChange={setShowSignatureSelector}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Chọn chữ ký / Select Signature</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            {mySignatures.map(sig => {
              const url = getFileUrl(sig.image_url);
              return (
                <div
                  key={sig.id}
                  className="border rounded-xl p-4 flex flex-col items-center gap-2 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => handleSelectSignature(sig.id)}
                >
                  <img src={url} alt="Signature" className="max-h-16 object-contain" />
                  <span className="text-xs text-muted-foreground mt-2 text-center">{sig.signer_name}</span>
                </div>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
