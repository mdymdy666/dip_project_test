<template>
  <section class="tool-stage">
    <el-dialog
      title="处理中"
      :visible.sync="dialogTableVisible"
      :show-close="false"
      :close-on-press-escape="false"
      :append-to-body="true"
      :close-on-click-modal="false"
      :center="true">
      <el-progress :percentage="percentage"></el-progress>
      <span slot="footer">请耐心等待</span>
    </el-dialog>

    <div class="stage-toolbar">
      <div>
        <span class="stage-kicker">IMAGE PIPELINE</span>
        <h2>{{ toolTitle }}</h2>
      </div>
      <button class="ghost-button" type="button" @click="resetData">
        <i class="el-icon-refresh"></i>
        <span>重新选择</span>
      </button>
    </div>

    <div class="image-comparison">
      <div class="image-panel source-panel">
        <div class="panel-head">
          <span>输入图像</span>
          <small>source</small>
        </div>
        <div
          class="image-frame"
          v-loading="loading"
          element-loading-text="上传图片中"
          element-loading-spinner="el-icon-loading">
          <el-image :src="url_1" class="workspace-image" :preview-src-list="srcList">
            <div slot="error" class="upload-empty">
              <button v-show="showbutton" class="primary-action" type="button" @click="true_upload">
                <i class="el-icon-upload2"></i>
                <span>上传图像</span>
              </button>
              <input ref="upload" class="hidden-input" name="file" type="file" @change="update" />
            </div>
          </el-image>
        </div>
      </div>

      <div class="flow-indicator">
        <i class="el-icon-right"></i>
      </div>

      <div class="image-panel result-panel">
        <div class="panel-head">
          <span>处理结果</span>
          <small>result</small>
        </div>
        <div
          class="image-frame"
          v-loading="loading"
          element-loading-text="处理中"
          element-loading-spinner="el-icon-loading">
          <el-image :src="url_2" class="workspace-image" :preview-src-list="srcList1">
            <div slot="error" class="result-empty">{{ wait_return }}</div>
          </el-image>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import axios from "axios";

const toolNames = {
  0: "添加椒盐噪声", 1: "均值平滑", 2: "中值平滑", 3: "高斯平滑",
  4: "拉普拉斯锐化", 5: "Sobel 水平方向", 6: "Sobel 垂直方向",
  7: "双线性插值放大", 8: "图像平移", 9: "旋转与缩放",
  10: "灰度图", 11: "全局阈值二值化", 12: "直方图均衡化",
  13: "灰度直方图", 14: "仿射变换", 15: "透视变换",
  16: "图像反色", 17: "RGB 转 HSV", 18: "HSV 通道 H",
  19: "HSV 通道 S", 20: "HSV 通道 V", 21: "RGB 通道 B",
  22: "RGB 通道 G", 23: "RGB 通道 R", 24: "水平翻转",
  25: "垂直翻转", 26: "对角镜像", 27: "开运算",
  28: "闭运算", 29: "腐蚀", 30: "膨胀", 31: "顶帽运算",
  32: "底帽运算", 33: "HoughLinesP 线检测", 34: "Canny 边缘检测",
  35: "图像增强", 36: "Roberts 边缘", 37: "Prewitt 边缘",
  38: "Laplacian 边缘", 39: "LoG 边缘", 51: "糖果风格",
  52: "星空风格", 53: "毕加索风格", 54: "缪斯风格",
  55: "马赛克风格", 56: "神奈川冲浪里", 57: "达达主义",
  58: "呐喊风格", 59: "羽毛风格",
};

export default {
  name: "Upload2Show",
  props: ["id"],
  data() {
    return {
      server_url: "http://127.0.0.1:5000",
      url_1: "",
      url_2: "",
      srcList: [],
      srcList1: [],
      url: "",
      visible: false,
      wait_return: "等待上传",
      wait_upload: "等待上传",
      loading: false,
      showbutton: true,
      percentage: 0,
      fullscreenLoading: false,
      dialogTableVisible: false,
    };
  },
  computed: {
    toolTitle() {
      return toolNames[this.$route.params.id] || "图像处理";
    },
  },
  created: function () {
    this.$watch("$route.params.id", () => {
      this.resetData();
    });
    document.title = "QTProj_WEB";
  },
  methods: {
    true_upload() {
      this.$refs.upload.click();
    },
    true_upload2() {
      this.$refs.upload2.click();
    },
    getObjectURL(file) {
      var url = null;
      if (window.createObjcectURL !== undefined) {
        url = window.createOjcectURL(file);
      } else if (window.URL !== undefined) {
        url = window.URL.createObjectURL(file);
      } else if (window.webkitURL !== undefined) {
        url = window.webkitURL.createObjectURL(file);
      }
      return url;
    },
    update(e) {
      this.percentage = 0;
      this.dialogTableVisible = true;
      this.url_1 = "";
      this.url_2 = "";
      this.srcList = [];
      this.srcList1 = [];
      this.wait_return = "";
      this.wait_upload = "";
      this.fullscreenLoading = true;
      this.loading = true;
      this.showbutton = false;
      let file = e.target.files[0];
      this.url_1 = this.$options.methods.getObjectURL(file);
      let param = new FormData();
      param.append("file", file, file.name);
      var timer = setInterval(() => {
        this.myFunc();
      }, 30);
      let config = {
        headers: { "Content-Type": "multipart/form-data" },
      };
      axios.post(this.server_url + `/upload/${this.$route.params.id}`, param, config)
        .then((response) => {
          this.percentage = 100;
          clearInterval(timer);
          this.url_1 = response.data.image_url;
          this.srcList.push(this.url_1);
          this.url_2 = response.data.draw_url;
          this.srcList1.push(this.url_2);
          this.fullscreenLoading = false;
          this.loading = false;
          this.dialogTableVisible = false;
          this.percentage = 0;
          this.notice1();
        });
    },
    myFunc() {
      if (this.percentage + 33 < 99) {
        this.percentage = this.percentage + 33;
      } else {
        this.percentage = 99;
      }
    },
    drawChart() {},
    notice1() {
      this.$notify({
        title: "处理成功",
        message: "点击图片可以查看大图",
        duration: 0,
        type: "success",
      });
    },
    resetData() {
      window.location.reload();
    },
  },
  mounted() {
    this.drawChart();
  },
};
</script>
