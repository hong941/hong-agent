import { RobotOutlined } from "@ant-design/icons";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { api, storeUser } from "../api";
import type { User } from "../types";

const quickAccounts = [
  { label: "患者", username: "patient_demo", password: "demo123" },
  { label: "医生", username: "doctor_zhang", password: "doctor123" },
  { label: "护士", username: "nurse_liu", password: "nurse123" },
  { label: "管理员", username: "admin", password: "admin123" },
];

export default function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [form] = Form.useForm();

  const handleSubmit = async (values: { username: string; password: string }) => {
    try {
      const user = await api.login(values.username, values.password);
      storeUser(user);
      onLogin(user);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "登录失败");
    }
  };

  const quickLogin = async (username: string, password: string) => {
    await handleSubmit({ username, password });
  };

  return (
    <div className="login-page">
      <Card className="login-panel">
        <div className="login-brand">
          <div className="login-brand-icon">
            <RobotOutlined />
          </div>
          <div>
            <Typography.Title level={3} style={{ margin: 0 }}>
              AI 智慧医院
            </Typography.Title>
            <Typography.Text type="secondary">智能分诊与 AI 病历助手</Typography.Text>
          </div>
        </div>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ username: "admin", password: "admin123" }}
        >
          <Form.Item name="username" label="账号" rules={[{ required: true }]}>
            <Input placeholder="请输入账号" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            登录
          </Button>
        </Form>
        <div className="quick-login">
          {quickAccounts.map((item) => (
            <Button key={item.username} onClick={() => quickLogin(item.username, item.password)}>
              {item.label}
            </Button>
          ))}
        </div>
      </Card>
    </div>
  );
}
