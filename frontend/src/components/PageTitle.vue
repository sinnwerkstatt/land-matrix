<template>
  <div v-if="title" class="container">
    <div class="row">
      <div class="col-md-12">
        <h1 v-html="title" />
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    props: {
      title: { type: String, default: "" },
    },
  };
</script>

<style lang="scss" scoped>
  h1 {
    font-size: 48px;
    font-weight: normal !important;
    color: black;
    text-align: left;
    text-transform: none;

    &:before {
      content: none;
    }
    span.small {
      font-size: 1rem;
    }
  }
</style>
