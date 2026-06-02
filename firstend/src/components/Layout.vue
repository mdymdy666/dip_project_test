<template>
  <div class="studio-shell">
    <aside class="studio-nav">
      <div class="brand-block">
        <div class="brand-mark">QT</div>
        <div>
          <div class="brand-title">QTProj</div>
          <div class="brand-subtitle">Digital Image Lab</div>
        </div>
      </div>

      <router-link class="nav-hero" to="/upload/50">
        <i class="el-icon-document"></i>
        <span>OCR 身份证识别</span>
      </router-link>

      <section v-for="group in groups" :key="group.title" class="nav-section">
        <div class="nav-section-title">{{ group.title }}</div>
        <router-link
          v-for="item in group.items"
          :key="item.path"
          :to="item.path"
          class="nav-pill"
          :class="{ active: $route.path === item.path }"
        >
          <span class="nav-index">{{ item.id }}</span>
          <span class="nav-label">{{ item.name }}</span>
        </router-link>
      </section>
    </aside>

    <main class="studio-main">
      <app-header :current-title="currentTitle" :current-group="currentGroup" />
      <div class="workspace-band">
        <router-view name="default" />
        <router-view name="footer" />
      </div>
    </main>
  </div>
</template>

<script>
import Header from "./Header.vue";

const styleItems = [
  [51, "糖果"], [52, "星空"], [53, "毕加索"], [54, "缪斯"],
  [55, "马赛克"], [56, "神奈川冲浪里"], [57, "达达主义"],
  [58, "呐喊"], [59, "羽毛"],
];

const baseItems = [
  [0, "椒盐噪声"], [1, "均值平滑"], [2, "中值平滑"], [3, "高斯平滑"],
  [4, "拉普拉斯锐化"], [5, "Sobel 水平"], [6, "Sobel 垂直"],
  [7, "双线性放大"], [8, "平移"], [9, "旋转缩放"],
  [10, "灰度图"], [11, "全局阈值"], [12, "直方图均衡"],
  [13, "灰度直方图"], [14, "仿射变换"], [15, "透视变换"],
  [16, "反色翻转"], [17, "RGB 转 HSV"], [18, "HSV-H"],
  [19, "HSV-S"], [20, "HSV-V"], [21, "RGB-B"], [22, "RGB-G"],
  [23, "RGB-R"], [24, "水平翻转"], [25, "垂直翻转"],
  [26, "对角镜像"], [27, "开运算"], [28, "闭运算"],
  [29, "腐蚀"], [30, "膨胀"], [31, "顶帽运算"], [32, "底帽运算"],
  [33, "Hough 线检测"], [34, "Canny 边缘"], [35, "图像增强"],
  [36, "Roberts 边缘"], [37, "Prewitt 边缘"], [38, "Laplacian 边缘"],
  [39, "LoG 边缘"],
];

const vehicleItems = [
  { id: "P1", name: "车牌识别", path: "/plate/recognize" },
  { id: "P2", name: "车牌找车主", path: "/vehicle/search" },
  { id: "P3", name: "身份证找车辆", path: "/owner/search" },
  { id: "P4", name: "关系变更", path: "/relations" },
];

function mapItem(item) {
  return { id: item[0], name: item[1], path: `/upload/${item[0]}` };
}

export default {
  name: "Layout",
  components: {
    "app-header": Header,
  },
  data() {
    return {
      groups: [
        { title: "车辆档案", items: vehicleItems },
        { title: "风格迁移", items: styleItems.map(mapItem) },
        { title: "基础处理", items: baseItems.map(mapItem) },
      ],
    };
  },
  computed: {
    currentItem() {
      if (this.$route.path === "/upload/50") {
        return { name: "OCR 身份证识别", group: "文字识别" };
      }
      for (const group of this.groups) {
        const match = group.items.find((item) => item.path === this.$route.path);
        if (match) {
          return { name: match.name, group: group.title };
        }
      }
      return { name: "数字图像处理", group: "工作台" };
    },
    currentTitle() {
      return this.currentItem.name;
    },
    currentGroup() {
      return this.currentItem.group;
    },
  },
};
</script>
