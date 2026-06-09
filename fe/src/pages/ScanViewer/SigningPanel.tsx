/**
 * SigningPanel - Panel phần ký duyệt, tách biệt hoàn toàn với bảng dữ liệu.
 *
 * Hiển thị 4 ô ký (EMPLOYEE, TREASURY, ACCOUNTING, CEO) theo dạng grid ngang.
 * Mỗi ô ký hiển thị:
 *   - Tên vai trò (tiếng Trung + tiếng Việt)
 *   - Chữ ký hiện tại (nếu có)
 *   - Nút ký / xóa / duyệt tương ứng với vai trò và trạng thái workflow
 */
import { Stamp, CheckCircle2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Approval {
  role: string;
  action: string;
  signature?: { processed_file_path?: string };
}

interface SigningRole {
  role: string;
  requiredStatus: string;
  label: string;
  sublabel: string;
}

const SIGNING_ROLES: SigningRole[] = [
  { role: "EMPLOYEE", requiredStatus: "DRAFT", label: "簽收", sublabel: "Ký nhận" },
  { role: "CEO", requiredStatus: "PENDING_CEO", label: "總經理", sublabel: "Tổng Giám Đốc" },
  { role: "TREASURY", requiredStatus: "PENDING_TREASURY", label: "出納", sublabel: "Thủ quỹ" },
  { role: "ACCOUNTING", requiredStatus: "PENDING_ACCOUNTING", label: "會計", sublabel: "Kế toán" },
  { role: "SUB_TREASURY", requiredStatus: "PENDING_SUB_TREASURY", label: "出納", sublabel: "Thủ quỹ phụ" },
];

interface SigningPanelProps {
  wfStatus: string;
  userRole?: string;
  approvals: Approval[];
  onSign: (role: string) => void;
  onApprove: () => void;
  onRemoveDraft: () => void;
  getFileUrl: (path?: string) => string;
  isLoading?: boolean;
}

import { useTranslation } from "@/hooks/useTranslation";
import { Loader2 } from "lucide-react";

export default function SigningPanel({
  wfStatus,
  userRole,
  approvals,
  onSign,
  onApprove,
  onRemoveDraft,
  getFileUrl,
  isLoading,
}: SigningPanelProps) {
  const { t } = useTranslation();

  const getApproval = (role: string) =>
    approvals?.find((a) => a.role === role && (a.action === "APPROVED" || a.action === "DRAFT"));

  const hasDraft = (role: string) =>
    !!approvals?.find((a) => a.role === role && a.action === "DRAFT");

  return (
    <div className="border rounded-md overflow-hidden mt-3">
      <div className="px-3 py-2 bg-muted/40 border-b">
        <h3 className="text-sm font-semibold">Chữ ký / 簽名</h3>
      </div>
      <div className="grid grid-cols-5 divide-x">
        {SIGNING_ROLES.map(({ role, requiredStatus, label, sublabel }) => {
          const approval = getApproval(role);
          const isDraft = hasDraft(role);
          const isMyTurn = wfStatus === requiredStatus && userRole === role;
          const sigUrl = approval?.signature?.processed_file_path
            ? getFileUrl(approval.signature.processed_file_path)
            : null;

          return (
            <div key={role} className="p-3 flex flex-col items-center gap-2 min-w-0">
              {/* Tên vai trò */}
              <div className="text-center">
                <div className="font-bold text-sm">{label}</div>
                <div className="text-xs text-muted-foreground">{sublabel}</div>
              </div>

              {/* Khu vực chữ ký */}
              <div className="min-h-[3rem] flex items-center justify-center w-full relative">
                {isLoading && isMyTurn ? (
                  <div className="flex justify-center items-center h-12">
                    <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                  </div>
                ) : sigUrl ? (
                  <div className="relative">
                    <img src={sigUrl} alt="Chữ ký" className="max-h-12 object-contain mx-auto" />
                    {isDraft && (
                      <span className="absolute -top-2 -right-2 text-[9px] bg-yellow-100 text-yellow-800 border border-yellow-200 px-1 py-0.5 rounded">
                        Nháp
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="w-full border-b border-dashed border-muted-foreground/30 h-px" />
                )}
              </div>

              {/* Nút hành động */}
              {isDraft ? (
                <div className="flex gap-1 w-full">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 text-xs px-1 text-red-600"
                    onClick={onRemoveDraft}
                    disabled={!isMyTurn || isLoading}
                  >
                    <Trash2 className="w-3 h-3 mr-1" /> {t('users.btn.delete') || 'Xóa'}
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1 text-xs px-1"
                    onClick={onApprove}
                    disabled={!isMyTurn || isLoading}
                  >
                    <CheckCircle2 className="w-3 h-3 mr-1" /> {t('scan.detail.sign_approve')}
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => onSign(role)}
                  disabled={!isMyTurn || isLoading}
                >
                  <Stamp className="w-3 h-3 mr-1" />
                  {role === "EMPLOYEE" ? t('scan.detail.sign_submit') : t('scan.detail.sign_approve')}
                </Button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
