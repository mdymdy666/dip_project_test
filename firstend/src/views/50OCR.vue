<template>
  <section class="ocr-stage">
    <el-dialog
      title="识别中"
      :visible.sync="dialogTableVisible"
      :show-close="false"
      :close-on-press-escape="false"
      :append-to-body="true"
      :close-on-click-modal="false"
      :center="true">
      <el-progress :percentage="percentage"></el-progress>
      <span slot="footer">请耐心等待</span>
    </el-dialog>

    <div class="ocr-upload-panel">
      <div class="stage-toolbar">
        <div>
          <span class="stage-kicker">OCR CARD READER</span>
          <h2>身份证信息检测</h2>
        </div>
        <button class="ghost-button" type="button" @click="resetData">
          <i class="el-icon-refresh"></i>
          <span>重新选择</span>
        </button>
      </div>

      <div
        class="image-frame ocr-frame"
        v-loading="loading"
        element-loading-text="上传图片中"
        element-loading-spinner="el-icon-loading">
        <el-image :src="url_1" class="workspace-image" :preview-src-list="srcList">
          <div slot="error" class="upload-empty">
            <button v-show="showbutton" class="primary-action" type="button" @click="true_upload">
              <i class="el-icon-upload2"></i>
              <span>上传身份证图像</span>
            </button>
            <input ref="upload" class="hidden-input" name="file" type="file" @change="update" />
          </div>
        </el-image>
      </div>
    </div>

    <div class="identity-panel">
      <div class="identity-head">
        <div>
          <span class="stage-kicker">IDENTITY PROFILE</span>
          <h2>识别结果</h2>
        </div>
        <span class="status-chip" :class="{ ready: ocrText && ocrText.CARD_NUM }">
          {{ ocrText && ocrText.CARD_NUM ? "已识别" : "等待上传" }}
        </span>
      </div>

      <div class="identity-grid">
        <div class="identity-field wide">
          <small>姓名</small>
          <strong>{{ ocrText.CARD_NAME || "--" }}</strong>
        </div>
        <div class="identity-field">
          <small>性别</small>
          <strong>{{ ocrText.CARD_GENDER || "--" }}</strong>
        </div>
        <div class="identity-field">
          <small>民族</small>
          <strong>{{ ocrText.CARD_ETHNIC || "--" }}</strong>
        </div>
        <div class="identity-field wide">
          <small>出生日期</small>
          <strong>{{ birthText }}</strong>
        </div>
        <div class="identity-field full">
          <small>身份证号</small>
          <strong>{{ ocrText.CARD_NUM || "--" }}</strong>
        </div>
        <div class="identity-field full address">
          <small>地址</small>
          <strong>{{ ocrText.CARD_ADDR || "--" }}</strong>
        </div>
      </div>
    </div>

    <div class="registry-card linked-vehicles">
      <div class="reference-head">
        <span class="stage-kicker">LINKED VEHICLES</span>
        <h2>身份证关联车辆</h2>
      </div>
      <el-table :data="linkedVehicles" border>
        <el-table-column prop="plate_no" label="车牌" width="130"></el-table-column>
        <el-table-column prop="brand" label="品牌" width="120"></el-table-column>
        <el-table-column prop="model" label="车型"></el-table-column>
        <el-table-column prop="production_date" label="生产日期" width="120"></el-table-column>
        <el-table-column prop="current_location" label="当前位置"></el-table-column>
        <el-table-column prop="start_date" label="持有开始" width="120"></el-table-column>
        <el-table-column prop="end_date" label="持有结束" width="120"></el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script>
import axios from "axios";
import prepic from "@/components/prepic.vue";

export default {
  name: "ocr",
  components: {
    prepic: prepic,
  },
  data() {
    return {
      server_url: "http://127.0.0.1:5000",
      url_1: "",
      srcList: [],
      url: "",
      visible: false,
      wait_return: "等待上传",
      wait_upload: "等待上传",
      loading: false,
      showbutton: true,
      percentage: 0,
      fullscreenLoading: false,
      dialogTableVisible: false,
      ocrText: {},
      linkedVehicles: [],
    };
  },
  computed: {
    birthText() {
      if (!this.ocrText.CARD_YEAR) {
        return "--";
      }
      return `${this.ocrText.CARD_YEAR}年${this.ocrText.CARD_MON}月${this.ocrText.CARD_DAY}日`;
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
      this.srcList = [];
      this.wait_return = "";
      this.wait_upload = "";
      this.fullscreenLoading = true;
      this.loading = true;
      this.showbutton = false;
      this.ocrText = {};
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
      axios.post(this.server_url + `/upload/50`, param, config)
        .then((response) => {
          this.percentage = 100;
          clearInterval(timer);
          if (response.data.status === 1) {
            this.url_1 = response.data.image_url;
            this.srcList.push(this.url_1);
            this.ocrText = response.data.ocr_text;
            this.lookupVehiclesById(this.ocrText.CARD_NUM);
            this.fullscreenLoading = false;
            this.loading = false;
            this.dialogTableVisible = false;
            this.percentage = 0;
            this.notice1();
          } else {
            this.fullscreenLoading = false;
            this.loading = false;
            this.dialogTableVisible = false;
            this.percentage = 0;
            this.$notify({
              title: "处理失败",
              message: response.data.error || "OCR识别失败，请上传有效的身份证图片",
              duration: 0,
              type: "error",
            });
          }
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
    lookupVehiclesById(idCard) {
      if (!idCard) return;
      axios.get(this.server_url + `/api/owner/by-id-card`, {
        params: { id_card: idCard },
      }).then((response) => {
        if (response.data.status === 1) {
          this.linkedVehicles = (response.data.data && response.data.data.vehicles) || [];
        }
      });
    },
  },
  mounted() {
    this.drawChart();
  },
};
</script>
