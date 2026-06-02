<template>
  <section class="registry-page">
    <div class="registry-card">
      <div class="stage-toolbar">
        <div>
          <span class="stage-kicker">OWNER TO VEHICLE</span>
          <h2>身份证号查车辆</h2>
        </div>
      </div>
      <div class="query-row">
        <el-input v-model="idCard" placeholder="例如：44030119840217411X"></el-input>
        <button class="primary-action" type="button" @click="lookup">查询</button>
      </div>
    </div>

    <div class="identity-panel">
      <div class="identity-head">
        <div>
          <span class="stage-kicker">OWNER PROFILE</span>
          <h2>人员信息</h2>
        </div>
      </div>
      <div class="identity-grid">
        <div class="identity-field wide"><small>姓名</small><strong>{{ owner.name || "--" }}</strong></div>
        <div class="identity-field"><small>性别</small><strong>{{ owner.gender || "--" }}</strong></div>
        <div class="identity-field"><small>民族</small><strong>{{ owner.ethnicity || "--" }}</strong></div>
        <div class="identity-field full"><small>身份证号</small><strong>{{ owner.id_card || "--" }}</strong></div>
        <div class="identity-field full address"><small>地址</small><strong>{{ owner.address || "--" }}</strong></div>
      </div>
    </div>

    <div class="registry-card">
      <div class="reference-head">
        <span class="stage-kicker">VEHICLES</span>
        <h2>车辆记录</h2>
      </div>
      <el-table :data="vehicles" border>
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

export default {
  name: "OwnerLookup",
  data() {
    return {
      serverUrl: "http://127.0.0.1:5000",
      idCard: "44030119840217411X",
      owner: {},
      vehicles: [],
    };
  },
  methods: {
    lookup() {
      axios.get(`${this.serverUrl}/api/owner/by-id-card`, {
        params: { id_card: this.idCard },
      }).then((response) => {
        if (response.data.status === 1) {
          const data = response.data.data || {};
          this.owner = data.owner || {};
          this.vehicles = data.vehicles || [];
        }
      });
    },
  },
  mounted() {
    this.lookup();
  },
};
</script>
