// 展示层格式化：以前这 5 行逻辑散落在 5 个页面里各写一遍，改格式要全局替换
const pad = (n) => String(n).padStart(2, "0");

/** ISO 字符串 → "2026-09-10 11:35"，非法值返回 "-" 而不是 NaN */
export function fmtDateTime(s) {
  if (!s) return "-";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return "-";
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** 看板用："09-10 11:35"（省年份） */
export function fmtShort(s) {
  const full = fmtDateTime(s);
  return full === "-" ? "-" : full.slice(5);
}

/** 金额：千分位 + 两位小数，空值兜底 0.00 */
export function fmtMoney(n) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** 距今天的天数：寄存到期用（负数=已到期） */
export function daysLeft(dateStr) {
  if (!dateStr) return null;
  const target = new Date(`${dateStr}T00:00:00`);
  return Math.round((target - new Date().setHours(0, 0, 0, 0)) / 86400000);
}

/** 今日日期 "YYYY-MM-DD"：日期筛选项 / 日期控件默认值用（刻意不走 toISOString，避免 UTC 时区把日期算到前一天） */
export function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
