<template>
  <div class="nowrap">
    <table class="w-100">
      <thead>
        <tr>
          <th>Current</th>
          <th>Date</th>
          <th>Jobs</th>
          <th>Employees</th>
          <th>Workers</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(val, i) in vals" :key="i" :class="{ 'is-current': val.current }">
          <td class="text-center" @click="updateCurrent(i)">
            <div class="form-check form-check-inline">
              <input
                :id="`${formfield.name}_current_${i}`"
                v-model="current"
                class="form-check-input"
                type="radio"
                :value="i"
              />
            </div>
          </td>
          <td>
            <LowLevelDateYearField
              v-model="val.date"
              :required="formfield.required"
              @input="updateEntries"
            />
          </td>
          <td>
            <input
              v-model="val.jobs"
              type="number"
              class="form-control"
              :required="formfield.required"
              @input="updateEntries"
            />
          </td>
          <td>
            <input
              v-model="val.employees"
              type="number"
              class="form-control"
              :required="formfield.required"
              @input="updateEntries"
            />
          </td>
          <td>
            <input
              v-model="val.workers"
              type="number"
              class="form-control"
              :required="formfield.required"
              @input="updateEntries"
            />
          </td>

          <td>
            <a class="btn" @click.stop="addEntry"><i class="fa fa-plus"></i></a>
            <a
              :class="{ disabled: vals.length <= 1 }"
              class="btn"
              @click.stop="removeEntry(i)"
            >
              <i class="fa fa-minus"></i
            ></a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
  import JSONFieldMixin from "../JSONFieldMixin";
  import LowLevelDateYearField from "./LowLevelDateYearField";

  export default {
    components: { LowLevelDateYearField },
    mixins: [JSONFieldMixin],
    computed: {
      filteredVals() {
        return this.vals.filter((x) => x.date || x.jobs || x.employees || x.workers);
      },
    },
  };
</script>

<style lang="scss" scoped>
  @import "../../../scss/colors";

  th {
    text-align: center;
  }
  td {
    padding: 0.4em;
  }

  .is-current {
    font-weight: bold;
    background: rgba($primary, 0.5);
    border-radius: 3px;
  }
</style>
