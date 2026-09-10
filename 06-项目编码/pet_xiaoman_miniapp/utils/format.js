// 视图格式化工具
//
// 为什么单独抽文件：WXML 的绑定表达式**不支持函数调用**，
// 像 `{{item.time.slice(0,16)}}` 会在编译期直接报
// `Bad attr ... unexpected token`，页面白屏。
// 所以所有格式化必须在这里先算好，再通过 data 传给 WXML。

/** ISO 时间字符串 → "2026-09-10 14:30"（后端返回 `2026-09-10T14:30:00`） */
function fmtTime(v) {
  if (!v) return "";
  return String(v).slice(0, 16).replace("T", " ");
}

/** 只取日期部分 → "2026-09-10" */
function fmtDate(v) {
  if (!v) return "";
  return String(v).slice(0, 10);
}

/** 金额 → 保留两位小数的字符串（不补 ¥，符号交给 WXML） */
function fmtMoney(v) {
  const n = Number(v);
  return isNaN(n) ? "0.00" : n.toFixed(2);
}

/** 给订单对象预置好展示字段，避免 WXML 里做任何运算 */
function decorateOrder(o) {
  return Object.assign({}, o, {
    expect_text: fmtTime(o && o.expect_time),
    created_text: fmtTime(o && o.created_at),
    amount_text: fmtMoney(o && o.total_amount),
  });
}

module.exports = { fmtTime, fmtDate, fmtMoney, decorateOrder };
