import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuth } from "../../contexts/AuthContext";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";

interface DashboardStats {
  total_uploaded_files: number;
  total_scanned_slips: number;
  total_failed_slips: number;
}

interface ScanSummary {
  id: string;
  original_filename: string;
  document_type: string;
  status: string;
  created_at: string;
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, scansRes] = await Promise.all([
          axiosClient.get("/api/stats/dashboard"),
          axiosClient.get("/api/scan/"),
        ]);
        setStats(statsRes.data);
        setScans(scansRes.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

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

  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('dashboard.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('dashboard.welcome', { name: user?.full_name || "" })}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {t('dashboard.total_files')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "..." : stats?.total_uploaded_files || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-600">
              {t('dashboard.total_success')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "..." : stats?.total_scanned_slips || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-600">
              {t('dashboard.total_error')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "..." : stats?.total_failed_slips || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-bold tracking-tight mb-4">{t('dashboard.recent_scans')}</h2>
        <div className="rounded-md border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('dashboard.table.filename')}</TableHead>
                <TableHead>{t('dashboard.table.type')}</TableHead>
                <TableHead>{t('dashboard.table.status')}</TableHead>
                <TableHead>{t('dashboard.table.time')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                    {t('dashboard.table.loading')}
                  </TableCell>
                </TableRow>
              ) : scans.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
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
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
