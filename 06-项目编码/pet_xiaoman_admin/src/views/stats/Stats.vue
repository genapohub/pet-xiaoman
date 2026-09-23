<!-- B-数据看板 Stats（对齐画布 2:1487）
     版式：note 横幅 + 页头(标题/副标题/近 30 天) + KPI 四卡 + 趋势柱(近30天新增门店) + 门店活跃榜。
     数据：本屏为平台超管示意看板，画布已标注「指标均为示意，非真实接口 / 后端待对齐」，
           故用本地 mock 渲染，不调用尚未就绪的 /stats 聚合接口（避免编造空壳数据）。 -->
<template>
  <div class="sup">
    <!-- 画布 note-noroute 横幅 -->
    <div class="note">
      超管数据看板（/stats）已纳入左侧菜单，与门店管理并列；本屏指标均为示意，非真实接口。【后端待对齐】需将 stats 加入超管 menus 才能真实访问。
    </div>

    <PxPageHeader title="平台门店概览" subtitle="超管视角 · 门店经营汇总（示意）">
      <template #actions>
        <span class="range">近 30 天</span>
      </template>
    </PxPageHeader>

    <!-- KPI 四卡：总门店数 5 / 营业中门店 4 / 独立小程序 1(松绿) / 待补店长 2 -->
    <div class="kpis">
      <div v-for="k in kpis" :key="k.label" class="kpi">
        <div class="kpi__label">{{ k.label }}</div>
        <div class="kpi__value" :class="k.accent ? `is-${k.accent}` : ''">{{ k.value }}</div>
      </div>
    </div>

    <!-- 趋势柱：近 30 天新增门店，末根高亮为陶土橙 -->
    <section class="card trend">
      <h3 class="card__title">近 30 天新增门店</h3>
      <div class="bars">
        <div
          v-for="(h, i) in trend"
          :key="i"
          class="bar"
          :class="{ 'is-accent': i === trend.length - 1 }"
          :style="{ height: h + 'px' }"
        />
      </div>
    </section>

    <!-- 门店活跃榜：本月，圆形序号（第一松绿，其余陶土橙） -->
    <section class="card rank">
      <header class="rank__head">
        <h3 class="card__title">门店活跃榜</h3>
        <span class="rank__sub">本月</span>
      </header>
      <div
        v-for="(r, i) in ranks"
        :key="r.name"
        class="rank__row"
        :class="{ 'is-last': i === ranks.length - 1 }"
      >
        <span class="rank__no" :class="{ 'is-top': i === 0 }">{{ i + 1 }}</span>
        <span class="rank__name">{{ r.name }}</span>
        <span class="rank__val">¥{{ r.value }}</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import PxPageHeader from "../../components/PxPageHeader.vue";

// 画布示意数据（非真实接口）
const kpis = [
  { label: "总门店数", value: "5", accent: "" },
  { label: "营业中门店", value: "4", accent: "" },
  { label: "独立小程序", value: "1", accent: "primary" },
  { label: "待补店长", value: "2", accent: "" },
];

const trend = [42, 58, 50, 72, 64, 82, 74, 92, 86, 104];

const ranks = [
  { name: "宠小满 · 金水店", value: "42,800" },
  { name: "宠小满 · 二七店", value: "38,200" },
  { name: "宠小满 · 中原店", value: "31,500" },
  { name: "宠小满 · 高新店", value: "27,900" },
];
</script>

<style scoped>
.sup { display: flex; flex-direction: column; gap: var(--px-sp-4); }

.note {
  font-size: var(--px-fs-xs);
  line-height: 1.6;
  color: var(--px-primary-pressed);
  background: var(--px-primary-light);
  border: 1px solid var(--px-primary-weak);
  border-radius: 10px;
  padding: 9px 12px;
}
.range {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: 999px;
}

/* KPI 四卡 */
.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--px-sp-3);
}
.kpi {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 88px;
  padding: 16px;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: 14px;
  box-shadow: var(--px-shadow-card-soft);
}
.kpi__label { font-size: var(--px-fs-sm); color: var(--px-text-2); }
.kpi__value {
  font-family: var(--px-font-num);
  font-size: 22px;
  font-weight: 600;
  line-height: 1.1;
  color: var(--px-text-1);
  font-variant-numeric: tabular-nums;
}
.kpi__value.is-primary { color: var(--px-primary); }
.kpi__value.is-warning { color: var(--px-chart-2); }

/* 通用卡片 */
.card {
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: 14px;
  box-shadow: var(--px-shadow-card-soft);
}
.card__title {
  margin: 0;
  font-family: var(--px-font-serif);
  font-size: 15px;
  font-weight: 600;
  color: var(--px-text-1);
}

/* 趋势柱 */
.trend { padding: 20px; }
.trend .bars {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 120px;
  margin-top: 16px;
}
.bar {
  width: 28px;
  background: var(--px-primary);
}
.bar.is-accent { background: var(--px-chart-2); }

/* 门店活跃榜 */
.rank { padding: 0; overflow: hidden; }
.rank__head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 16px 20px;
}
.rank__sub { font-size: var(--px-fs-xs); color: var(--px-text-3); }
.rank__row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-top: 1px solid var(--px-border);
}
.rank__row.is-last { border-top: none; }
.rank__no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  font-family: var(--px-font-num);
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: var(--px-chart-2);
  flex-shrink: 0;
}
.rank__no.is-top { background: var(--px-primary); }
.rank__name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--px-text-1);
}
.rank__val {
  font-family: var(--px-font-num);
  font-size: 14px;
  font-weight: 600;
  color: var(--px-primary);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1366px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
