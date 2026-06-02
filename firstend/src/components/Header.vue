<template>
  <header class="topbar">
    <div>
      <div class="eyebrow">{{ currentGroup }}</div>
      <h1>{{ currentTitle }}</h1>
    </div>
    <div class="topbar-metrics">
      <div class="metric"><strong>49</strong><span>图像能力</span></div>
      <div class="metric"><strong>9</strong><span>风格模型</span></div>
      <div class="metric"><strong>1</strong><span>OCR 流程</span></div>
    </div>
  </header>
</template>

<script>
export default {
  name: "Header",
  props: {
    currentTitle: {
      type: String,
      default: "数字图像处理",
    },
    currentGroup: {
      type: String,
      default: "工作台",
    },
  },
};
</script>
