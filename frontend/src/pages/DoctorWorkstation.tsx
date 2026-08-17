import { useEffect, useState } from "react";
import {
  Button,
  Descriptions,
  Input,
  List,
  Space,
  Spin,
  Table,
  Tabs,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { api } from "../api";
import type { Followup, KnowledgeHit, Patient, SOAP, Summary } from "../types";
import RiskTag from "../components/RiskTag";

export default function DoctorWorkstation() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selected, setSelected] = useState<Patient | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [soap, setSoap] = useState<SOAP | null>(null);
  const [followup, setFollowup] = useState<Followup | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeHit[]>([]);
  const [knowledgeQuery, setKnowledgeQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const loadPatients = async () => {
    try {
      const data = await api.patients();
      setPatients(data);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "加载患者失败");
    }
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleSelect = (patient: Patient) => {
    setSelected(patient);
    setSummary(null);
    setSoap(null);
    setFollowup(null);
  };

  const handleSummary = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      setSummary(await api.summary(selected.id));
    } catch (error) {
      message.error(error instanceof Error ? error.message : "生成摘要失败");
    } finally {
      setLoading(false);
    }
  };

  const handleSOAP = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      setSoap(await api.soap(selected.id));
    } catch (error) {
      message.error(error instanceof Error ? error.message : "生成 SOAP 失败");
    } finally {
      setLoading(false);
    }
  };

  const handleFollowup = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      setFollowup(await api.followup(selected.id));
    } catch (error) {
      message.error(error instanceof Error ? error.message : "生成随访计划失败");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchKnowledge = async (value: string) => {
    setKnowledgeQuery(value);
    if (!value.trim()) {
      setKnowledge([]);
      return;
    }
    try {
      setKnowledge(await api.searchKnowledge(value));
    } catch (error) {
      message.error(error instanceof Error ? error.message : "检索失败");
    }
  };

  const columns: ColumnsType<Patient> = [
    { title: "姓名", dataIndex: "name" },
    { title: "年龄", dataIndex: "age", width: 70 },
    { title: "性别", dataIndex: "gender", width: 70 },
    {
      title: "风险",
      dataIndex: "risk_level",
      width: 100,
      render: (tier: string) => <RiskTag tier={tier} />,
    },
    { title: "状态", dataIndex: "status", width: 110 },
    {
      title: "科室",
      dataIndex: "department_name",
      width: 110,
      render: (value: string | null) => value || "待定",
    },
  ];

  const citationList = (
    <List
      size="small"
      dataSource={summary?.citations || soap?.citations || followup?.citations || []}
      renderItem={(item) => (
        <List.Item>
          <Typography.Text>
            {item.title} · {item.source}
          </Typography.Text>
        </List.Item>
      )}
    />
  );

  return (
    <div className="work-grid">
      <div className="panel">
        <div className="panel-title">患者列表</div>
        <Table
          rowKey="id"
          size="small"
          columns={columns}
          dataSource={patients}
          pagination={{ pageSize: 8 }}
          onRow={(record) => ({
            onClick: () => handleSelect(record),
            style: {
              cursor: "pointer",
              background: selected?.id === record.id ? "#eef7f6" : undefined,
            },
          })}
        />
      </div>
      <div className="panel">
        <div className="panel-title">医生工作站</div>
        {selected ? (
          <>
            <Descriptions
              size="small"
              column={{ xs: 1, sm: 2, md: 3 }}
              bordered
              style={{ marginBottom: 12 }}
            >
              <Descriptions.Item label="姓名">{selected.name}</Descriptions.Item>
              <Descriptions.Item label="年龄">{selected.age}</Descriptions.Item>
              <Descriptions.Item label="性别">{selected.gender}</Descriptions.Item>
              <Descriptions.Item label="主诉">{selected.chief_complaint}</Descriptions.Item>
              <Descriptions.Item label="风险">
                <RiskTag tier={selected.risk_level} />
              </Descriptions.Item>
              <Descriptions.Item label="状态">{selected.status}</Descriptions.Item>
              <Descriptions.Item label="既往史">{selected.medical_history || "未记录"}</Descriptions.Item>
              <Descriptions.Item label="过敏史">{selected.allergies || "未记录"}</Descriptions.Item>
              <Descriptions.Item label="用药">{selected.medications || "未记录"}</Descriptions.Item>
            </Descriptions>
            <Tabs
              items={[
                {
                  key: "summary",
                  label: "AI 摘要",
                  children: (
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                      <Button type="primary" loading={loading} onClick={handleSummary}>
                        生成摘要
                      </Button>
                      {summary && <p className="ai-output">{summary.summary}</p>}
                    </Space>
                  ),
                },
                {
                  key: "soap",
                  label: "SOAP 草稿",
                  children: (
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                      <Button type="primary" loading={loading} onClick={handleSOAP}>
                        生成 SOAP
                      </Button>
                      {soap && (
                        <>
                          <p className="ai-output">S（主观）：{soap.subjective}</p>
                          <p className="ai-output">O（客观）：{soap.objective}</p>
                          <p className="ai-output">A（评估）：{soap.assessment}</p>
                          <p className="ai-output">P（计划）：{soap.plan}</p>
                        </>
                      )}
                    </Space>
                  ),
                },
                {
                  key: "followup",
                  label: "随访计划",
                  children: (
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                      <Button type="primary" loading={loading} onClick={handleFollowup}>
                        生成随访计划
                      </Button>
                      {followup && <p className="ai-output">{followup.plan}</p>}
                    </Space>
                  ),
                },
                {
                  key: "knowledge",
                  label: "知识检索",
                  children: (
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                      <Input.Search
                        value={knowledgeQuery}
                        onChange={(e) => setKnowledgeQuery(e.target.value)}
                        onSearch={handleSearchKnowledge}
                        placeholder="输入症状或主题"
                      />
                      <List
                        size="small"
                        dataSource={knowledge}
                        renderItem={(item) => (
                          <List.Item>
                            <div>
                              <Typography.Text strong>{item.title}</Typography.Text>
                              <Typography.Paragraph
                                type="secondary"
                                style={{ margin: "4px 0 0" }}
                              >
                                {item.content}
                              </Typography.Paragraph>
                              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                                来源：{item.source}
                              </Typography.Text>
                            </div>
                          </List.Item>
                        )}
                      />
                    </Space>
                  ),
                },
              ]}
            />
            {(summary || soap || followup) && (
              <div style={{ marginTop: 12 }}>
                <Typography.Text strong>引用来源</Typography.Text>
                {citationList}
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {(summary?.disclaimer || soap?.disclaimer || followup?.disclaimer) ?? ""}
                </Typography.Text>
              </div>
            )}
          </>
        ) : (
          <Spin tip="请选择患者" />
        )}
      </div>
    </div>
  );
}
