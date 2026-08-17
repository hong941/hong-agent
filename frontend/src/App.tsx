import { useMemo, useState } from "react";
import {
  DashboardOutlined,
  LogoutOutlined,
  MedicineBoxOutlined,
  RobotOutlined,
  SettingOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Button, Layout, Tabs, Typography } from "antd";
import { api, clearUser, getStoredUser } from "./api";
import type { User } from "./types";
import AdminConsole from "./pages/AdminConsole";
import DoctorWorkstation from "./pages/DoctorWorkstation";
import OpsDashboard from "./pages/OpsDashboard";
import PatientPortal from "./pages/PatientPortal";
import Login from "./components/Login";

const roleTabKeys: Record<string, string[]> = {
  patient: ["patient"],
  doctor: ["doctor"],
  nurse: ["doctor", "ops"],
  admin: ["ops", "admin"],
};

export default function App() {
  const [user, setUser] = useState<User | null>(() => getStoredUser());

  const tabItems = useMemo(() => {
    const keys = user ? roleTabKeys[user.role] || ["patient"] : [];
    const items = [
      {
        key: "patient",
        label: "患者端",
        icon: <UserOutlined />,
        children: <PatientPortal />,
      },
      {
        key: "doctor",
        label: "医生端",
        icon: <MedicineBoxOutlined />,
        children: <DoctorWorkstation />,
      },
      {
        key: "ops",
        label: "运营端",
        icon: <DashboardOutlined />,
        children: <OpsDashboard />,
      },
      {
        key: "admin",
        label: "管理端",
        icon: <SettingOutlined />,
        children: <AdminConsole />,
      },
    ];
    return items.filter((item) => keys.includes(item.key));
  }, [user]);

  const handleLogout = () => {
    clearUser();
    setUser(null);
  };

  if (!user) {
    return <Login onLogin={(next) => setUser(next)} />;
  }

  return (
    <Layout className="app-shell">
      <Layout.Header className="app-header">
        <div className="app-header-title">
          <RobotOutlined style={{ color: "#0e6e6e", fontSize: 22 }} />
          <Typography.Title level={4}>AI 智慧医院</Typography.Title>
        </div>
        <div className="app-user">
          <span>
            {user.name} · {user.role}
          </span>
          <Button size="small" icon={<LogoutOutlined />} onClick={handleLogout}>
            退出
          </Button>
        </div>
      </Layout.Header>
      <Layout.Content className="app-content">
        <Tabs
          className="page-tabs"
          defaultActiveKey={tabItems[0]?.key}
          items={tabItems}
        />
      </Layout.Content>
    </Layout>
  );
}
