import React, { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight, History, Loader2, Check, Clock, X } from "lucide-react";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";
import { useToast } from "@/hooks/use-toast";

interface ScanSummary {
  id: string;
  original_filename: string;
  document_type: string;
  status: string;
  workflow_status: string;
  current_assignee_role: string | null;
  created_at: string;
}

interface SignatureBasic {
  id: string;
  signer_name: string;
}

interface ScanApproval {
  id: string;
  role: string;
  action: string;
  note: string | null;
  signature: SignatureBasic | null;
  created_at: string;
}

const WORKFLOW_STEPS = [
  { id: 'EMPLOYEE', label: 'Bước 1: Nhân viên (Maker)' },
  { id: 'ACCOUNTING', label: 'Bước 2: Kế toán' },
  { id: 'TREASURY', label: 'Bước 3: Thủ quỹ 1' },
  { id: 'CEO', label: 'Bước 4: Giám đốc' },
  { id: 'SUB_TREASURY', label: 'Bước 5: Thủ quỹ phụ' }
];

const getRoleStatus = (roleId: string, approvals: ScanApproval[] = [], currentAssignee: string | null, workflowStatus: string) => {
  const roleApprovals = approvals.filter(a => a.role === roleId).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  const latest = roleApprovals[0];

  if (workflowStatus === 'COMPLETED') {
    return { status: 'completed', data: latest };
  }

  if (currentAssignee === roleId) {
    return { status: 'current', data: latest };
  }

  if (latest) {
    if (latest.action === 'APPROVED') return { status: 'completed', data: latest };
    if (latest.action === 'REJECTED') return { status: 'rejected', data: latest };
  }

  const currentIndex = WORKFLOW_STEPS.findIndex(s => s.id === currentAssignee);
  const thisIndex = WORKFLOW_STEPS.findIndex(s => s.id === roleId);

  if (currentIndex > -1 && thisIndex < currentIndex) {
    return { status: 'completed', data: latest };
  }

  return { status: 'pending', data: null };
};

export default function AuditLog() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [approvalsData, setApprovalsData] = useState<Record<string, ScanApproval[]>>({});
  const [loadingApprovals, setLoadingApprovals] = useState<Record<string, boolean>>({});
  const { t } = useTranslation();
  const { toast } = useToast();

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      const res = await axiosClient.get("/api/scan/");
      setScans(res.data);
    } catch (error) {
      console.error("Failed to fetch scans", error);
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: "Không thể tải danh sách phiếu.",
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = async (scanId: string) => {
    if (expandedRow === scanId) {
      setExpandedRow(null);
      return;
    }

    setExpandedRow(scanId);

    if (!approvalsData[scanId]) {
      setLoadingApprovals(prev => ({ ...prev, [scanId]: true }));
      try {
        const res = await axiosClient.get(`/api/scan/${scanId}`);
        setApprovalsData(prev => ({ ...prev, [scanId]: res.data.approvals || [] }));
      } catch (error) {
        console.error("Failed to fetch scan details", error);
      } finally {
        setLoadingApprovals(prev => ({ ...prev, [scanId]: false }));
      }
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("vi-VN");
  };

  const getBadgeColor = (status: string) => {
    if (!status) return "bg-gray-500 text-white";
    const s = status.toUpperCase();
    if (s === "COMPLETED") return "bg-green-500 hover:bg-green-600 text-white border-transparent";
    if (s === "APPROVED") return "bg-blue-500 hover:bg-blue-600 text-white border-transparent";
    if (s === "REJECTED" || s === "FAILED") return "bg-red-500 hover:bg-red-600 text-white border-transparent";
    if (s === "PROCESSING" || s === "PENDING" || s === "DRAFT" || s.startsWith("PENDING_")) return "bg-yellow-500 hover:bg-yellow-600 text-white border-transparent text-gray-900";
    return "bg-gray-500 hover:bg-gray-600 text-white border-transparent";
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-lg border shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/10 rounded-full text-primary">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900">{t('audit.title')}</h1>
            <p className="text-zinc-500">{t('audit.desc')}</p>
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="rounded-md border-0">
            <Table>
              <TableHeader className="bg-zinc-50">
                <TableRow>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>{t('audit.table.filename')}</TableHead>
                  <TableHead>{t('audit.table.type')}</TableHead>
                  <TableHead>{t('audit.table.wf_status')}</TableHead>
                  <TableHead>{t('audit.table.assignee')}</TableHead>
                  <TableHead>{t('audit.table.time')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      Đang tải...
                    </TableCell>
                  </TableRow>
                ) : scans.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      {t('audit.table.empty')}
                    </TableCell>
                  </TableRow>
                ) : (
                  scans.map((scan) => (
                    <React.Fragment key={scan.id}>
                      <TableRow
                        className="cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => toggleRow(scan.id)}
                      >
                        <TableCell>
                          {expandedRow === scan.id ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
                        </TableCell>
                        <TableCell className="font-medium">{scan.original_filename}</TableCell>
                        <TableCell>{scan.document_type}</TableCell>
                        <TableCell>
                          <Badge className={getBadgeColor(scan.workflow_status || "DRAFT")}>
                            {(scan.workflow_status || "DRAFT").toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {scan.current_assignee_role ? (
                            <Badge variant="outline" className="font-normal">{scan.current_assignee_role}</Badge>
                          ) : <span className="text-muted-foreground text-sm">-</span>}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">{formatDate(scan.created_at)}</TableCell>
                      </TableRow>

                      {expandedRow === scan.id && (
                        <TableRow className="bg-muted/10">
                          <TableCell colSpan={6} className="p-0 border-b">
                            <div className="px-14 py-6">
                              <h4 className="text-sm font-semibold mb-4 text-zinc-700">{t('audit.title')}</h4>

                              {loadingApprovals[scan.id] ? (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                  <Loader2 className="w-4 h-4 animate-spin" /> Đang tải lịch sử...
                                </div>
                              ) : (
                                <div className="flex flex-row items-start w-full mt-2 bg-white p-4 rounded-lg border shadow-sm">
                                  {WORKFLOW_STEPS.map((step, index) => {
                                    const { status, data } = getRoleStatus(step.id, approvalsData[scan.id] || [], scan.current_assignee_role, scan.workflow_status || 'DRAFT');
                                    const isLast = index === WORKFLOW_STEPS.length - 1;

                                    return (
                                      <div key={step.id} className="relative flex flex-col items-center flex-1 text-center px-1">
                                        {!isLast && (
                                          <div className={`absolute top-4 left-[50%] w-full h-1 ${status === 'completed' ? 'bg-green-500' : 'bg-gray-200'}`} style={{ zIndex: 0 }} />
                                        )}

                                        <div className="relative z-10 flex items-center justify-center w-8 h-8 rounded-full shadow-sm ring-4 ring-white"
                                          style={{
                                            backgroundColor: status === 'completed' ? '#22c55e' : status === 'current' ? '#eab308' : status === 'rejected' ? '#ef4444' : '#d1d5db',
                                            color: 'white'
                                          }}>
                                          {status === 'completed' && <Check className="w-4 h-4" />}
                                          {status === 'current' && <Clock className="w-4 h-4" />}
                                          {status === 'rejected' && <X className="w-4 h-4" />}
                                          {status === 'pending' && <div className="w-2.5 h-2.5 bg-white rounded-full opacity-50" />}
                                        </div>

                                        <div className={`mt-3 flex flex-col items-center p-2 rounded-md w-full ${status === 'current' ? 'bg-yellow-50 border border-yellow-200 shadow-sm' : ''}`}>
                                          <span className="font-bold text-zinc-900 text-[15px]">{step.label.split(': ').pop()}</span>

                                          {status === 'completed' && (
                                            <div className="flex flex-col items-center mt-1.5 space-y-1">
                                              {data?.signature?.signer_name && <span className="text-sm font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">{data.signature.signer_name}</span>}
                                              {data?.created_at && <span className="text-[13px] text-zinc-500 font-medium">{formatDate(data.created_at)}</span>}
                                            </div>
                                          )}
                                          {status === 'current' && (
                                            <div className="flex flex-col items-center mt-1.5 space-y-1">
                                              <span className="text-[13px] text-yellow-700 font-bold bg-yellow-200/50 px-2 py-0.5 rounded border border-yellow-300/50">
                                                Đang chờ
                                              </span>
                                            </div>
                                          )}
                                          {status === 'rejected' && (
                                            <div className="flex flex-col items-center mt-1.5 space-y-1">
                                              <span className="text-sm font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-100">Đã từ chối</span>
                                              {data?.created_at && <span className="text-[13px] text-zinc-500 font-medium">{formatDate(data.created_at)}</span>}
                                              {data?.note && <span className="text-[13px] text-red-500 italic line-clamp-2 mt-0.5" title={data.note}>{data.note}</span>}
                                            </div>
                                          )}
                                          {status === 'pending' && (
                                            <div className="flex flex-col items-center mt-1.5 space-y-1">
                                              <span className="text-[13px] text-zinc-400 font-medium bg-zinc-50 px-2 py-0.5 rounded border border-zinc-100">
                                                Chưa tới
                                              </span>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
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
