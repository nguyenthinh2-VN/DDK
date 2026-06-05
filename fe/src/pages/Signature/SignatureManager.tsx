import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { ImagePlus, Loader2, Sparkles, Trash2 } from "lucide-react";

import axiosClient from "../../api/axiosClient";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "../../contexts/AuthContext";
import { useTranslation } from "../../hooks/useTranslation";

interface SignatureResponse {
  id: string;
  user_id: string;
  signer_name: string;
  original_filename: string;
  image_url: string;
  bg_removed: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  remove_background_applied?: boolean;
}

const getFileUrl = (filePath?: string) => {
  if (!filePath) return "";
  if (filePath.startsWith("http")) return filePath;
  const base = axiosClient.defaults.baseURL || window.location.origin;
  return new URL(filePath, base).toString();
};

export default function SignatureManager() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [signatures, setSignatures] = useState<SignatureResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [signerName, setSignerName] = useState("");
  const [removeBackground, setRemoveBackground] = useState(true);

  const activePreview = useMemo(() => {
    if (previewUrl) return previewUrl;
    return "";
  }, [previewUrl]);

  useEffect(() => {
    setSignerName(user?.full_name || "");
  }, [user?.full_name]);

  useEffect(() => {
    fetchSignature();
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const fetchSignature = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axiosClient.get("/api/signatures/me");
      setSignatures(res.data);
    } catch (err: any) {
      if (err?.response?.status !== 404) {
        setError(err?.response?.data?.detail || "Không thể tải chữ ký hiện tại.");
      }
      setSignatures([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setError("");
    setSuccess("");
    if (!file) {
      setSelectedFile(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl("");
      return;
    }

    setSelectedFile(file);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError("Vui lòng chọn file chữ ký.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("signer_name", signerName.trim() || user?.full_name || "");
    formData.append("remove_background", String(removeBackground));

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const res = await axiosClient.post("/api/signatures/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSignatures(prev => [res.data, ...prev]);
      setSuccess(
        removeBackground
          ? "Đã upload và xóa nền chữ ký thành công."
          : "Đã upload chữ ký nền trong suốt thành công."
      );
      setSelectedFile(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Upload chữ ký thất bại.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    setError("");
    setSuccess("");
    try {
      await axiosClient.delete(`/api/signatures/${id}`);
      setSignatures(prev => prev.filter(s => s.id !== id));
      setSuccess("Đã gỡ chữ ký.");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Không thể gỡ chữ ký.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('signature.title')}</h1>
        <p className="mt-2 text-muted-foreground">
          {t('signature.desc')}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t('signature.upload.title')}</CardTitle>
            <CardDescription>
              {t('signature.upload.desc')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {error && <div className="rounded-md bg-destructive/15 px-4 py-3 text-sm text-destructive">{error}</div>}
            {success && <div className="rounded-md bg-green-100 px-4 py-3 text-sm text-green-700">{success}</div>}

            <div className="space-y-2">
              <Label htmlFor="signature-name">{t('signature.signer_name')}</Label>
              <Input
                id="signature-name"
                value={signerName}
                onChange={(e) => setSignerName(e.target.value)}
                placeholder="Nguyễn Văn A"
              />
            </div>

            <div className="space-y-3">
              <Label>{t('signature.mode.title')}</Label>
              <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 hover:bg-muted/40">
                <input
                  type="radio"
                  className="mt-1"
                  checked={removeBackground}
                  onChange={() => setRemoveBackground(true)}
                />
                <div>
                  <div className="font-medium">{t('signature.mode.auto')}</div>
                  <div className="text-sm text-muted-foreground">
                    {t('signature.mode.auto_desc')}
                  </div>
                </div>
              </label>
              <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 hover:bg-muted/40">
                <input
                  type="radio"
                  className="mt-1"
                  checked={!removeBackground}
                  onChange={() => setRemoveBackground(false)}
                />
                <div>
                  <div className="font-medium">{t('signature.mode.manual')}</div>
                  <div className="text-sm text-muted-foreground">
                    {t('signature.mode.manual_desc')}
                  </div>
                </div>
              </label>
            </div>

            <div className="space-y-2">
              <Label htmlFor="signature-file">{t('signature.file')}</Label>
              <Input
                id="signature-file"
                type="file"
                accept="image/png,image/jpeg,image/jpg"
                onChange={handleFileChange}
              />
              <p className="text-xs text-muted-foreground">
                {t('signature.file_hint')}
              </p>
            </div>

            <div className="rounded-2xl border border-dashed bg-zinc-50/80 p-6">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium">
                <Sparkles className="h-4 w-4" />
                {t('signature.preview')}
              </div>
              <div className="flex min-h-[240px] items-center justify-center rounded-xl bg-[radial-gradient(circle_at_top,#ffffff,#f4f4f5)] p-4">
                {activePreview ? (
                  <img
                    src={activePreview}
                    alt="Signature preview"
                    className="max-h-[220px] max-w-full object-contain"
                  />
                ) : (
                  <div className="flex flex-col items-center gap-3 text-center text-sm text-muted-foreground">
                    <ImagePlus className="h-8 w-8" />
                    <p>{t('signature.preview_empty')}</p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-3 border-t pt-6">
            <Button variant="outline" onClick={fetchSignature} disabled={submitting || loading}>
              {t('signature.btn.refresh')}
            </Button>
            <Button onClick={handleSubmit} disabled={!selectedFile || submitting || signatures.length >= 3}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('signature.btn.uploading')}
                </>
              ) : (
                t('signature.btn.upload')
              )}
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('signature.current.title')}</CardTitle>
            <CardDescription>{t('signature.current.desc')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="text-sm text-muted-foreground">{t('signature.current.loading')}</div>
            ) : signatures.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
                {t('signature.current.empty')}
              </div>
            ) : (
              <div className="grid gap-4">
                {signatures.map(sig => (
                  <div key={sig.id} className="border rounded-xl p-4 flex flex-col gap-3">
                    <div className="rounded-xl border bg-zinc-50 p-2">
                      <div className="flex h-[120px] items-center justify-center rounded-lg bg-white p-2 shadow-sm">
                        <img
                          src={getFileUrl(sig.image_url)}
                          alt={sig.signer_name}
                          className="max-h-full max-w-full object-contain"
                        />
                      </div>
                    </div>
                    <div className="space-y-1 text-xs">
                      <div><span className="font-medium">{t('signature.current.signer')}</span> {sig.signer_name}</div>
                      <div><span className="font-medium">{t('signature.current.updated_at')}</span> {new Date(sig.updated_at).toLocaleString("vi-VN")}</div>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="w-full mt-2"
                      onClick={() => {
                        if (window.confirm(t('signature.confirm.delete'))) {
                          handleDelete(sig.id);
                        }
                      }}
                      disabled={deletingId === sig.id}
                    >
                      {deletingId === sig.id ? (
                        <>
                          <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                          {t('signature.btn.deleting')}
                        </>
                      ) : (
                        <>
                          <Trash2 className="mr-2 h-3 w-3" />
                          {t('signature.btn.delete')}
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
