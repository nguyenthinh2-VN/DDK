import React from "react";
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
import { FileScan, Upload, LayoutDashboard, LogOut } from "lucide-react";

const menuItems = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Danh sách phiếu (Scan)", url: "/scans", icon: FileScan },
  { title: "Upload", url: "/upload", icon: Upload },
];

export default function DashboardLayout() {
  const { isAuthenticated, loading, logout, user } = useAuth();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Đang tải...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
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
                <span className="text-sm font-medium">{user?.fullname}</span>
                <span className="text-xs text-zinc-500 capitalize">{user?.role}</span>
              </div>
              <button onClick={logout} className="p-2 hover:bg-zinc-100 rounded-md transition-colors" title="Đăng xuất">
                <LogOut className="h-4 w-4 text-zinc-600" />
              </button>
            </div>
          </SidebarFooter>
        </Sidebar>

        <main className="flex-1 flex flex-col min-h-screen overflow-hidden">
          <header className="h-14 flex items-center px-4 border-b bg-white">
            <SidebarTrigger />
            <div className="ml-auto font-medium text-sm">
              Hệ thống xử lý Phiếu tạm ứng
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
