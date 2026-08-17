import { Tag } from "antd";

const colorMap: Record<string, string> = {
  red: "red",
  yellow: "gold",
  green: "green",
};

const labelMap: Record<string, string> = {
  red: "高风险",
  yellow: "中风险",
  green: "低风险",
};

export default function RiskTag({ tier }: { tier: string }) {
  return (
    <Tag color={colorMap[tier] || "default"}>{labelMap[tier] || tier}</Tag>
  );
}
