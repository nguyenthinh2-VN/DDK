import { Outlet, Navigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { FileScan, Upload, LayoutDashboard, LogOut, Globe, PenTool, Users, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "../hooks/useTranslation";

export default function DashboardLayout() {
  const { isAuthenticated, loading, logout, user } = useAuth();
  const { t, lang } = useTranslation();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Đang tải...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const toggleLanguage = () => {
    const newLang = lang === "vi" ? "tw" : "vi";
    localStorage.setItem("app_language", newLang);
    window.dispatchEvent(new Event("languageChange"));
  };

  const menuItems = [
    { title: t('layout.menu.dashboard'), url: "/", icon: LayoutDashboard },
    { title: t('layout.menu.scans'), url: "/scans", icon: FileScan },
    { title: t('audit.title'), url: "/audit-logs", icon: History },
    { title: t('layout.menu.upload'), url: "/upload", icon: Upload },
    { title: t('layout.menu.signature'), url: "/signature", icon: PenTool },
  ];

  if (user?.role_level && user.role_level <= 3) {
    menuItems.push({ title: t('layout.menu.users'), url: "/users", icon: Users });
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-zinc-50/50">
        <Sidebar>
          <SidebarHeader className="border-b p-4">
            <h2 className="text-xl font-bold tracking-tight">DDK OCR</h2>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Chức năng chính</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {menuItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild>
                        <Link to={item.url}>
                          <item.icon className="mr-2 h-4 w-4" />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter className="border-t p-4">
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-sm font-medium">{user?.full_name}</span>
                <span className="text-xs text-zinc-500 capitalize">{user?.role}</span>
              </div>
              <button onClick={logout} className="p-2 hover:bg-zinc-100 rounded-md transition-colors" title="Đăng xuất">
                <LogOut className="h-4 w-4 text-zinc-600" />
              </button>
            </div>
          </SidebarFooter>
        </Sidebar>

        <main className="flex-1 flex flex-col min-h-screen overflow-hidden">
          <header className="h-14 flex items-center px-4 border-b bg-white justify-between">
            <div className="flex items-center gap-2">
              <SidebarTrigger />
              <div className="font-medium text-sm ml-2 hidden sm:block">
                {t('layout.header.title')}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleLanguage}
                className="flex items-center gap-2"
                title="Đổi ngôn ngữ"
              >
                <Globe className="w-4 h-4" />
                <span>{lang === "vi" ? "VN" : "TW"}</span>
              </Button>
            </div>
          </header>
          <div className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
