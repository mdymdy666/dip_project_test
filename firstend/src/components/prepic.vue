<template>
  <section class="reference-strip">
    <div class="reference-head">
      <span class="stage-kicker">REFERENCE</span>
      <h2>样例对照</h2>
    </div>
    <div class="reference-images">
      <figure>
        <el-image :src="src0" class="reference-image"></el-image>
        <figcaption>默认图像</figcaption>
      </figure>
      <figure>
        <el-image :src="src" class="reference-image"></el-image>
        <figcaption>当前效果</figcaption>
      </figure>
    </div>
  </section>
</template>

<script>
export default {
  name: "prepic",
  props: ["id"],
  data() {
    return {
      src0: require("../../public/img/default.jpg"),
      src: require("../../public/img/" + this.$route.params.id + ".jpg"),
    };
  },
};
</script>
