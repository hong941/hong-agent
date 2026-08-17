import { useState } from "react";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  InputNumber,
  List,
  Select,
  Space,
  Tag,
  Typography,
  message,
} from "antd";
import { CalendarOutlined, SendOutlined } from "@ant-design/icons";
import { api } from "../api";
import type { Appointment, TriageResult } from "../types";
import RiskTag from "../components/RiskTag";

interface ChatMessage {
  role: string;
  content: string;
}

export default function PatientPortal() {
  const [form] = Form.useForm();
  const [session, setSession] = useState<{
    patientId: number;
    conversationId: number;
  } | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [canComplete, setCanComplete] = useState(false);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState(false);

  const handleStart = async (values: {
    name: string;
    age: number;
    gender: string;
    chief_complaint: string;
    phone?: string;
  }) => {
    try {
      const data = await api.startTriage(values);
      setSession({ patientId: data.patient_id, conversationId: data.conversation_id });
      setMessages([{ role: "assistant", content: data.message }]);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "启动预问诊失败");
    }
  };

  const handleSend = async () => {
    if (!session || !input.trim()) return;
    const content = input.trim();
    setMessages((prev) => [...prev, { role: "user", content }]);
    setInput("");
    try {
      const data = await api.answerTriage(session.conversationId, content);
      setMessages((prev) => [...prev, { role: "assistant", content: data.message }]);
      setCanComplete(data.can_complete);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "发送失败");
    }
  };

  const handleComplete = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const data = await api.completeTriage(session.patientId);
      setResult(data);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "分诊失败");
    } finally {
      setLoading(false);
    }
  };

  const handleBook = async () => {
    if (!session || !result) return;
    setLoading(true);
    try {
      const data = await api.bookAppointment(session.patientId, result.department_id);
      setAppointment(data);
      message.success("预约成功");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "预约失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {!session ? (
        <div className="panel">
          <div className="panel-title">就诊信息</div>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleStart}
            initialValues={{ age: 30, gender: "男" }}
          >
            <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
              <Input placeholder="请输入姓名" />
            </Form.Item>
            <Form.Item name="age" label="年龄" rules={[{ required: true }]}>
              <InputNumber min={0} max={120} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="gender" label="性别" rules={[{ required: true }]}>
              <Select options={[{ value: "男" }, { value: "女" }, { value: "其他" }]} />
            </Form.Item>
            <Form.Item name="chief_complaint" label="主要症状" rules={[{ required: true }]}>
              <Input.TextArea
                rows={3}
                placeholder="例如：活动后胸痛伴胸闷 1 小时"
              />
            </Form.Item>
            <Form.Item name="phone" label="联系电话">
              <Input placeholder="选填" />
            </Form.Item>
            <Button type="primary" htmlType="submit">
              开始预问诊
            </Button>
          </Form>
        </div>
      ) : (
        <div className="split-grid">
          <div className="panel">
            <div className="panel-title">智能预问诊</div>
            <div className="chat-list">
              {messages.map((item, index) => (
                <div
                  key={index}
                  className={
                    item.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"
                  }
                >
                  {item.content}
                </div>
              ))}
            </div>
            <Space.Compact style={{ width: "100%", marginTop: 12 }}>
              <Input.TextArea
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="补充症状持续时间、严重程度、过敏史等"
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                disabled={!input.trim()}
              >
                发送
              </Button>
            </Space.Compact>
            <Button
              block
              type="primary"
              disabled={!canComplete || !!result}
              loading={loading}
              onClick={handleComplete}
              style={{ marginTop: 10 }}
            >
              完成预问诊
            </Button>
          </div>

          <div className="panel">
            <div className="panel-title">分诊结果</div>
            {result ? (
              <Space direction="vertical" size={14} style={{ width: "100%" }}>
                <Space wrap>
                  <RiskTag tier={result.tier} />
                  <Tag>分 {result.score} 分</Tag>
                  <Tag color="blue">{result.department}</Tag>
                  <Tag>置信度 {Math.round(result.confidence * 100)}%</Tag>
                </Space>
                <Alert type="warning" showIcon message={result.recommendation} />
                <Descriptions column={1} size="small" bordered>
                  <Descriptions.Item label="判断依据">
                    {result.reasons.join("；")}
                  </Descriptions.Item>
                  <Descriptions.Item label="后续步骤">
                    <List
                      size="small"
                      dataSource={result.next_steps}
                      renderItem={(item) => <List.Item>{item}</List.Item>}
                    />
                  </Descriptions.Item>
                </Descriptions>
                {!appointment ? (
                  <Button
                    type="primary"
                    icon={<CalendarOutlined />}
                    loading={loading}
                    onClick={handleBook}
                  >
                    预约挂号
                  </Button>
                ) : (
                  <Alert
                    type="success"
                    showIcon
                    message="预约成功"
                    description={`${appointment.department_name} · ${new Date(
                      appointment.scheduled_time
                    ).toLocaleString("zh-CN")}`}
                  />
                )}
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {result.disclaimer}
                </Typography.Text>
              </Space>
            ) : (
              <Typography.Text type="secondary">
                完成预问诊后展示风险分级、科室建议和挂号结果。
              </Typography.Text>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
