// this whole file is only a test at the moment.
import { apolloClient } from "apolloclient";
import { data_deal_query_gql } from "views/Data/query";

export const dataModule = {
  state: () => ({
    investors: [],
    deals: [],
  }),
  getters: {
    mapMarkers: (state) => {
      return "foo";
    },
  },
  mutations: {
    setDeals(state, deals) {
      state.deals = deals;
    },
  },
  actions: {
    fetchDeals(context) {
      let user = context.rootState.page.user;
      apolloClient
        .query({
          query: data_deal_query_gql,
          variables: {
            limit: 0,
            filters: context.getters.filtersForGQL,
            subset: user && user.is_authenticated ? "ACTIVE" : "PUBLIC",
          },
        })
        .then((data) => {
          context.commit("setDeals", data.data.deals);
        });
    },
    // fetchMarkers(context) {
    //   let filters= context.getters.filtersForGQL.filter(
    //       (f) => f.field !== "country_id" && f.field !== "country.fk_region_id"
    //     );
    //
    // },
  },
};
