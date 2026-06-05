import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Toaster } from "@/components/ui/toaster";
import Login from './pages/Login/Login';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard/Dashboard';
import ScanViewer from './pages/ScanViewer/ScanViewer';
import Scans from './pages/Scans/Scans';
import Upload from './pages/Upload/Upload';
import SignatureManager from './pages/Signature/SignatureManager';
import UserManager from './pages/Users/UserManager';
import AuditLog from './pages/AuditLog/AuditLog';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Private routes inside DashboardLayout */}
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="/scan/:id" element={<ScanViewer />} />
            <Route path="/scans" element={<Scans />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/signature" element={<SignatureManager />} />
            <Route path="/users" element={<UserManager />} />
            <Route path="/audit-logs" element={<AuditLog />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster />
    </AuthProvider>
  );
}

export default App;
