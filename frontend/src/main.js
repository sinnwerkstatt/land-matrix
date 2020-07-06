import Vue from "vue";
import BootstrapVue from "bootstrap-vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import Multiselect from "vue-multiselect";
import VCalendar from "v-calendar";

import "../node_modules/font-awesome/scss/font-awesome.scss";

Vue.use(BootstrapVue);
import "bootstrap";

Vue.use(VCalendar);

Vue.component("multiselect", Multiselect);
import "vue-multiselect/dist/vue-multiselect.min.css";

import "leaflet/dist/leaflet.css";
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
  iconUrl: require("leaflet/dist/images/marker-icon.png"),
  shadowUrl: require("leaflet/dist/images/marker-shadow.png"),
});
import "leaflet-draw/dist/leaflet.draw.css";

import "./scss/main.scss";

// needs to be registered globally for streamfield loops
import Title from "./components/Wagtail/Title";
import Heading from "./components/Wagtail/Heading";
import Image from "./components/Wagtail/Image";
import Paragraph from "./components/Wagtail/Paragraph";
import Columns1on1 from "./components/Wagtail/Columns1on1";
import Columns3 from "./components/Wagtail/Columns3";
import FullWidthContainer from "./components/Wagtail/FullWidthContainer";
import Slider from "./components/Wagtail/Slider";
import Gallery from "./components/Wagtail/Gallery";
import FaqsBlock from "./components/Wagtail/FaqsBlock";
import Twitter from "./components/Wagtail/Twitter";
import LatestNews from "./components/Wagtail/LatestNews";
import LatestDatabaseModifications from "./components/Wagtail/LatestDatabaseModifications";
import Statistics from "./components/Wagtail/Statistics";
import SectionDivider from "@/components/Wagtail/SectionDivider";
import RawHTML from "@/components/Wagtail/RawHTML";
Vue.component("wagtail-title", Title);
Vue.component("wagtail-heading", Heading);
Vue.component("wagtail-image", Image);
Vue.component("wagtail-slider", Slider);
Vue.component("wagtail-gallery", Gallery);
Vue.component("wagtail-linked_image", Image);
Vue.component("wagtail-paragraph", Paragraph);
Vue.component("wagtail-columns_1_1", Columns1on1);
Vue.component("wagtail-columns_3", Columns3);
Vue.component("wagtail-section_divider", SectionDivider);
Vue.component("wagtail-html", RawHTML);
Vue.component("wagtail-full_width_container", FullWidthContainer);
Vue.component("wagtail-faqs_block", FaqsBlock);
Vue.component("wagtail-twitter", Twitter);
Vue.component("wagtail-latest_news", LatestNews);
Vue.component("wagtail-latest_database_modifications", LatestDatabaseModifications);
Vue.component("wagtail-statistics", Statistics);
// Vue.component("wagtail-", );

store.dispatch("fetchUser");
store.dispatch("fetchCountriesAndRegions");
// This is because e.g. "footer columns" are specified on the root page *rolls eyes*:
store.dispatch("fetchWagtailRootPage");

store.dispatch("fetchFields");

export default new Vue({
  router,
  store,
  render: (h) => h(App),
}).$mount("#app");
