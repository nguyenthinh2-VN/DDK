import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import axiosClient from "../../api/axiosClient";
import { useTranslation } from "../../hooks/useTranslation";
import { useToast } from "@/hooks/use-toast";

interface Role {
  id: string;
  name: string;
  display_name: string;
  level: number;
}

interface UserFormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  user: any | null; // null if creating, object if editing
}

export default function UserFormDialog({ isOpen, onClose, onSuccess, user }: UserFormDialogProps) {
  const { t, lang } = useTranslation();
  const { toast } = useToast();
  const [roles, setRoles] = useState<Role[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form states
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [roleId, setRoleId] = useState("");
  const [isActive, setIsActive] = useState(true);

  const isEdit = !!user;

  useEffect(() => {
    if (isOpen) {
      fetchRoles();
      if (user) {
        setUsername(user.username);
        setPassword(""); // empty password on edit
        setFullName(user.full_name);
        setRoleId(user.role?.id || "");
        setIsActive(user.is_active);
      } else {
        setUsername("");
        setPassword("");
        setFullName("");
        setRoleId("");
        setIsActive(true);
      }
    }
  }, [isOpen, user]);

  const fetchRoles = async () => {
    try {
      const res = await axiosClient.get("/api/admin/roles");
      setRoles(res.data);
    } catch (error) {
      console.error("Failed to fetch roles", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (isEdit) {
        // Edit
        const payload: any = {
          full_name: fullName,
          role_id: roleId,
          is_active: isActive,
        };
        if (password) {
          payload.password = password;
        }
        await axiosClient.put(`/api/admin/users/${user.id}`, payload);
      } else {
        // Create
        const payload = {
          username,
          password,
          full_name: fullName,
          role_id: roleId,
        };
        await axiosClient.post("/api/admin/users", payload);
      }
      toast({
        title: "Thành công",
        description: t("users.alert.save_success"),
      });
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: error.response?.data?.detail || t("users.alert.save_fail"),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {isEdit ? t("users.form.edit_title") : t("users.form.create_title")}
            </DialogTitle>
            <DialogDescription>
              {isEdit ? t("users.form.edit_desc") : t("users.form.create_desc")}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="username">{t("users.form.username")}</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isEdit}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="password">
                {t("users.form.password")}
                <span className="text-xs font-normal text-muted-foreground ml-2">
                  ({isEdit ? t("users.form.password_edit_hint") : t("users.form.password_create_hint")})
                </span>
              </Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required={!isEdit}
                minLength={6}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="fullname">{t("users.form.fullname")}</Label>
              <Input
                id="fullname"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="role">{t("users.form.role")}</Label>
              <Select value={roleId} onValueChange={setRoleId} required>
                <SelectTrigger>
                  <SelectValue placeholder={t("users.form.role_placeholder")} />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem key={role.id} value={role.id}>
                      {lang === "tw" ? role.name : role.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {isEdit && (
              <div className="flex items-center justify-between mt-2">
                <Label htmlFor="status" className="flex flex-col gap-1">
                  <span>{t("users.form.status")}</span>
                </Label>
                <Switch
                  id="status"
                  checked={isActive}
                  onCheckedChange={setIsActive}
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
              {t("users.form.btn_cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t("users.form.btn_submitting") : t("users.form.btn_submit")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
