<template>
  <div id="app">
    <Navbar />
    <div class="content">
      <Messages />
      <BreadcrumbBar />
      <router-view />
    </div>
    <Footer />
  </div>
</template>

<script>
  import Navbar from "$components/Navbar";
  import Messages from "$components/Messages";
  import BreadcrumbBar from "$components/BreadcrumbBar";
  import Footer from "$components/Footer";

  export default {
    name: "Landmatrix",
    components: { Navbar, Messages, BreadcrumbBar, Footer },
  };
</script>

<style lang="scss" scoped>
  .content {
    min-height: calc(100vh - 60px - 31px);
  }
</style>
