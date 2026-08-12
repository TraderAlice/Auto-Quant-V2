const A_SHARE_CALENDARS = new Set(["XSHG", "XSHE"]);
const A_SHARE_VENUES = new Set(["SSE", "SZSE", "XSHG", "XSHE"]);

const PROFILES = {
  "a-share-equity": {
    label: "A 股股票研究",
    adapters: ["A 股公告", "财经新闻"],
    replay: ["交易日与盘中时段", "公告前 5 个交易日 → 后 20 个交易日", "盘前、盘中、盘后分别对齐可见性"],
    diagnostics: ["Rank IC / ICIR", "行业与规模中性后收益", "停牌、ST、涨跌停与换手成本", "公告修订与延迟敏感性"],
    guardrails: [
      "交易日历、时区与盘中/盘后可见性必须明确",
      "复权、停牌、ST、涨跌停与 T+1 可交易性必须进入样本",
      "行业/规模暴露、幸存者偏差、成本与流动性必须诊断",
    ],
  },
  "session-equity": {
    label: "交易时段股票研究",
    adapters: ["公司事件", "财经新闻"],
    replay: ["交易所日历与本地时区", "事件前 5 个交易日 → 后 20 个交易日", "盘前、盘中、盘后分别对齐可见性"],
    diagnostics: ["Rank IC / ICIR", "行业与规模暴露", "公司行动与可交易性", "成本、流动性与借券约束"],
    guardrails: [
      "交易日历、时区、复权与公司行动必须明确",
      "可交易性、卖空/借券、成本、流动性与基准必须声明",
      "事件窗使用交易时间，不能用自然时间替代",
    ],
  },
  crypto: {
    label: "加密资产研究",
    adapters: ["加密事件", "财经新闻"],
    replay: ["24/7 UTC 连续时间", "事件前 24 小时 → 后 72 小时", "链上确认、交易所状态与资金费率同轴"],
    diagnostics: ["跨场所收益与流动性", "资金费率 / 基差", "交易所中断与链上最终性", "费率、滑点与成交量语义"],
    guardrails: [
      "场所、现货/永续合约、计价币和标记/指数价格必须明确",
      "24/7 UTC、资金费率、链上最终性与交易所中断必须进入时间模型",
      "跨场所流动性、费率、滑点和成交量语义必须诊断",
    ],
  },
  mixed: {
    label: "混合资产研究",
    adapters: ["按标的映射的事件源"],
    replay: ["逐标的保留原始市场时钟", "先归一化再定义跨市场窗口", "不使用统一自然日填平休市段"],
    diagnostics: ["逐标的类别与场所", "时钟 / 币种 / 收益归一化", "缺失市场策略", "跨资产可比性"],
    guardrails: [
      "每个标的必须保留自己的经济类别、时钟、场所和币种",
      "跨市场收益、成交量、汇率和缺失时段必须显式归一化",
      "不能用统一自然日静默填平不同市场日历",
    ],
  },
  unresolved: {
    label: "未解析标的研究",
    adapters: ["仅验证过的已映射证据"],
    replay: ["等待 Core 声明市场时钟", "不生成事件窗", "仅验证数据契约与页面流程"],
    diagnostics: ["数据契约完整性", "未解析字段", "来源与许可", "不声明市场结论"],
    guardrails: [
      "仅验证工作流与数据契约，不声明市场特定结论",
      "补齐市场时钟、场所、频率和价格/成交量语义后再运行正式实验",
    ],
  },
};

function values(record) {
  return record && typeof record === "object" ? Object.values(record) : [];
}

function researchProfile(dataset, context) {
  const classes = new Set([dataset?.asset_class, ...values(context?.assetClasses)].filter(Boolean).map((item) => String(item).toLowerCase()));
  const calendar = context?.market?.calendar;
  const venues = new Set(context?.venues || []);
  const isCrypto = [...classes].some((item) => item.includes("crypto") || item.includes("digital"))
    || context?.market?.clock === "continuous";
  const isEquity = [...classes].some((item) => item.includes("equity") || item.includes("stock"));
  const isAShare = isEquity && (A_SHARE_CALENDARS.has(calendar) || [...venues].some((item) => A_SHARE_VENUES.has(item)));
  if (isAShare) return "a-share-equity";
  if (isCrypto) return "crypto";
  if (classes.size > 1 || [...classes].some((item) => item.includes("mixed") || item.includes("multi-asset"))) return "mixed";
  if (isEquity) return "session-equity";
  return "unresolved";
}

export function researchSubjectFromProject(project) {
  const studies = project?.studies?.filter((item) => item?.dataset) || [];
  const study = studies.find((item) => item.subjectKind === "factor") || studies[0];
  if (!study) return null;
  const dataset = study.dataset;
  const context = study.datasetContext || {};
  const profileId = researchProfile(dataset, context);
  const profile = PROFILES[profileId];
  const market = context.market || {};
  const interval = context.baseInterval || context.frequency || null;
  const unresolved = [
    ["经济类别", dataset.asset_class || context.assetClass],
    ["标的池", dataset.universe?.length],
    ["市场时钟", market.clock],
    ["交易日历", market.calendar],
    ["时区", market.timezone],
    ["基础频率", interval],
    ["场所", context.venues?.length],
  ].filter(([, value]) => !value).map(([label]) => label);
  return {
    id: `${dataset.id}@${dataset.version}`,
    profileId,
    label: profile.label,
    assetClass: dataset.asset_class || context.assetClass || "unresolved",
    universe: dataset.universe || [],
    timeRange: dataset.time_range || null,
    market,
    interval,
    featureIntervals: context.featureIntervals || [],
    venues: context.venues || [],
    currencies: context.currencies || [],
    priceAdjustment: context.priceAdjustment || null,
    adapters: profile.adapters,
    replay: profile.replay,
    diagnostics: profile.diagnostics,
    guardrails: profile.guardrails,
    unresolved,
    sourceStudyId: study.id,
    datasetHash: study.datasetHash || null,
  };
}
