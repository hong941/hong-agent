# AI 智慧医院平台：简历项目描述

> 使用说明：文中 `[xx%]`、`[xx 秒]` 等为目标值/占位符。项目实测前请勿写入简历作为已达成结果；实测后替换为真实数据即可。

## 一句话定位

从 0 到 1 搭建的 AI 智慧医院平台原型，用大模型、RAG、规则引擎和 FHIR 数据标准，打通“患者智能分诊 - 医生 AI 助手 - 运营风险预警”的诊疗闭环。

## 项目背景与目标

- 背景：传统医院流程中，预问诊依赖人工、医生写病历耗时、患者就诊排队缺乏智能引导，AI 能力散落且难落地。
- 目标：以“AI 分诊 + AI 病历 + AI 运营”为主线，交付一套可演示、可评测、可私有化部署的智慧医院原型，同时形成完整的技术闭环和工程化沉淀。

## 我做了什么（What）

- 主导需求分析、系统设计、数据库建模、前后端开发、AI 能力接入与部署交付。
- 患者端：实现多轮结构化预问诊，自动采集症状、病史、过敏史、用药史；通过“规则引擎 + 大模型”双通道输出红黄绿风险分级，推荐科室与号源，并提供带安全边界的健康咨询。
- 医生端：实现 AI 病历助手，基于 FHIR 结构化病历和医疗知识库生成患者摘要、SOAP 草稿、随访计划，关键结论带引用溯源。
- 运营端：实现实时候诊队列、科室负载、分诊分布、风险预警大屏，支持护士人工接管高风险对话。
- 平台底座：建设模型网关、RAG 知识库、评测集、权限体系、审计日志和合成数据生成链路。

## 怎么做（How）

- 技术栈：React 19 + TypeScript + Ant Design + ECharts；Python FastAPI + SQLAlchemy；PostgreSQL + pgvector；Redis；Docker Compose；GitHub Actions。
- AI 方案：统一 OpenAI 兼容模型网关，云端 API 与本地 Ollama/vLLM 可切换；BGE 向量模型 + pgvector 混合检索；BM25 + 向量 + 重排的多路召回；多步任务使用 LangGraph 编排。
- 数据方案：采用 FHIR R4 作为数据标准，使用 Synthea 生成合成患者数据；知识库采用公开医学指南、文献切片和结构化 FAQ，构建可评测的 RAG 语料。
- 安全与工程化：RBAC 权限、审计日志、输入过滤、输出引用校验、脱敏边界；单元测试、接口测试、AI 评测集和可观测性埋点。

## 效果如何（Effect）

- 分诊结果与专家标注一致性达到 [xx%]，红黄绿分级准确率 [xx%]。
- 预问诊结构化信息采集完整度达到 [xx%]，患者到院前即完成主要问诊信息采集。
- AI 病历摘要关键信息召回率 [xx%]，引用准确率 [xx%]，医生整理病历时间预计下降 [xx%]。
- 医疗问答首字响应 [xx 秒]，完整回答 P95 延迟 [xx 秒]，关键结论均有知识库引用。
- 8 周完成 MVP，Docker 一键启动演示环境，内置 20+ 合成患者和完整评测用例。

## 简历条目（中文版）

**项目名称：AI 智慧医院平台 | 全栈 + AI 应用 | 2026.08 - 至今**

**项目简介：** 从 0 到 1 搭建覆盖患者端、医生端、运营端的 AI 智慧医院原型，用大模型 + RAG + 规则引擎实现智能预问诊、分诊、AI 病历助手与风险预警，形成从症状采集到随访的诊疗闭环。

**核心工作：**

- 主导项目从需求、设计到交付全流程，独立完成数据模型、前后端与 AI 服务开发。
- 设计患者端智能预问诊与分诊引擎：多轮结构化采集症状和病史，规则与模型双通道分级，输出风险等级、科室建议和挂号闭环。
- 搭建医生端 AI 病历助手：基于 FHIR 病历与医疗知识库 RAG 生成摘要、SOAP 草稿和随访计划，答案带引用溯源，降低医生文书负担。
- 构建运营端实时大屏：候诊队列、科室负载、分诊分布、风险预警，并支持护士人工接管。
- 建设 AI 底座与工程化体系：模型网关、pgvector 混合检索、医疗知识库、RBAC、审计日志、评测集与 CI/CD。

**项目成果：**

- 分诊准确率 [xx%]，预问诊信息完整度 [xx%]，摘要引用准确率 [xx%]。
- 首字响应 [xx 秒]，P95 完整回答延迟 [xx 秒]。
- 8 周交付可演示 MVP，支持 Docker 一键部署与私有化运行。

## 简历条目（英文版）

**Project: AI Smart Hospital Platform | Full-Stack + AI Application | Aug 2026 - Present**

**Overview:** Built an AI-driven smart hospital prototype covering patient, doctor, and operations workflows, combining LLMs, RAG, and a rule engine to form an end-to-end loop from symptom collection and triage to follow-up care.

**Key Contributions:**

- Led the full lifecycle from requirements and design to delivery; designed data models, backend services, frontend, and AI services.
- Built an intelligent pre-consultation and triage engine with structured multi-turn collection and dual-channel rule/LLM risk grading, department recommendation, and appointment booking.
- Built an AI clinical documentation copilot that generates patient summaries, SOAP drafts, and follow-up plans grounded in FHIR records and a medical knowledge base with citations.
- Built a real-time operations dashboard for queue, department load, triage distribution, and risk alerts with nurse handover.
- Built the AI platform foundation: model gateway, pgvector hybrid retrieval, medical RAG, RBAC, audit logging, evaluation harness, and CI/CD.

**Results:**

- Triage agreement with expert labels [xx%]; structured pre-consultation completeness [xx%]; citation accuracy [xx%].
- First-token latency [xx s]; P95 full response latency [xx s].
- Delivered an 8-week MVP with one-command Docker deployment and private deployment support.
