import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileScan, Trash2 } from "lucide-react";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";

interface ScanSummary {
  id: string;
  original_filename: string;
  document_type: string;
  status: string;
  created_at: string;
}

export default function Scans() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      const res = await axiosClient.get("/api/scan/");
      setScans(res.data);
    } catch (error) {
      console.error("Failed to fetch scans", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm(t('scans.confirm.delete'))) {
      try {
        await axiosClient.delete(`/api/scan/${id}`);
        fetchScans();
      } catch (error) {
        alert(t('scans.alert.delete_fail'));
      }
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("vi-VN");
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "text-green-600 font-medium";
      case "failed": return "text-red-600 font-medium";
      case "processing": return "text-blue-600 font-medium";
      default: return "text-gray-600 font-medium";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('scans.title')}</h1>
          <p className="text-muted-foreground mt-2">
            {t('scans.desc')}
          </p>
        </div>
        <Button onClick={() => navigate("/upload")} className="flex items-center gap-2">
          <FileScan className="w-4 h-4" /> {t('scans.btn.upload')}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('scans.card.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('dashboard.table.filename')}</TableHead>
                  <TableHead>{t('dashboard.table.type')}</TableHead>
                  <TableHead>{t('dashboard.table.status')}</TableHead>
                  <TableHead>{t('dashboard.table.time')}</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      {t('dashboard.table.loading')}
                    </TableCell>
                  </TableRow>
                ) : scans.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      {t('dashboard.table.empty')}
                    </TableCell>
                  </TableRow>
                ) : (
                  scans.map((scan) => (
                    <TableRow
                      key={scan.id}
                      className="cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => navigate(`/scan/${scan.id}`)}
                    >
                      <TableCell className="font-medium">{scan.original_filename}</TableCell>
                      <TableCell>{scan.document_type}</TableCell>
                      <TableCell className={getStatusColor(scan.status)}>
                        {scan.status.toUpperCase()}
                      </TableCell>
                      <TableCell>{formatDate(scan.created_at)}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={(e) => handleDelete(e, scan.id)}
                          title="Xoá"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
