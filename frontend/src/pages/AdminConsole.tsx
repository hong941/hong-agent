import { useEffect, useState } from "react";
import {
  Button,
  Descriptions,
  Form,
  Input,
  Modal,
  Space,
  Table,
  Tabs,
  Tag,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { api } from "../api";
import type { Audit, KnowledgeItem, SystemStatus } from "../types";

export default function AdminConsole() {
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [system, setSystem] = useState<SystemStatus | null>(null);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const loadAll = async () => {
    try {
      const [knowledgeData, auditData, systemData] = await Promise.all([
        api.adminKnowledge(),
        api.adminAudit(),
        api.systemStatus(),
      ]);
      setKnowledge(knowledgeData);
      setAudit(auditData);
      setSystem(systemData);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "加载管理数据失败");
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleCreate = async (values: {
    title: string;
    category: string;
    content: string;
    source: string;
    tags: string;
  }) => {
    try {
      await api.createKnowledge({
        title: values.title,
        category: values.category,
        content: values.content,
        source: values.source,
        tags: values.tags
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      message.success("已添加");
      setOpen(false);
      form.resetFields();
      loadAll();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "添加失败");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteKnowledge(id);
      message.success("已删除");
      loadAll();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "删除失败");
    }
  };

  const knowledgeColumns: ColumnsType<KnowledgeItem> = [
    { title: "标题", dataIndex: "title" },
    { title: "分类", dataIndex: "category", width: 120 },
    {
      title: "内容",
      dataIndex: "content",
      ellipsis: true,
    },
    { title: "来源", dataIndex: "source", width: 180 },
    {
      title: "操作",
      width: 90,
      render: (_, record) => (
        <Button size="small" danger onClick={() => handleDelete(record.id)}>
          删除
        </Button>
      ),
    },
  ];

  const auditColumns: ColumnsType<Audit> = [
    { title: "操作人", dataIndex: "actor", width: 120 },
    { title: "动作", dataIndex: "action", width: 160 },
    { title: "对象", dataIndex: "target_type", width: 110 },
    { title: "对象 ID", dataIndex: "target_id", width: 100 },
    { title: "时间", dataIndex: "created_at", width: 190 },
  ];

  return (
    <div>
      <Tabs
        items={[
          {
            key: "knowledge",
            label: "知识库",
            children: (
              <div className="panel">
                <Space style={{ width: "100%", justifyContent: "space-between" }}>
                  <div className="panel-title">医疗知识条目</div>
                  <Button type="primary" onClick={() => setOpen(true)}>
                    新增条目
                  </Button>
                </Space>
                <Table
                  rowKey="id"
                  size="small"
                  columns={knowledgeColumns}
                  dataSource={knowledge}
                  pagination={{ pageSize: 8 }}
                />
              </div>
            ),
          },
          {
            key: "audit",
            label: "审计日志",
            children: (
              <div className="panel">
                <div className="panel-title">审计日志</div>
                <Table
                  rowKey="id"
                  size="small"
                  columns={auditColumns}
                  dataSource={audit}
                  pagination={{ pageSize: 10 }}
                />
              </div>
            ),
          },
          {
            key: "system",
            label: "系统状态",
            children: (
              <div className="panel">
                <div className="panel-title">系统状态</div>
                {system && (
                  <Descriptions bordered column={{ xs: 1, md: 2 }}>
                    <Descriptions.Item label="模型模式">
                      <Tag color={system.provider_mode === "mock" ? "orange" : "green"}>
                        {system.provider_mode}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="模型">{system.model_name}</Descriptions.Item>
                    <Descriptions.Item label="数据库">{system.database_url}</Descriptions.Item>
                    <Descriptions.Item label="API Base">{system.api_base_url}</Descriptions.Item>
                    <Descriptions.Item label="知识条目">{system.knowledge_count}</Descriptions.Item>
                    <Descriptions.Item label="患者数量">{system.patient_count}</Descriptions.Item>
                  </Descriptions>
                )}
              </div>
            ),
          },
        ]}
      />
      <Modal
        title="新增知识条目"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="source" label="来源">
            <Input />
          </Form.Item>
          <Form.Item name="tags" label="标签（逗号分隔）">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
