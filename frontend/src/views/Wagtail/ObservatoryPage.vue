<template>
  <div class="observatory">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-sm-12 col-md-10 col-lg-8 col-xl-6">
          <h1>{{ page.title }}</h1>
          <QuasiStaticMap :region-id="region_id" :country-id="country_id" />
        </div>
      </div>
      <div class="row justify-content-center">
        <div class="col-sm-12 col-md-10 col-lg-8 col-xl-6">
          <div v-if="page.introduction_text" class="intro-text">
            <div class="intro">
              {{ page.introduction_text }}
            </div>
            <div v-if="!readMore" class="readmore">
              <p><a href="" @click.prevent="readMore = true">Read more</a></p>
            </div>
            <div class="row">
              <Streamfield v-if="readMore" :content="content" />
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="jumbotron jumbotron-fluid charts">
      <div class="container">
        <div class="row justify-content-center">
          <div class="col-sm-12 col-md-10 col-lg-8 col-xl-6">
            <div class="row">
              <div class="col-12">
                <h3>We currently have information about:</h3>
                <div class="row">
                  <div class="col-6 text-center">
                    <label>Size</label>
                    <div class="total">{{ totalSize }} ha</div>
                    <StatusPieChart
                      :deal-data="negotiationStatusBuckets"
                      :display-legend="true"
                      :aspect-ratio="1"
                      value-field="size"
                      unit="ha"
                    />
                  </div>
                  <div class="col-6 text-center">
                    <label>Number of deals</label>
                    <div class="total">
                      {{ totalCount }}
                    </div>
                    <StatusPieChart
                      :deal-data="negotiationStatusBuckets"
                      :display-legend="true"
                      :aspect-ratio="1"
                      value-field="count"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-sm-12 col-md-11 col-lg-9 col-xl-7">
          <MapDataCharts @click.native="setGlobalLocationFilter" />
        </div>
      </div>
    </div>
    <ArticleList
      :articles-label="$t('Country profiles')"
      :articles="filteredCountryProfiles"
    >
      <div class="description">
        <p>
          {{
            $t(
              "Country profiles present national-level data of large-scale land acquisitions and transactions including who the investors are, what the aim of the investment is, who the former owner was and what the land was previously used for, and what the potential benefits and impacts of the land deals are."
            )
          }}
        </p>
        <p>
          {{
            $t(
              "By making this information available, the Land Matrix hopes to enhance broad engagement and data exchange, facilitating the continuous improvement of the data. Find out how to get involved"
            )
          }}
          <router-link :to="`/get-involved/`">
            {{ $t("here") }}
          </router-link>
          .
        </p>
        <h4>{{ $t("Download country profiles for") }}:</h4>
      </div>
    </ArticleList>
    <ArticleList
      :articles-label="$t('News & publications')"
      :articles="filteredNewsPubs"
    />
    <div v-if="page.twitter_feed" class="container tweets">
      <div class="row justify-content-center">
        <div class="col-sm-12 col-md-10 col-lg-8 col-xl-6">
          <h3>{{ $t("Latest tweets") }}</h3>
          <Twitter :value="page.twitter_feed" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import gql from "graphql-tag";
  import { deal_aggregations_query } from "$store/queries";
  import Streamfield from "$components/Streamfield";
  import StatusPieChart from "$components/Charts/StatusPieChart";
  import MapDataCharts from "$components/Wagtail/MapDataCharts";
  import ArticleList from "$components/Wagtail/ArticleList";
  import Twitter from "$components/Wagtail/Twitter";
  import QuasiStaticMap from "$components/QuasiStaticMap";

  export default {
    name: "ObservatoryPage",
    components: {
      QuasiStaticMap,
      StatusPieChart,
      Streamfield,
      MapDataCharts,
      ArticleList,
      Twitter,
    },
    data() {
      return {
        readMore: false,
        deals: [],
        deal_aggregations: null,
        articles: [],
      };
    },
    apollo: {
      deal_aggregations: deal_aggregations_query,
      articles: {
        query: gql`
          query {
            articles: blogpages {
              id
              title
              slug
              date
              header_image
              excerpt
              categories {
                slug
              }
              tags {
                slug
              }
              url
            }
          }
        `,
      },
    },
    computed: {
      page() {
        return this.$store.state.page.wagtailPage;
      },
      region_id() {
        return this.page.region ? this.page.region.id : null;
      },
      country_id() {
        return this.page.country ? this.page.country.id : null;
      },
      slug() {
        let ret;
        if (this.page.region) {
          ret = this.$store.getters.getCountryOrRegion({
            type: "region",
            id: this.page.region.id,
          });
        } else if (this.page.country) {
          ret = this.$store.getters.getCountryOrRegion({
            type: "country",
            id: this.page.country.id,
          });
        }
        return ret ? ret.slug : null;
      },
      content() {
        return this.page ? this.page.body : [];
      },
      totalCount() {
        if (!this.deal_aggregations) return;
        return this.deal_aggregations.current_negotiation_status
          .map((ns) => ns.count)
          .reduce((a, b) => +a + +b, 0)
          .toLocaleString();
      },
      totalSize() {
        if (!this.deal_aggregations) return;
        return this.deal_aggregations.current_negotiation_status
          .map((ns) => ns.size)
          .reduce((a, b) => +a + +b, 0)
          .toLocaleString();
      },
      negotiationStatusBuckets() {
        if (!this.deal_aggregations) return;
        let retval = [
          { color: "rgba(252,148,31,0.4)", label: "Intended", count: 0, size: 0 },
          { color: "rgba(252,148,31,1)", label: "Concluded", count: 0, size: 0 },
          { color: "rgba(125,74,15,1)", label: "Failed", count: 0, size: 0 },
        ];
        for (let agg of this.deal_aggregations.current_negotiation_status) {
          switch (agg.value) {
            case "EXPRESSION_OF_INTEREST":
            case "UNDER_NEGOTIATION":
            case "MEMORANDUM_OF_UNDERSTANDING":
              retval[0].count += agg.count;
              retval[0].size += +agg.size;
              break;
            case "ORAL_AGREEMENT":
            case "CONTRACT_SIGNED":
              retval[1].count += agg.count;
              retval[1].size += +agg.size;
              break;

            case "NEGOTIATIONS_FAILED":
            case "CONTRACT_CANCELED":
              retval[2].count += agg.count;
              retval[2].size += +agg.size;
              break;
          }
        }
        return retval;
      },

      filteredCountryProfiles() {
        if (!this.slug) return [];
        return this.articles
          .filter((a) => {
            return (
              a.tags.find((t) => {
                return t.slug === this.slug;
              }) &&
              a.categories.find((c) => {
                return c.slug === "country-profile";
              })
            );
          })
          .sort((a, b) => new Date(b.date) - new Date(a.date));
      },
      filteredNewsPubs() {
        if (!this.slug) return [];
        return this.articles
          .filter((a) => {
            return (
              a.tags.find((t) => {
                return t.slug === this.slug;
              }) &&
              a.categories.find((c) => {
                return ["news", "publications"].includes(c.slug);
              })
            );
          })
          .sort((a, b) => new Date(b.date) - new Date(a.date));
      },
    },
    watch: {
      page: {
        immediate: true,
        handler() {
          this.readMore = !this.page.introduction_text;
        },
      },
    },
    methods: {
      setGlobalLocationFilter() {
        if (this.page.region) {
          this.$store.dispatch("setFilter", {
            filter: "country_id",
            value: null,
          });
          this.$store.dispatch("setFilter", {
            filter: "region_id",
            value: this.page.region.id,
          });
        } else if (this.page.country) {
          this.$store.dispatch("setFilter", {
            filter: "region_id",
            value: null,
          });
          this.$store.dispatch("setFilter", {
            filter: "country_id",
            value: this.page.country.id,
          });
        }
      },
    },
  };
</script>

<style lang="scss" scoped>
  @import "src/scss/colors";

  .observatory {
    margin-bottom: 5em;
    h1 {
      font-size: 48px;
      font-weight: normal !important;
      color: black;
      text-align: left;
      text-transform: none;

      &:before {
        content: none;
      }
    }

    .intro-text {
      padding-top: 1.5em;
      padding-bottom: 0.8em;
      .readmore {
        margin-top: 1.5em;
      }
    }

    .charts {
      background-color: #f9f9f9;
      padding: 0 0 1.5em;
      margin-top: 0;

      label {
        color: $lm_orange;
        font-weight: bold;
        font-size: 15px;
        margin-bottom: 0;
      }

      .total {
        font-weight: bold;
        font-size: 15px;
        margin-bottom: 0.5em;
      }
    }

    .tweets {
      margin-bottom: 2em;
    }
  }
</style>
<style lang="scss">
  .observatory {
    h3 {
      font-size: 24px;
    }

    .static-map {
      margin-top: 1.5em;
    }

    .streamfield {
      .container {
        padding-top: 1.5em;
        padding-bottom: 0;
      }
    }

    .charts {
      .legend {
        text-align: center;
        margin-top: 1em;

        .legend-item {
          .colored-area {
            width: 0.8em;
            height: 0.8em;
          }
        }
      }
    }
  }
</style>
