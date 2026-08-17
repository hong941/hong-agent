import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  List,
  Row,
  Space,
  Statistic,
  Table,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import type { EChartsOption } from "echarts";
import { api, getStoredUser } from "../api";
import type { Dashboard, Patient } from "../types";
import Chart from "../components/Chart";
import RiskTag from "../components/RiskTag";

export default function OpsDashboard() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const role = getStoredUser()?.role;
  const canHandover = role === "nurse" || role === "admin";

  const load = async () => {
    try {
      setDashboard(await api.dashboard());
    } catch (error) {
      message.error(error instanceof Error ? error.message : "加载运营数据失败");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const riskOption = useMemo<EChartsOption>(() => {
    const data =
      dashboard?.risk_distribution.map((item) => ({
        name:
          item.tier === "red" ? "高风险" : item.tier === "yellow" ? "中风险" : "低风险",
        value: item.count,
      })) || [];
    return {
      tooltip: { trigger: "item" },
      legend: { bottom: 0 },
      series: [
        {
          type: "pie",
          radius: ["42%", "68%"],
          data,
          color: ["#c6474b", "#d69c2f", "#2f7d5a"],
          label: { formatter: "{b}: {c}" },
        },
      ],
    };
  }, [dashboard]);

  const departmentOption = useMemo<EChartsOption>(() => {
    const status = dashboard?.department_status || [];
    return {
      tooltip: { trigger: "axis" },
      grid: { left: 40, right: 24, top: 32, bottom: 64 },
      xAxis: {
        type: "category",
        data: status.map((item) => item.name),
        axisLabel: { rotate: 35, fontSize: 11 },
      },
      yAxis: { type: "value", max: 100 },
      series: [
        {
          name: "负载",
          type: "bar",
          data: status.map((item) => item.load),
          itemStyle: { color: "#0e6e6e" },
        },
      ],
    };
  }, [dashboard]);

  const columns: ColumnsType<Patient> = [
    { title: "姓名", dataIndex: "name" },
    { title: "年龄", dataIndex: "age", width: 60 },
    { title: "主诉", dataIndex: "chief_complaint", ellipsis: true },
    {
      title: "风险",
      dataIndex: "risk_level",
      width: 90,
      render: (tier: string) => <RiskTag tier={tier} />,
    },
    { title: "状态", dataIndex: "status", width: 110 },
    { title: "科室", dataIndex: "department_name", width: 100 },
  ];

  const auditColumns: ColumnsType<Dashboard["recent_audit"][number]> = [
    { title: "操作人", dataIndex: "actor", width: 120 },
    { title: "动作", dataIndex: "action", width: 150 },
    { title: "对象", dataIndex: "target_type", width: 100 },
    { title: "时间", dataIndex: "created_at", width: 180 },
  ];

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Card className="metric-card">
            <Statistic title="候诊中" value={dashboard?.waiting_count || 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card className="metric-card">
            <Statistic title="分诊中" value={dashboard?.triage_count || 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card className="metric-card">
            <Statistic title="已挂号" value={dashboard?.scheduled_count || 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card className="metric-card">
            <Statistic
              title="高风险预警"
              value={dashboard?.red_alert_count || 0}
              valueStyle={{ color: "#c6474b" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={10}>
          <div className="panel">
            <div className="panel-title">风险分布</div>
            <Chart option={riskOption} />
          </div>
        </Col>
        <Col xs={24} lg={14}>
          <div className="panel">
            <div className="panel-title">科室负载</div>
            <Chart option={departmentOption} />
          </div>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <div className="panel">
            <div className="panel-title">候诊队列</div>
            <Table
              rowKey="id"
              size="small"
              columns={columns}
              dataSource={dashboard?.queue || []}
              pagination={false}
            />
          </div>
        </Col>
        <Col xs={24} lg={10}>
          <div className="panel">
            <div className="panel-title">风险预警</div>
            {dashboard?.alerts.length ? (
              <List
                dataSource={dashboard.alerts}
                renderItem={(item) => (
                  <List.Item
                    actions={
                      canHandover
                        ? [
                            <Button
                              key="handover"
                              size="small"
                              onClick={async () => {
                                try {
                                  await api.handover(item.patient_id);
                                  message.success("已接管");
                                  load();
                                } catch (error) {
                                  message.error(
                                    error instanceof Error ? error.message : "接管失败"
                                  );
                                }
                              }}
                            >
                              接管
                            </Button>,
                          ]
                        : undefined
                    }
                  >
                    <div>
                      <Space wrap>
                        <Typography.Text strong>{item.patient_name}</Typography.Text>
                        <RiskTag tier={item.risk_level} />
                        <Typography.Text type="secondary">
                          {item.age} 岁
                        </Typography.Text>
                      </Space>
                      <div>
                        <Typography.Text type="secondary">
                          {item.chief_complaint}
                        </Typography.Text>
                      </div>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <Alert type="success" showIcon message="当前无高风险预警" />
            )}
          </div>
        </Col>
      </Row>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="panel-title">最近审计</div>
        <Table
          rowKey="id"
          size="small"
          columns={auditColumns}
          dataSource={dashboard?.recent_audit || []}
          pagination={false}
        />
      </div>
    </div>
  );
}
