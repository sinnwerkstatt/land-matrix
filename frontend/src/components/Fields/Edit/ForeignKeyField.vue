<template>
  <div>
    <select v-model="val" class="form-control">
      <option v-for="choice in choices" :key="choice.id" :value="choice.id">
        {{ choice.name }}
      </option>
    </select>
  </div>
</template>

<script>
  import gql from "graphql-tag";

  export default {
    props: {
      formfield: { type: Object, required: true },
      value: { type: Object, required: false, default: null },
      model: { type: String, required: true },
    },
    data() {
      return {
        currencies: [],
      };
    },
    apollo: {
      currencies: gql`
        query {
          currencies {
            id
            name
          }
        }
      `,
    },
    computed: {
      val: {
        get() {
          return this.value ? this.value.id : null;
        },
        set(v) {
          let choice = this.choices.find((c) => c.id === v);
          this.$emit("input", { id: choice.id, name: choice.name });
        },
      },

      choices() {
        let options = {
          Country: this.$store.state.page.countries,
          Currency: this.currencies,
        };
        return options[this.formfield.related_model];
      },
    },
  };
</script>
