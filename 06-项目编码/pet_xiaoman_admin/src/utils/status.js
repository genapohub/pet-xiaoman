// 状态语义 → 颜色/文案映射。集中一处，避免同个订单状态在不同页面颜色不一致

/** Element Plus tag type。未知状态统一灰色，不要悄悄变成绿色误导员工 */
export const ORDER_STATUS = {
  待确认: "warning",
  已预约: "primary",
  接宠中: "primary",
  服务中: "primary",
  待交付: "warning",
  已完成: "info",
  已取消: "danger",
};

export const VISIT_STATUS = {
  待回访: "warning",
  已回访: "success",
  无需回访: "info",
};

export const SALE_STATUS = {
  在售: "success",
  下架: "info",
};

export const BOARDING_SEVERITY = {
  正常: "success",
  临期: "warning",
  已到期: "danger",
};

/** 订单状态 → 下一步该做什么（详情右侧操作区排序依据） */
export const NEXT_ACTION = {
  待确认: "确认订单",
  已预约: "出发接宠",
  接宠中: "开始服务",
  服务中: "标记待交付",
  待交付: "交付并结清",
  已完成: "—",
  已取消: "—",
};

export const ORDER_STATUS_LIST = Object.keys(ORDER_STATUS);
