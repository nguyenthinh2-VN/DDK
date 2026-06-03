import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import axiosClient from "../../api/axiosClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Lock, User } from "lucide-react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const payload = {
        username: username,
        password: password,
      };

      const response = await axiosClient.post("/api/auth/login", payload);
      const token = response.data.access_token;

      // Save token temporarily so the interceptor can use it for /auth/me
      localStorage.setItem("access_token", token);

      const meResponse = await axiosClient.get("/api/auth/me");

      login(token, meResponse.data);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.");
    } finally {
      setIsLoading(false);
    }
  };

  const [lang, setLang] = useState(localStorage.getItem("app_language") || "vi");

  const handleLangChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLang = e.target.value;
    setLang(newLang);
    localStorage.setItem("app_language", newLang);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 relative overflow-hidden">

      {/* Language Switcher */}
      <div className="absolute top-4 right-4 z-20">
        <select
          value={lang}
          onChange={handleLangChange}
          className="bg-white text-zinc-900 border border-zinc-200 rounded-md px-3 py-1 text-sm outline-none focus:border-zinc-300 transition-colors cursor-pointer"
        >
          <option value="vi">Tiếng Việt</option>
          <option value="tw">繁體中文</option>
        </select>
      </div>

      <Card className="w-full max-w-md z-10 shadow-md">
        <CardHeader className="space-y-1 pb-8">
          <CardTitle className="text-3xl font-bold text-center tracking-tight text-zinc-900">DDK OCR</CardTitle>
          <CardDescription className="text-center text-zinc-500">
            Đăng nhập vào hệ thống quản lý
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-destructive/15 text-destructive p-3 rounded-md text-sm text-center font-medium shadow-sm transition-all duration-300 animate-in fade-in zoom-in">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="username">Tài khoản</Label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-zinc-400" />
                <Input
                  id="username"
                  placeholder="admin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-zinc-400" />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="pl-9"
                />
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? "Đang xử lý..." : "Đăng nhập"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
