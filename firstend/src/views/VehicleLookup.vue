<template>
  <section class="registry-page">
    <div class="registry-card">
      <div class="stage-toolbar">
        <div>
          <span class="stage-kicker">PLATE TO OWNER</span>
          <h2>车牌号查车主</h2>
        </div>
      </div>
      <div class="query-row">
        <el-input v-model="plateNo" placeholder="例如：苏BD0011 / 粤Z5A55港"></el-input>
        <button class="primary-action" type="button" @click="lookup">查询</button>
      </div>
    </div>

    <div class="identity-panel">
      <div class="identity-head">
        <div>
          <span class="stage-kicker">CURRENT MATCH</span>
          <h2>车辆与当前车主</h2>
        </div>
      </div>
      <div class="identity-grid">
        <div class="identity-field wide"><small>品牌车型</small><strong>{{ vehicleText }}</strong></div>
        <div class="identity-field"><small>生产日期</small><strong>{{ vehicle.production_date || "--" }}</strong></div>
        <div class="identity-field"><small>当前位置</small><strong>{{ vehicle.current_location || "--" }}</strong></div>
        <div class="identity-field wide"><small>当前车主</small><strong>{{ owner.name || "--" }}</strong></div>
        <div class="identity-field full"><small>身份证号</small><strong>{{ owner.id_card || "--" }}</strong></div>
      </div>
    </div>

    <div class="registry-card">
      <div class="reference-head">
        <span class="stage-kicker">HISTORY</span>
        <h2>车主历史追溯</h2>
      </div>
      <el-table :data="history" border>
        <el-table-column prop="plate_no" label="车牌" width="130"></el-table-column>
        <el-table-column prop="name" label="车主" width="120"></el-table-column>
        <el-table-column prop="id_card" label="身份证"></el-table-column>
        <el-table-column prop="start_date" label="开始" width="120"></el-table-column>
        <el-table-column prop="end_date" label="结束" width="120"></el-table-column>
        <el-table-column prop="event_location" label="地点"></el-table-column>
        <el-table-column prop="note" label="备注"></el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script>
import axios from "axios";

export default {
  name: "VehicleLookup",
  data() {
    return {
      serverUrl: "http://127.0.0.1:5000",
      plateNo: "苏BD0011",
      vehicle: {},
      owner: {},
      history: [],
    };
  },
  computed: {
    vehicleText() {
      if (!this.vehicle.brand) return "--";
      return `${this.vehicle.brand} ${this.vehicle.model || ""}`;
    },
  },
  methods: {
    lookup() {
      axios.get(`${this.serverUrl}/api/vehicle/by-plate`, {
        params: { plate_no: this.plateNo },
      }).then((response) => {
        if (response.data.status === 1) {
          const data = response.data.data || {};
          this.vehicle = data.vehicle || {};
          this.owner = data.owner || {};
          this.history = data.history || [];
        }
      });
    },
  },
  mounted() {
    this.lookup();
  },
};
</script>
