<template>
  <section class="registry-page">
    <div class="registry-card">
      <div class="stage-toolbar">
        <div>
          <span class="stage-kicker">RELATIONSHIP OPS</span>
          <h2>车辆车主关系变更</h2>
        </div>
        <button class="ghost-button" type="button" @click="loadRelationships">
          <i class="el-icon-refresh"></i><span>刷新</span>
        </button>
      </div>

      <div class="relation-form">
        <el-input v-model="form.plate_no" placeholder="车牌号"></el-input>
        <el-input v-model="form.id_card" placeholder="新车主身份证号"></el-input>
        <el-input v-model="form.start_date" placeholder="开始日期 YYYY-MM-DD"></el-input>
        <el-input v-model="form.event_location" placeholder="地点"></el-input>
        <el-input v-model="form.note" placeholder="备注"></el-input>
        <button class="primary-action" type="button" @click="changeOwner">确认变更</button>
      </div>
    </div>

    <div class="registry-card">
      <div class="reference-head">
        <span class="stage-kicker">TIMELINE</span>
        <h2>关系历史</h2>
      </div>
      <el-table :data="relationships" border>
        <el-table-column prop="plate_no" label="车牌" width="130"></el-table-column>
        <el-table-column prop="name" label="车主" width="110"></el-table-column>
        <el-table-column prop="id_card" label="身份证"></el-table-column>
        <el-table-column prop="brand" label="品牌" width="110"></el-table-column>
        <el-table-column prop="model" label="车型" width="150"></el-table-column>
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
  name: "RelationshipManager",
  data() {
    return {
      serverUrl: "http://127.0.0.1:5000",
      form: {
        plate_no: "苏BD0011",
        id_card: "110101199003077512",
        start_date: "2026-06-02",
        event_location: "系统测试登记点",
        note: "动态过户测试",
      },
      relationships: [],
    };
  },
  methods: {
    loadRelationships() {
      axios.get(`${this.serverUrl}/api/relationships`).then((response) => {
        if (response.data.status === 1) {
          this.relationships = response.data.data || [];
        }
      });
    },
    changeOwner() {
      axios.post(`${this.serverUrl}/api/relationships/change-owner`, this.form)
        .then((response) => {
          if (response.data.status === 1) {
            this.$notify({ title: "变更成功", message: "车辆车主关系已更新", type: "success" });
            this.loadRelationships();
          } else {
            this.$notify({ title: "变更失败", message: response.data.error || "请检查输入", type: "error" });
          }
        });
    },
  },
  mounted() {
    this.loadRelationships();
  },
};
</script>
