var terrainLayer = new olgm.layer.Google({
        title: 'Terrain',
        type: 'base',
        visible: true,
        mapTypeId: google.maps.MapTypeId.TERRAIN
    }),
    satelliteLayer = new olgm.layer.Google({
        title: 'Satellite',
        type: 'base',
        visible: false,
        mapTypeId: google.maps.MapTypeId.SATELLITE
    }),
    osmLayer = new ol.layer.Tile({
        title: 'OpenStreetMap',
        type: 'base',
        visible: false,
        source: new ol.source.OSM({}),
        //source: new ol.source.XYZ({
        //    //urls: ["http://a.tile2.opencyclemap.org/transport/{z}/{x}/{y}.png","http://b.tile2.opencyclemap.org/transport/{z}/{x}/{y}.png","http://c.tile2.opencyclemap.org/transport/{z}/{x}/{y}.png"]
        //    //urls: ["http://a.tile3.opencyclemap.org/landscape/{z}/{x}/{y}.png","http://b.tile3.opencyclemap.org/landscape/{z}/{x}/{y}.png","http://c.tile3.opencyclemap.org/landscape/{z}/{x}/{y}.png"]
        //    urls: ["http://s.tile.openstreetmap.org/{z}/{x}/{y}.png","http://b.tile.openstreetmap.org/{z}/{x}/{y}.png","http://c.tile.openstreetmap.org/{z}/{x}/{y}.png"]
        //    //urls: ["http://otile1.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png","http://otile2.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png","http://otile3.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png","http://otile4.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png"]
        //    //urls: ["http://a.tile.stamen.com/watercolor/{z}/{x}/{y}.png","http://b.tile.stamen.com/watercolor/{z}/{x}/{y}.png","http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png","http://d.tile.sta
        //})
    });

var baseLayers = [
    osmLayer,
    satelliteLayer,
    terrainLayer,
];

var contextLayers = [
    // Global layers
    new ol.layer.Tile({
        title: 'Accessibility<a href="#accessability" data-toggle="modal" data-target="#map-legend"><i class="lm lm-question-circle"> </i></a>',
        source: new ol.source.TileWMS({
            url: "http://sdi.cde.unibe.ch/geoserver/lo/wms",
            params: {
                'srs': 'EPSG%3a900913',
                'layers': 'accessability' // Typo needed!
            }
        }),
        visible: false,
        opacity: 0.6
    }),
    new ol.layer.Tile({
        title: 'Global Land Cover 2009<a href="#globcover_2009" data-toggle="modal" data-target="#map-legend"><i class="lm lm-question-circle"> </i></a>',
        source: new ol.source.TileWMS({
            url: "http://sdi.cde.unibe.ch/geoserver/lo/wms",
            params: {
                'srs': 'EPSG%3a900913',
                'layers': 'globcover_2009'
            }
        }),
        visible: false,
        opacity: 0.6
    }),
    new ol.layer.Tile({
        title: 'Global Cropland<a href="#gl_cropland" data-toggle="modal" data-target="#map-legend"><i class="lm lm-question-circle"> </i></a>',
        source: new ol.source.TileWMS({
            url: "http://sdi.cde.unibe.ch/geoserver/lo/wms",
            params: {
                'srs': 'EPSG%3a900913',
                'layers': 'gl_cropland'
            }
        }),
        visible: false,
        opacity: 0.6
    }),
    new ol.layer.Tile({
        title: 'Global Pasture Land<a href="#gl_pasture" data-toggle="modal" data-target="#map-legend"><i class="lm lm-question-circle"> </i></a>',
        source: new ol.source.TileWMS({
            url: "http://sdi.cde.unibe.ch/geoserver/lo/wms",
            params: {
                'srs': 'EPSG%3a900913',
                'layers': 'gl_pasture'
            }
        }),
        visible: false,
        opacity: 0.6
    }),
    // LAOS LOCAL LAYER! TODO!
    new ol.layer.Tile({
        title: 'Incidence of poverty<a href="#lo:laos_poverty_incidence" data-toggle="modal" data-target="#map-legend"><i class="lm lm-question-circle"> </i></a>',
        source: new ol.source.TileWMS({
            url: "http://sdi.cde.unibe.ch/geoserver/gwc/service/wms",
            params: {
                'srs': 'EPSG%3A900913',
                'layers': 'lo:laos_poverty_incidence'
            }
        }),
        extent: [10018755, 181, 12801601, 3482189],
        visible: false,
        opacity: 0.7
    })
];
/*
 new ol.Layer.WMS("Accessibility to province capital","http://sdi.cde.unibe.ch/geoserver/gwc/service/wms",{
 epsg: 900913,
 format: "image/png8",
 layers: "lo:laos_t_to_prov_capital_mean_min",
 transparent: true,
 },{
 visibility: false,
 isBaseLayer: false,
 sphericalMercator: true,
 maxExtent: new ol.Bounds(10018755, 181, 12801601, 3482189),
 opacity: 0.7,
 })

 /*,
 new ol.Layer.WMS("Seasonal road accessibility","http://sdi.cde.unibe.ch/geoserver/gwc/service/wms",{
 epsg: 900913,
 format: "image/png8",
 layers: "lo:laos_w_road_access",
 transparent: true,
 },{
 visibility: false,
 isBaseLayer: false,
 sphericalMercator: true,
 maxExtent: new ol.Bounds(10018755, 181, 12801601, 3482189),
 opacity: 0.7,
 }),
 new ol.Layer.WMS("Population density","http://sdi.cde.unibe.ch/geoserver/gwc/service/wms",{
 epsg: 900913,
 format: "image/png8",
 layers: "lo:laos_pop_density",
 transparent: true,
 },{
 visibility: false,
 isBaseLayer: false,
 sphericalMercator: true,
 maxExtent: new ol.Bounds(10018755, 181, 12801601, 3482189),
 opacity: 0.7,
 }),
 new ol.Layer.WMS("Share of households being farm household","http://sdi.cde.unibe.ch/geoserver/gwc/service/wms",{
 epsg: 900913,
 format: "image/png8",
 layers: "lo:laos_w_pct_farmhh",
 transparent: true,
 },{
 visibility: false,
 isBaseLayer: false,
 sphericalMercator: true,
 maxExtent: new ol.Bounds(10018755, 181, 12801601, 3482189),
 opacity: 0.7,
 }),
 new ol.Layer.WMS("Protected areas","http://sdi.cde.unibe.ch/geoserver/gwc/service/wms",{
 epsg: 900913,
 format: "image/png8",
 layers: "lo:laos_protected_area",
 transparent: true,
 },{
 visibility: false,
 isBaseLayer: false,
 sphericalMercator: true,
 maxExtent: new ol.Bounds(10018755, 181, 12801601, 3482189),
 opacity: 0.7,
 }),
 new ol.Layer.WMS("Percentage of economically active population","http://sdi.cde.unibe.ch/geoserver/gwc/service/wms",{
 epsg: 900913,
 format: "image/png8",
 layers: "lo:laos_pop_econ_active_pct",
 transparent: true,
 },{
 visibility: false,
 isBaseLayer: false,
 sphericalMercator: true,
 maxExtent: new ol.Bounds(10018755, 181, 12801601, 3482189),
 opacity: 0.7,
 }),

 ]

 */
