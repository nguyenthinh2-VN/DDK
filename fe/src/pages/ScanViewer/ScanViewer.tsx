import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { AlertCircle, Pencil, Save, X, Ban, Plus, Trash2, Download } from "lucide-react";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import RawTableViewer from "./RawTableViewer";
import SigningPanel from "./SigningPanel";
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
    setEditedJson(JSON.parse(JSON.stringify(scan.ocr_json || {})));
    setIsEditing(true);
    setSaveMessage(null);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedJson(null);
    setSaveMessage(null);
  };

  const handleFieldChange = (field: string, value: string | any) => {
    setEditedJson((prev: Record<string, unknown>) => ({ ...prev, [field]: value }));
  };

  const handleAddLineItem = () => {
    const newItems = [...(editedJson?.line_items || [])];
    newItems.push({
      hang_muc: "",
      muc_dich: "",
      so_luong_don_gia: "",
      so_tien: "",
      so_chung_tu: ""
    });
    handleFieldChange("line_items", newItems);
  };

  const handleRemoveLineItem = (idx: number) => {
    const newItems = [...(editedJson?.line_items || [])];
    newItems.splice(idx, 1);
    handleFieldChange("line_items", newItems);
  };

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
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error("Failed to save OCR JSON", error);
      setSaveMessage({ type: "error", text: t("scan.detail.save_fail") });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!scan) return;
    try {
      const response = await axiosClient.get(`/api/scan/${scan.id}/export-pdf`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `PhieuTamUng_${scan.form_no || scan.id.substring(0, 6)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (error) {
      console.error("Failed to download PDF", error);
      toast({
        title: "Lỗi tải xuống",
        description: "Không thể xuất PDF. Vui lòng thử lại.",
        variant: "destructive",
      });
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

  // ── Render ──────────────────────────────────────────

  if (loading) return <div className="p-8">{t('dashboard.table.loading')}</div>;
  if (!scan) return <div className="p-8">{t('scan.detail.not_found')}</div>;

  const displayJson = isEditing ? editedJson : (scan.ocr_json || {});
  const bboxImageUrl = (scan.ocr_json || {}).bbox_image_url;

  const scaleX = imgRenderSize.w / imgNaturalSize.w;
  const scaleY = imgRenderSize.h / imgNaturalSize.h;

  const renderBbox = (box: number[] | null) => {
    if (!box) return null;
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

  // suppress unused warning - activeSignRole used by handleStartSigning
  void activeSignRole;

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
                {wfStatus === "COMPLETED" && (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleDownloadPdf}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    <Download className="w-3.5 h-3.5 mr-1.5" /> Tải PDF
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
          <CardContent className="flex-1 overflow-auto p-4 space-y-3">

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

            {/* Bảng OCR thô từ PaddleOCR - dùng trực tiếp html_content */}
            <div className="border rounded-md overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 bg-muted/40 border-b">
                <h3 className="text-sm font-semibold">{t('scan.detail.table')}</h3>
              </div>
              {isEditing ? (
                <div className="p-4 space-y-4 bg-muted/10">
                  <h4 className="font-medium text-sm">Hạng mục (Line Items)</h4>
                  {editedJson.line_items?.map((item: any, idx: number) => (
                    <div key={idx} className="p-3 border rounded bg-background shadow-sm">
                      <div className="font-semibold text-sm mb-3 text-primary border-b pb-2 flex items-center justify-between">
                        <span>Hạng mục {idx + 1}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleRemoveLineItem(idx)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs text-muted-foreground font-medium">Hạng mục</label>
                          <textarea
                            className="w-full text-sm border rounded p-1 min-h-[40px]"
                            value={item.hang_muc || ""}
                            onChange={(e) => {
                              const newItems = [...editedJson.line_items];
                              newItems[idx].hang_muc = e.target.value;
                              handleFieldChange("line_items", newItems);
                            }}
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">Mục đích</label>
                          <textarea
                            className="w-full text-sm border rounded p-1 min-h-[40px]"
                            value={item.muc_dich || ""}
                            onChange={(e) => {
                              const newItems = [...editedJson.line_items];
                              newItems[idx].muc_dich = e.target.value;
                              handleFieldChange("line_items", newItems);
                            }}
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">Số lượng / Đơn giá</label>
                          <textarea
                            className="w-full text-sm border rounded p-1 min-h-[40px]"
                            value={item.so_luong_don_gia || ""}
                            onChange={(e) => {
                              const newItems = [...editedJson.line_items];
                              newItems[idx].so_luong_don_gia = e.target.value;
                              handleFieldChange("line_items", newItems);
                            }}
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">Số tiền</label>
                          <textarea
                            className="w-full text-sm border rounded p-1 min-h-[40px]"
                            value={item.so_tien || ""}
                            onChange={(e) => {
                              const newItems = [...editedJson.line_items];
                              newItems[idx].so_tien = e.target.value;
                              handleFieldChange("line_items", newItems);
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  <div className="flex justify-center mt-2">
                    <Button variant="outline" size="sm" onClick={handleAddLineItem} className="w-full border-dashed">
                      <Plus className="w-4 h-4 mr-2" /> Thêm hạng mục
                    </Button>
                  </div>

                  <h4 className="font-medium text-sm mt-4">Tổng kết (Footer)</h4>
                  <div className="grid grid-cols-2 gap-2 p-3 border rounded bg-background">
                    <div>
                      <label className="text-xs text-muted-foreground">Số tiền tạm ứng</label>
                      <Input
                        className="h-8 text-sm"
                        value={editedJson.footer?.so_tien_tam_ung || ""}
                        onChange={(e) => {
                          const newFooter = { ...(editedJson.footer || {}), so_tien_tam_ung: e.target.value };
                          handleFieldChange("footer", newFooter);
                        }}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Thực chi</label>
                      <Input
                        className="h-8 text-sm"
                        value={editedJson.footer?.thuc_chi || ""}
                        onChange={(e) => {
                          const newFooter = { ...(editedJson.footer || {}), thuc_chi: e.target.value };
                          handleFieldChange("footer", newFooter);
                        }}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <RawTableViewer htmlContent={scan.html_content} />
              )}
            </div>

            {/* Panel ký duyệt tách biệt */}
            <SigningPanel
              wfStatus={wfStatus}
              userRole={user?.role}
              approvals={scan.approvals || []}
              onSign={handleStartSigning}
              onApprove={handleApprove}
              onRemoveDraft={handleRemoveDraftSignature}
              getFileUrl={getFileUrl}
            />

          </CardContent>
        </Card>
      </div>

      {/* Dialog từ chối */}
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

      {/* Dialog chọn chữ ký */}
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
