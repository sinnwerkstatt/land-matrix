<template>
  <div>
    <a href="#" @click.prevent="displayDeals = !displayDeals">{{ value.length }}</a>
    <div v-if="displayDeals">
      <span v-for="val in value" :key="val.id">
        <br />
        <router-link :to="{ name: 'deal_detail', params: { dealId: val.id } }">
          #{{ val.id }}
        </router-link>
      </span>
    </div>
  </div>
</template>

<script>
  export default {
    props: {
      formfield: { type: Object, required: true },
      value: { type: [Array, Object], required: true },
      model: { type: String, required: true },
    },
    data() {
      return {
        displayDeals: false,
      };
    },
  };
</script>
