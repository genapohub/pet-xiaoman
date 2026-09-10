<template>
  <!-- 全局中文语言包
       Element Plus 默认 locale 是英文，日期面板会显示 "September / Sun Mon Tue…"，
       分页、空态、确认框等也全是英文。项目采用按需引入（没有全局 app.use(ElementPlus)），
       所以统一在这里用 el-config-provider 注入 zh-cn，一处生效、无需改各页面。 -->
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
// 注意用 /es/locale/lang/ 路径：按需引入下走 es 产物，tree-shaking 更彻底
import zhCn from "element-plus/es/locale/lang/zh-cn";
</script>
