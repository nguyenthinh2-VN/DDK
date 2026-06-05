import React, { useState, useEffect } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { useTranslation } from "../../hooks/useTranslation";
import axiosClient from "../../api/axiosClient";
import UserFormDialog from "./UserFormDialog";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Edit, Trash2, Plus, Users as UsersIcon } from "lucide-react";
import { toast, useToast } from "@/hooks/use-toast";

export default function UserManager() {
  const { t, lang } = useTranslation();
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Dialog state
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<any | null>(null);

  // Permission checks
  const canCreate = currentUser?.role_level && currentUser.role_level <= 2; // Director+
  const canDelete = currentUser?.role_level === 1; // CEO

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await axiosClient.get("/api/admin/users");
      setUsers(res.data);
    } catch (error) {
      console.error("Failed to fetch users", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreate = () => {
    setEditingUser(null);
    setIsDialogOpen(true);
  };

  const handleEdit = (user: any) => {
    setEditingUser(user);
    setIsDialogOpen(true);
  };

  const handleDelete = async (user: any) => {
    if (!window.confirm(t("users.confirm.delete"))) return;
    try {
      await axiosClient.delete(`/api/admin/users/${user.id}`);
      toast({
        title: "Thành công",
        description: t("users.alert.delete_success"),
      });
      fetchUsers();
    } catch (error: any) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: error.response?.data?.detail || t("users.alert.delete_fail"),
      });
    }
  };

  if (loading && users.length === 0) {
    return <div className="flex items-center justify-center p-10">Đang tải...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-lg border shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/10 rounded-full text-primary">
            <UsersIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900">{t("users.title")}</h1>
            <p className="text-zinc-500">{t("users.desc")}</p>
          </div>
        </div>
        {canCreate && (
          <Button onClick={handleCreate} className="w-full sm:w-auto shadow-sm">
            <Plus className="w-4 h-4 mr-2" />
            {t("users.btn.create")}
          </Button>
        )}
      </div>

      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-zinc-50">
            <TableRow>
              <TableHead>{t("users.table.username")}</TableHead>
              <TableHead>{t("users.table.fullname")}</TableHead>
              <TableHead>{t("users.table.role")}</TableHead>
              <TableHead>{t("users.table.status")}</TableHead>
              <TableHead>{t("users.table.created_at")}</TableHead>
              <TableHead className="text-right">{t("users.table.actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  {t("users.table.empty")}
                </TableCell>
              </TableRow>
            ) : (
              users.map((u) => (
                <TableRow key={u.id} className="hover:bg-zinc-50/50">
                  <TableCell className="font-medium">{u.username}</TableCell>
                  <TableCell>{u.full_name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="font-normal text-xs">
                      {lang === "tw" ? u.role?.name : u.role?.display_name}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {u.is_active ? (
                      <Badge variant="outline" className="bg-emerald-50 text-emerald-600 border-emerald-200">
                        {t("users.status.active")}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-rose-50 text-rose-600 border-rose-200">
                        {t("users.status.inactive")}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(u.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEdit(u)}
                        title={t("users.btn.edit")}
                        className="h-8 w-8 text-zinc-500 hover:text-primary"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      {canDelete && currentUser?.id !== u.id && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(u)}
                          title={t("users.btn.delete")}
                          className="h-8 w-8 text-zinc-500 hover:text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <UserFormDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        onSuccess={fetchUsers}
        user={editingUser}
      />
    </div>
  );
}
