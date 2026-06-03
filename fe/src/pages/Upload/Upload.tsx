import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload as UploadIcon, FileImage, X } from "lucide-react";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";

export default function Upload() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const addFiles = (newFiles: File[]) => {
    setError("");
    const combined = [...files, ...newFiles];
    if (combined.length > 5) {
      setError(t('upload.alert.max_files'));
      return;
    }
    setFiles(combined);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
    setError("");
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    if (files.length === 2) {
      setError(t('upload.alert.min_batch'));
      return;
    }

    setLoading(true);
    setError("");

    const formData = new FormData();

    try {
      if (files.length === 1) {
        // Đơn luồng
        formData.append("file", files[0]);
        const res = await axiosClient.post("/api/scan/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        navigate(`/scan/${res.data.id}`);
      } else {
        // Đa luồng (Batch)
        files.forEach((file) => {
          formData.append("files", file); // Backend expects 'files'
        });
        await axiosClient.post("/api/scan/batch", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        // Redirect to scans list where they can see the processing status
        navigate("/scans");
      }
    } catch (err: unknown) {
      console.error(err);
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || t('upload.alert.fail'));
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('upload.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('upload.desc')}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('upload.card.title')}</CardTitle>
          <CardDescription>
            {t('upload.card.desc')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 bg-destructive/15 text-destructive p-3 rounded-md text-sm font-medium">
              {error}
            </div>
          )}

          {files.length === 0 ? (
            <div
              className="border-2 border-dashed rounded-lg p-12 text-center hover:bg-muted/50 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <div className="flex flex-col items-center justify-center space-y-4">
                <div className="p-4 bg-primary/10 rounded-full">
                  <UploadIcon className="w-8 h-8 text-primary" />
                </div>
                <div>
                  <p className="text-lg font-medium">{t('upload.drag')}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {t('upload.drag_sub')}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid gap-3">
                {files.map((f, idx) => (
                  <div key={idx} className="border rounded-lg p-3 bg-muted/20 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <FileImage className="w-8 h-8 text-primary" />
                      <div>
                        <p className="font-medium text-sm truncate max-w-[200px] sm:max-w-xs">{f.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {(f.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeFile(idx)}
                      disabled={loading}
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>

              {files.length < 5 && (
                <Button
                  variant="outline"
                  className="w-full border-dashed"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                >
                  {t('upload.btn.add')}
                </Button>
              )}
            </div>
          )}

          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/jpeg, image/png, image/jpg"
            onChange={handleFileChange}
            multiple
          />
        </CardContent>
        <CardFooter className="flex justify-end border-t p-6">
          <Button
            onClick={handleUpload}
            disabled={files.length === 0 || loading}
            className="w-full sm:w-auto"
          >
            {loading ? t('upload.btn.submit.loading') : files.length === 1 ? t('upload.btn.submit.single') : t('upload.btn.submit.batch')}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
