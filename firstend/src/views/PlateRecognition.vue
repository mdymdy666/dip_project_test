<template>
  <section class="ocr-stage">
    <el-dialog title="识别中" :visible.sync="dialogVisible" :show-close="false"
               :close-on-press-escape="false" :close-on-click-modal="false" :center="true">
      <el-progress :percentage="percentage"></el-progress>
      <span slot="footer">正在调用 HyperLPR3 深度学习模型</span>
    </el-dialog>

    <div class="ocr-upload-panel">
      <div class="stage-toolbar">
        <div>
          <span class="stage-kicker">PLATE RECOGNITION</span>
          <h2>车牌图片识别</h2>
        </div>
        <button class="ghost-button" type="button" @click="resetData">
          <i class="el-icon-refresh"></i><span>重新选择</span>
        </button>
      </div>
      <div class="image-frame ocr-frame" v-loading="loading" element-loading-text="识别中"
           element-loading-spinner="el-icon-loading">
        <el-image :src="drawUrl || imageUrl" class="workspace-image" :preview-src-list="previewList">
          <div slot="error" class="upload-empty">
            <button v-show="showButton" class="primary-action" type="button" @click="trueUpload">
              <i class="el-icon-upload2"></i><span>上传车辆/车牌图片</span>
            </button>
            <input ref="upload" class="hidden-input" name="file" type="file" @change="update" />
          </div>
        </el-image>
      </div>
    </div>

    <div class="identity-panel">
      <div class="identity-head">
        <div>
          <span class="stage-kicker">MATCH RESULT</span>
          <h2>车辆与车主</h2>
        </div>
        <span class="status-chip" :class="{ ready: primary && primary.plate_no }">
          {{ primary && primary.plate_no ? primary.plate_no : "等待上传" }}
        </span>
      </div>

      <div v-if="plates.length" class="plate-list">
        <button v-for="plate in plates" :key="plate.plate_no" class="plate-chip"
                type="button" @click="selectPlate(plate)">
          {{ plate.plate_no }} · {{ plate.confidence }}
        </button>
      </div>

      <div class="identity-grid">
        <div class="identity-field wide">
          <small>车牌号</small>
          <strong>{{ primary.plate_no || "--" }}</strong>
        </div>
        <div class="identity-field">
          <small>品牌</small>
          <strong>{{ vehicle.brand || "--" }}</strong>
        </div>
        <div class="identity-field">
          <small>车型</small>
          <strong>{{ vehicle.model || "--" }}</strong>
        </div>
        <div class="identity-field">
          <small>生产日期</small>
          <strong>{{ vehicle.production_date || "--" }}</strong>
        </div>
        <div class="identity-field">
          <small>当前位置</small>
          <strong>{{ vehicle.current_location || "--" }}</strong>
        </div>
        <div class="identity-field wide">
          <small>当前车主</small>
          <strong>{{ owner.name || "--" }}</strong>
        </div>
        <div class="identity-field full">
          <small>车主身份证</small>
          <strong>{{ owner.id_card || "--" }}</strong>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import axios from "axios";

export default {
  name: "PlateRecognition",
  data() {
    return {
      serverUrl: "http://127.0.0.1:5000",
      imageUrl: "",
      drawUrl: "",
      previewList: [],
      plates: [],
      primary: {},
      vehicle: {},
      owner: {},
      loading: false,
      showButton: true,
      dialogVisible: false,
      percentage: 0,
    };
  },
  methods: {
    trueUpload() {
      this.$refs.upload.click();
    },
    getObjectURL(file) {
      if (window.URL !== undefined) {
        return window.URL.createObjectURL(file);
      }
      if (window.webkitURL !== undefined) {
        return window.webkitURL.createObjectURL(file);
      }
      return "";
    },
    update(e) {
      const file = e.target.files[0];
      if (!file) return;
      this.loading = true;
      this.dialogVisible = true;
      this.showButton = false;
      this.percentage = 33;
      this.imageUrl = this.getObjectURL(file);
      this.drawUrl = "";
      this.plates = [];
      this.primary = {};
      this.vehicle = {};
      this.owner = {};

      const param = new FormData();
      param.append("file", file, file.name);
      axios.post(`${this.serverUrl}/api/plate/recognize`, param, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then((response) => {
        this.percentage = 100;
        if (response.data.status === 1) {
          this.imageUrl = response.data.image_url;
          this.drawUrl = response.data.draw_url;
          this.previewList = [this.drawUrl, this.imageUrl];
          this.plates = response.data.plates || [];
          this.selectPlate(response.data.primary || {});
          this.$notify({ title: "识别成功", message: "已完成车牌识别与车主匹配", type: "success" });
        } else {
          this.$notify({ title: "识别失败", message: response.data.error || "未识别到车牌", type: "error" });
        }
      }).finally(() => {
        this.loading = false;
        this.dialogVisible = false;
        this.percentage = 0;
      });
    },
    selectPlate(plate) {
      this.primary = plate || {};
      const lookup = this.primary.lookup || {};
      this.vehicle = lookup.vehicle || {};
      this.owner = lookup.owner || {};
    },
    resetData() {
      window.location.reload();
    },
  },
};
</script>
