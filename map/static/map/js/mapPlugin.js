(function ($) {
    $.extend({
        setMap: function (options) {

            // Default settings.
            var settings = $.extend({
                target: "map",
                zoom: 2.8,
                centerTo: [-20, 20],
                legendKey: 'intention',
                visibleLayer: 'countries',  // Either "countries" (default) or "deals". Should correspond to state of switch position.
                autoToggle: true  // Defaults to true. Should correspond to state of checkbox next to switch.
            }, options);

            // Chart settings. Also needed to adjust clustering sensibility.
            var minFontSize = 1.25;  // Font size is usually clusterRadius / 100
            var minClusterRadius = 100;
            var maxClusterRadius = 300;
            var clusterDistance = 125;

            // The resolution for which to toggle the layers automatically.
            var autoToggleResolution = 2000;

            var mapInstance = this;

            // Variables needed to calculate the size of the clusters.
            var currentResolution;
            var maxFeatureCount;

            // Variable used to trigger cluster update even though resolution
            // did not change (after changing displayed layer)
            var layerChanged = false;

            // Mappings to allow grouping of intentions (required for Agriculture, Forestry)
            var legendValueMappings = {
                'intention': {
                    'Biofuels': 'Agriculture',
                    'Food crops': 'Agriculture',
                    'Fodder': 'Agriculture',
                    'Livestock': 'Agriculture',
                    'Non-food agricultural commodities': 'Agriculture',
                    'Agriculture unspecified': 'Agriculture',
                    'Timber plantation (for wood and fibre)': 'Forestry',
                    'Forest logging / management (for wood and fibre)': 'Forestry',
                    'For carbon sequestration/REDD': 'Forestry',
                    'Forestry unspecified': 'Forestry',
                }
            };

            // use this.setLegendKey() to switch currently active legend.
            mapInstance.legendKey = options.legendKey;
            mapInstance.dealsPerCountryLayer = null;

            var baseLayers = getBaseLayers();
            var contextLayers = getContextLayers();
            var polygonLayers = {};

            // initialize map
            var map = new ol.Map({
                target: settings.target,
                layers: baseLayers.concat(contextLayers),
                view: new ol.View({
                    center: ol.proj.fromLonLat(settings.centerTo),
                    zoom: settings.zoom
                })
            });

            // Layer and source holding countries.
            var countrySource = new ol.source.Vector();
            var countryLayer = new ol.layer.Vector({
                source: countrySource,
                name: "highlightedCountries",
                style: new ol.style.Style({
                    fill: new ol.style.Fill({
                        color: [252, 148, 31, 0.2]
                    }),
                    stroke: new ol.style.Stroke({
                        color: [252, 148, 31, 1],
                        width: 2,
                        lineCap: "round"
                    })
                }),
                visible: settings.visibleLayer == 'countries'
            });
            map.addLayer(countryLayer);

            // Layer and source for the deals per country. All deals are
            // clustered and displayed in the 'centre' of the country.
            var dealsPerCountrySource = new ol.source.Vector();
            var dealsPerCountryCluster = new ol.source.Cluster({
                source: dealsPerCountrySource,
                distance: clusterDistance
            });

            // Layer and source for the deals. All deals are clustered.
            var dealsSource = new ol.source.Vector();
            var dealsCluster = new ol.source.Cluster({
                source: dealsSource,
                distance: clusterDistance
            });

            // Map search if available
            if (settings.searchFieldId) {
                var mapSearch = new google.maps.places.SearchBox(document.getElementById(settings.searchFieldId));
                mapSearch.addListener('places_changed', function() {
                    var places = this.getPlaces();
                    if (places.length != 1) {
                      return;
                    }
                    var loc = places[0].geometry.viewport.toJSON();
                    mapInstance.zoomToExtent(loc.south, loc.west, loc.north, loc.east);
                });
            }

            // Overlay for the container with detailed information after a click
            var featureDetailsElement = $("#" + settings.featureDetailsElement);

            // Draw deals per country with all properties in the geojson.
            function drawCountryInformation(features, countryDealsSource) {
                $.each(features, function (key, country) {
                    // extent.getCenter() returns undefined with ol 4.0, so
                    // calculate it manually.
                    var definedCentre = country.get('centre_coordinates');
                    if (definedCentre) {
                        var lat = definedCentre[0];
                        var lon = definedCentre[1];
                    } else {
                        var extent = country.getGeometry().getExtent();
                        var lat = extent[0] + (extent[2] - extent[0]) / 2;
                        var lon = extent[1] + (extent[3] - extent[1]) / 2;
                    }

                    // Copy the properties of the country, except the geometry
                    var properties = country.getProperties();
                    delete properties.geometry;

                    var countryInfoPoint = new ol.Feature(
                        new ol.geom.Point(ol.proj.fromLonLat([lat, lon]))
                    );

                    // Relabel subcategories
                    var propertyMappings,
                        childCount,
                        parentProp;
                    for (var propertyKey in legendValueMappings) {
                        propertyMappings = legendValueMappings[propertyKey];
                        if (typeof propertyMappings === "undefined") {
                            continue;
                        }
                        if (typeof properties[propertyKey] === "undefined") {
                            properties[propertyKey] = {};
                        }
                        for (var childProp in propertyMappings) {
                            childCount = properties[propertyKey][childProp];
                            if (typeof childCount === "undefined") {
                                continue;
                            }
                            parentProp = propertyMappings[childProp];
                            if (typeof properties[propertyKey][parentProp] === "undefined") {
                                properties[propertyKey][parentProp] = 0;
                            }
                            properties[propertyKey][parentProp] += childCount;
                        }
                    }

                    countryInfoPoint.setProperties(properties);

                    countryDealsSource.addFeature(countryInfoPoint);
                });
            }

            /**
             * Prepare a data array based on the country feature properties.
             *
             * @param features: A list of country features (in the current cluster)
             * @returns {Array}
             */
            function prepareCountryClusterData(features) {

                var data = getBasicClusterData();
                var count = 0;

                // Update "count" of each value based on the feature's values.
                $.each(features, function(index, feature) {
                    // Also update count of features
                    count += feature.getProperties()['deals'];
                    var properties = feature.getProperties()[mapInstance.legendKey];
                    if (!properties) return;

                    for (var prop in properties) {
                        if (properties.hasOwnProperty(prop)) {
                            var searchProp = $.grep(data, function(e) { return e.id === prop; });
                            if (searchProp.length === 1) {
                                searchProp[0].count += properties[prop];
                            }
                        }
                    }
                });
                return {
                    cluster: data,
                    count: count
                };
            }

            /**
             * Prepare a data array based on the deal feature properties.
             *
             * @param features: A list of deal features (in the current cluster)
             * @returns {Array}
             */
            function prepareDealClusterData(features) {

                var data = getBasicClusterData();
                var count = features.length;

                // Update "count" of each value based on the feature's values.
                $.each(features, function(index, feature) {
                    var properties = feature.getProperties();
                    properties = properties[mapInstance.legendKey];
                    if (!properties) return;

                    if (typeof properties === 'string') {
                        properties = [properties];
                    }
                    $.each(properties, function(i, prop) {
                        var searchProp = $.grep(data, function(e) { return e.id == prop; });
                        if (searchProp.length == 1) {
                            searchProp[0].count += 1;
                        }
                    });
                });
                return {
                    cluster: data,
                    count: count
                };
            }

            /**
             * Return an array with an object for each of the current legend
             * attributes. Count is set to 0.
             *
             * @returns {Array}
             */
            function getBasicClusterData() {
                // Collect all possible values
                var data = [];
                $.each(options.legend[mapInstance.legendKey].attributes, function(i, d) {
                    data.push({
                        color: d.color,
                        id: d.id,
                        count: 0
                    });
                });
                return data;
            }

            // Calculate the feature count (maxFeatureCount) in the biggest
            // cluster visible on the map. No need to calculate this if the
            // resolution did not change.
            function calculateClusterInfo(clusterLayerSource, countProperty) {
                if (currentResolution == map.getView().getResolution() && !layerChanged) {
                    return;
                }
                layerChanged = false;
                currentResolution = map.getView().getResolution();
                maxFeatureCount = 0;
                $.each(clusterLayerSource.getFeatures(), function(i, feature) {
                    var clusteredFeatures = feature.get('features');
                    if (countProperty) {
                        var c = 0;
                        $.each(clusteredFeatures, function(j, f) {
                            c += f.getProperties()[countProperty];
                        });
                        maxFeatureCount = Math.max(maxFeatureCount, c);
                    } else {
                        maxFeatureCount = Math.max(
                            maxFeatureCount,
                            getUniqueDealsFromFeatures(clusteredFeatures).length);
                    }
                });
            }

            /**
             * Filter a list of features and return only the first feature of a
             * deal based on its identifier. This removes multipoint entries by
             * keeping only the first point encountered.
             *
             * CAREFUL: This does not really return deals with multipoint
             * geometries, it just returns the first feature of each deal. Use
             * this only for calculating statistics etc., not for mapping!
             *
             * @param features
             * @returns list of deal features.
             */
            function getUniqueDealsFromFeatures(features) {
                var uniqueIds = [];
                return features.filter(function(c) {
                    var id = c.getProperties().identifier;
                    if (uniqueIds.indexOf(id) == -1) {
                        uniqueIds.push(id);
                        return c;
                    }
                });
            }

            // Draw a clustered layer with the properties from the current
            // legend as 'svg-doghnut' surrounding the cluster point.
            function getCountryClusterLayer() {
                return new ol.layer.Vector({
                    source: dealsPerCountryCluster,
                    name: "countries",
                    style: getCountryClusterStyle,
                    visible: settings.visibleLayer == 'countries'
                });
            }

            // Draw a clustered layer with the properties from the current
            // legend as donut surrounding the cluster point.
            function getDealsClusterLayer() {
                return new ol.layer.Vector({
                    name: "deals",
                    source: dealsCluster,
                    style: getDealsClusterStyle,
                    visible: settings.visibleLayer == 'deals'
                });
            }

            function getCountryClusterStyle(feature) {
                calculateClusterInfo(dealsPerCountryCluster, 'deals');

                var clusteredFeatures = feature.get('features');

                var clusterSVG = new Image();
                var clusterData = prepareCountryClusterData(clusteredFeatures);
                var sizeVariables = getChartSizeVariables(clusterData.count);
                clusterSVG.src = 'data:image/svg+xml,' + escape(getSvgChart(clusterData, 'countries', sizeVariables.chartSize));

                return getChartStyle(clusterSVG, clusterData.count.toString(), sizeVariables.chartSize, sizeVariables.fontSize);
            }

            function getDealsClusterStyle(feature) {
                calculateClusterInfo(dealsCluster);

                var clusteredFeatures = feature.get('features');
                var dealFeatures = getUniqueDealsFromFeatures(clusteredFeatures);

                var clusterSVG = new Image();
                var clusterData = prepareDealClusterData(dealFeatures);
                var sizeVariables = getChartSizeVariables(clusterData.count);
                clusterSVG.src = 'data:image/svg+xml,' + escape(getSvgChart(clusterData, 'deals', sizeVariables.chartSize));

                // No cluster text label for single locations (marker)
                var clusterText = clusterData.count > 1 ? clusterData.count.toString() : '';
                return getChartStyle(clusterSVG, clusterText, sizeVariables.chartSize, sizeVariables.fontSize);
            }

            function getBaseLayers() {
                return [
                    new ol.layer.Tile({
                        name: 'osm',
                        visible: true,
                        source: new ol.source.OSM()
                    }),
                    new ol.layer.Tile({
                        name: 'esri_satellite',
                        visible: false,
                        source: new ol.source.XYZ({
                            attributions: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                            url: 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                        })
                    }),
                    new ol.layer.Tile({
                        name: 'mapquest_satellite',
                        visible: false,
                        source: new ol.source.BingMaps({
                            key: 'AlP-ATiag3_dWlbAC1mQChWw_SM61c6iDv_NLJexfsE-YeAVJjIL7sgeotE3i8a2',
                            imagerySet: 'aerial'
                        })
                    })
                ];
            }

            function getContextLayers() {
                return [
                    new ol.layer.Image({
                        name: 'land_cover',
                        visible: false,
                        opacity: 0.8,
                        source: new ol.source.ImageWMS({
                            url: 'http://sdi.cde.unibe.ch/geoserver/lo/wms',
                            params: {
                                LAYERS: 'globcover_2009'
                            }
                        }),
                        // Can also be defined as property "legendUrl"
                        legendUrlFunction: function() {
                            var imgParams = {
                                request: 'GetLegendGraphic',
                                service: 'WMS',
                                layer: 'globcover_2009',
                                format: 'image/png',
                                width: 25,
                                height: 25,
                                legend_options: 'forceLabels:1;fontAntiAliasing:1;fontName:Nimbus Sans L Regular;'
                            };
                            return 'http://sdi.cde.unibe.ch/geoserver/lo/wms' + '?' + $.param(imgParams);
                        },
                        dataSourceOwner: 'Source: <a href="http://due.esrin.esa.int/page_globcover.php" target="_blank">ESA</a>'
                    }),
                    new ol.layer.Image({
                        name: 'cropland',
                        visible: false,
                        opacity: 0.8,
                        source: new ol.source.ImageWMS({
                            url: 'http://sdi.cde.unibe.ch/geoserver/lo/wms',
                            params: {
                                LAYERS: 'gl_cropland'
                            }
                        }),
                        legendUrlFunction: function() {
                            var imgParams = {
                                request: 'GetLegendGraphic',
                                service: 'WMS',
                                layer: 'gl_cropland',
                                format: 'image/png',
                                width: 25,
                                height: 25,
                                legend_options: 'forceLabels:1;fontAntiAliasing:1;fontName:Nimbus Sans L Regular;'
                            };
                            return 'http://sdi.cde.unibe.ch/geoserver/lo/wms' + '?' + $.param(imgParams);
                        },
                        dataSourceOwner: 'Source: <a href="http://sedac.ciesin.columbia.edu/data/set/aglands-croplands-2000" target="_blank">Socioeconomic Data and Applications Center (SEDAC)</a>'
                    }),
                    new ol.layer.Tile({
                        name: 'community_lands',
                        visible: false,
                        source: new ol.source.TileArcGISRest({
                            url: 'http://gis-stage.wri.org/arcgis/rest/services/IndigenousCommunityLands/comm_comm_LandMatrix/MapServer/'
                        }),
                        legendUrl: '/static/map/images/legend_community_lands.png',
                        dataSourceOwner: 'Source: <a href="http://www.landmarkmap.org/" target="_blank">LandMark</a>'
                    }),
                    new ol.layer.Tile({
                        name: 'indigenous_lands',
                        visible: false,
                        source: new ol.source.TileArcGISRest({
                            url: 'http://gis-stage.wri.org/arcgis/rest/services/IndigenousCommunityLands/comm_ind_LandMatrix/MapServer'
                        }),
                        legendUrl: '/static/map/images/legend_indigenous_lands.png',
                        dataSourceOwner: 'Source: <a href="http://www.landmarkmap.org/" target="_blank">LandMark</a>'
                    })
                ];
            }

            // Determine the chart size and font size based on the current
            // feature count. Also do some ugly manual tweaking when zoomed out
            // really far.
            function getChartSizeVariables(featureCount) {
                var currMaxClusterRadius = maxClusterRadius;
                if (currentResolution > 10000) {
                    currMaxClusterRadius = 250;
                }
                if (currentResolution > 20000) {
                    currMaxClusterRadius = 200;
                }
                if (currentResolution > 40000) {
                    currMaxClusterRadius = 150;
                }
                var currMaxFontSize = currMaxClusterRadius / 100;
                var minValue = 1;
                var scaleFactor = (featureCount - minValue) / (maxFeatureCount - minValue);
                var chartSize = scaleFactor * (currMaxClusterRadius - minClusterRadius) + minClusterRadius || minClusterRadius;
                var fontSize = scaleFactor * (currMaxFontSize - minFontSize) + minFontSize || minFontSize;
                return {
                    chartSize: chartSize,
                    fontSize: fontSize
                };
            }

            // Return the basic chart style for cluster: Use a SVG image icon
            // and display number of features as text.
            function getChartStyle(clusterSVG, clusterText, chartSize, fontSize) {
                return new ol.style.Style({
                    image: new ol.style.Icon({
                        img: clusterSVG,
                        imgSize: [chartSize, chartSize]
                    }),
                    text: new ol.style.Text({
                        text: clusterText,
                        scale: fontSize,
                        fill: new ol.style.Fill({
                            color: '#222'
                        })
                    })
                });
            }

            // Return a SVG donut chart based on the feature's data.
            function getSvgChart(data, clusterType, chartSize) {
                // Calculate total
                var total = 0;
                $.each(data.cluster, function (i, d) {
                    total += d.count;
                });

                var backgroundColor = clusterType == 'countries' ? '#f9de98' : '#fff';
                var donutWidth = chartSize / 20;

                // SVG and basic circle
                var radius = chartSize / (2 * Math.PI);
                var svg = [
                    '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="' + chartSize + 'px" height="' + chartSize + 'px" viewBox="0 0 ' + chartSize + ' ' + chartSize + '" enable-background="new 0 0 ' + chartSize + ' ' + chartSize + '" xml:space="preserve">',
                    // Basic circle
                    '<circle class="donut-hole" cx="' + chartSize/2 + '" cy="' + chartSize/2 + '" r="' + radius + '" fill="' + backgroundColor + '"></circle>',
                    '<circle class="donut-ring" cx="' + chartSize/2 + '" cy="' + chartSize/2 + '" r="' + radius + '" fill="transparent" stroke="#d2d3d4" stroke-width="' + donutWidth + '"></circle>'
                ];

                var defaultOffset = chartSize / 4; // To make chart start at top (12:00), not right (3:00).
                var totalOffsets = 0;
                $.each(data.cluster, function (i, d) {
                    var offset = chartSize - totalOffsets + defaultOffset;
                    var currValue = d.count / total * chartSize;
                    var currRemainder = chartSize - currValue;
                    var currAttr = $.grep(options.legend[mapInstance.legendKey].attributes, function (e) {
                        return e.id == d.id;
                    });
                    var currColor = "silver";
                    if (currAttr.length == 1) {
                        currColor = currAttr[0].color;
                    }
                    totalOffsets += currValue;

                    svg.push('<circle class="donut-segment" cx="' + chartSize/2 + '" cy="' + chartSize/2 + '" r="' + radius + '" fill="transparent" stroke="' + currColor + '" stroke-width="' + donutWidth + '" stroke-dasharray="' + currValue + ' ' + currRemainder + '" stroke-dashoffset="' + offset + '"></circle>');
                });

                // If it is a single deal location, add a marker
                if (data.count == 1 && clusterType == 'deals') {
                    // Parameters found through try-and-error, there is most
                    // probably a better way ...
                    var translate = chartSize / 2.38;
                    var scale = chartSize / 100;
                    svg.push('<path transform="translate(' + translate + ' ' + translate + ') scale(' + scale + ')" fill="#4a4a4a" d="M8 0c-2.761 0-5 2.239-5 5 0 5 5 11 5 11s5-6 5-11c0-2.761-2.239-5-5-5zM8 8.063c-1.691 0-3.063-1.371-3.063-3.063s1.371-3.063 3.063-3.063 3.063 1.371 3.063 3.063-1.371 3.063-3.063 3.063zM6.063 5c0-1.070 0.867-1.938 1.938-1.938s1.938 0.867 1.938 1.938c0 1.070-0.867 1.938-1.938 1.938s-1.938-0.867-1.938-1.938z" />');
                }

                svg.push('</svg>');
                return svg.join('');
            }

            // Decide which overlay to show.
            function showFeatureDetails(event, features) {
                featureDetailsElement.closest('.map-overlay-content').addClass('is-wide');
                // show empty tab and spinner
                settings.featureDetailsCallback(
                    featureDetailsElement.parent()
                );

                if (settings.visibleLayer == 'countries') {
                    showCountryDetails(features);
                } else {
                    if (features.length == 1) {
                        showSingleDealDetails(features[0])
                    } else {
                        showManyDealDetails(features);
                    }
                }
            }

            /**
             * Show details about a cluster (list) of features.
             *
             * @param features: List of features (not unique deals!)
             */
            function showManyDealDetails(features) {
                // Create a copy of the legend object
                var legend = $.extend(true, {}, options.legend[mapInstance.legendKey]);

                var dealFeatures = getUniqueDealsFromFeatures(features);
                var clusterData = prepareDealClusterData(dealFeatures);

                var count = dealFeatures.length;
                var total = 0;
                $.each(clusterData.cluster, function(i, c) {
                    legend.attributes[i].count = c.count;
                    total += c.count;
                });

                var dealsData = dealFeatures.map(function(f) {
                    var props = f.getProperties();
                    return {
                        id: props.identifier,
                        url: props.url
                    };
                });

                featureDetailsElement.html(Handlebars.templates['deals-many-details']({
                    legend: legend,
                    count: count,
                    total: total,
                    hasMultipleAttributes: count != total,
                    deals: dealsData
                }));

                // Chart
                var chartData = {
                    colors: legend.attributes.map(function(l) { return l.color }),
                    labels: legend.attributes.map(function(l) { return l.label }),
                    data: legend.attributes.map(function(l) { return l.count })
                };
                drawChart(chartData);
            }

            /**
             * Show details about a cluster (list) of deals grouped by country.
             * @param features
             */
            function showCountryDetails(features) {
                // Create a copy of the legend object
                var legend = $.extend(true, {}, options.legend[mapInstance.legendKey]);

                var countries = [];
                var country_names = [];

                // Loop through each feature to get its values. Also collect
                // additional information of the feature (name, url etc.)
                $.each(features, function(i, feature) {
                    var featureProperties = feature.getProperties();

                    // The feature's properties currently active according to the legend.
                    var featurePropertiesLegend = featureProperties[mapInstance.legendKey];
                    if (!featurePropertiesLegend) {
                        return;
                    }

                    var featureTotal = 0;
                    legend.attributes.map(function(l) {
                        if (!l.values) {
                            l.values = [];
                        }
                        var val = featurePropertiesLegend[l.id] || 0;
                        l.values.push(val);
                        featureTotal += val;
                    });

                    countries.push({
                        name: featureProperties.name,
                        total: featureTotal,
                        url: featureProperties.url
                    });
                    country_names.push(featureProperties.name);

                });

                featureDetailsElement.html(Handlebars.templates['countries-details']({
                    title: country_names.join(', '),
                    countries: countries,
                    legend: legend
                }));

                // Chart
                var chartData = {
                    colors: legend.attributes.map(function(l) { return l.color }),
                    labels: legend.attributes.map(function(l) { return l.label }),
                    data: legend.attributes.map(function(l) {
                        return l.values.reduce(function(pv, cv) { return pv + cv; }, 0) || 0;
                    })
                };
                drawChart(chartData);
            }

            /**
             * Show details about a single deal.
             *
             * @param feature
             */
            function showSingleDealDetails(feature) {

                // Collect translated legend values if not available yet.
                if (!mapInstance.legendLabelled) {
                    var legendLabelled = {};
                    for (var legendKey in options.legend) {
                        if (options.legend.hasOwnProperty(legendKey)) {
                            var legendValues = {};
                            $.each(options.legend[legendKey].attributes, function(i, l) {
                                legendValues[l.id] = l.label;
                            });
                            legendLabelled[legendKey] = legendValues;
                        }
                    }
                    mapInstance.legendLabelled = legendLabelled;
                }

                featureDetailsElement.html(Handlebars.templates['deals-single-details']({
                    properties: feature.getProperties()
                }));
            }

            // Display popover on click. Doubleclick should still zoom in.
            map.on("singleclick", function (event) {
                var dealFeature = null;
                var countryFeature = null;
                map.forEachFeatureAtPixel(event.pixel, function (feature, layer) {
                    // use 'active' layer (deals per country or all deals) only.
                    if (layer.get('name') == settings.visibleLayer) {
                        dealFeature = feature;
                    }
                    if (layer.get('name') == "highlightedCountries") {
                        countryFeature = feature;
                    }
                });
                // catch click on 'cluster' first, on countries second.
                if (dealFeature) {
                    showFeatureDetails(event, dealFeature.get("features"))
                }
                else if (countryFeature) {
                    showFeatureDetails(event, [countryFeature])
                }
            });

            // change pointer on hover
            map.on("pointermove", function (evt) {
                var hit = this.forEachFeatureAtPixel(evt.pixel, function(feature, layer) {
                    return true;
                });
                if (hit) {
                    this.getTargetElement().style.cursor = 'pointer';
                } else {
                    this.getTargetElement().style.cursor = '';
                }
            });

            // Listen to zoom events. If autoToggle is active, toggle layers.
            // map.getView().on("change:resolution", function() {
            //     if (settings.autoToggle) {
            //         toggleLayerByResolution();
            //     }
            // });

            // Redraw the layer with the deals per country, with the current
            // legend as properties.
            this.setDealsPerCountryLayer = function() {
                if (this.dealsPerCountryLayer) {
                    // Update only the style
                    this.dealsPerCountryLayer.setStyle(getCountryClusterStyle);
                } else {
                    this.dealsPerCountryLayer = getCountryClusterLayer();
                    map.addLayer(this.dealsPerCountryLayer);

                    // Apparently, it is necessary to re-render the map after
                    // the layer was rendered in order to properly display
                    // the charts on the map. Thanks, OpenLayers ...
                    this.dealsPerCountryLayer.on('render', function() {
                        map.render();
                    });
                }
            };

            // Redraw the layer with the deals, with the current legend as
            // properties.
            this.setDealsLayer = function() {
                if (this.dealsLayer) {
                    // Update only the style
                    this.dealsLayer.setStyle(getDealsClusterStyle);
                } else {
                    this.dealsLayer = getDealsClusterLayer();
                    map.addLayer(this.dealsLayer);

                    // Apparently, it is necessary to re-render the map after
                    // the layer was rendered in order to properly display
                    // the charts on the map. Thanks, OpenLayers ...
                    this.dealsLayer.on('render', function() {
                        map.render();
                    });
                }
            };

            // Load geojson from countries-api and display data.
            this.loadCountries = function() {
                $.ajax(settings.countriesUrl).then(function (response) {
                    var geojsonFormat = new ol.format.GeoJSON();
                    var features = geojsonFormat.readFeatures(response,
                        {featureProjection: "EPSG:3857"}
                    );
                    // countrySource.addFeatures(features);
                    drawCountryInformation(features, dealsPerCountrySource);
                });
            };

            this.loadDeals = function() {
                $.ajax(settings.dealsUrl).then(function(response) {
                    var geojsonFormat = new ol.format.GeoJSON();
                    var features = geojsonFormat.readFeatures(response,
                        {featureProjection: "EPSG:3857"}
                    );
                    dealsSource.addFeatures(features);
                });
            };

            // change the legend and reload the layer with deals.
            this.setLegendKey = function(legendKey) {
                this.legendKey = legendKey;
                // maybe: cache layers in an object.
                this.setDealsPerCountryLayer();
                this.setDealsLayer();
            };

            // Set the value of the autoToggle setting. If true, toggle layers
            // automatically by resolution.
            this.setAutoToggle = function(autoToggle) {
                settings.autoToggle = autoToggle;
                if (autoToggle) {
                    toggleLayerByResolution();
                }
            };

            /**
             * Change the currently visible layer.
             *
             * @param visibleLayer: str. Either "countries" or "deals".
             */
            this.toggleVisibleLayer = function(visibleLayer) {
                settings.visibleLayer = visibleLayer;
                var countriesVisible = visibleLayer == 'countries';

                // Toggle the checkbox
                settings.switchLayerCallback($("[data-show-layer='" + visibleLayer + "'"));

                // Manually refresh the clustering (layerChanged is needed to
                // refresh clustering even though resolution did not change).
                layerChanged = true;
                if (visibleLayer == 'countries') {
                    dealsPerCountryCluster.refresh();
                } else {
                    dealsCluster.refresh();
                }

                this.dealsLayer.setVisible(!countriesVisible);
                countryLayer.setVisible(countriesVisible);
                this.dealsPerCountryLayer.setVisible(countriesVisible);
            };

            // Toggle the layer (country and deals) based on the map's
            // resolution.
            function toggleLayerByResolution() {
                var resolution = map.getView().getResolution();
                var visibleLayer = 'countries';
                if (resolution < autoToggleResolution) {
                    visibleLayer = 'deals';
                }
                if (settings.visibleLayer != visibleLayer) {
                    // Prevent toggling layer (and refreshing clustering) if the
                    // layer did not change.
                    mapInstance.toggleVisibleLayer(visibleLayer);
                }
            }

            // Toggle a base layer based on its name.
            this.toggleBaseLayer = function(layerName) {
                $.each(baseLayers, function(i, layer) {
                    layer.setVisible(layer.get('name') == layerName);
                });
            };

            this.toggleContextLayer = function(checkboxEl) {
                var selectedLayer;
                $.each(contextLayers, function(i, layer) {
                    if (layer.get('name') == checkboxEl.value) {
                        selectedLayer = layer;
                        layer.setVisible(checkboxEl.checked);
                    }
                });
                // Toggle legend if available
                if (!selectedLayer) {
                    return;
                }
                var legendUrl = selectedLayer.get('legendUrl');
                var legendUrlFunction = selectedLayer.get('legendUrlFunction');
                if (legendUrlFunction) {
                    legendUrl = legendUrlFunction();
                }
                var legendHtml = legendUrl ? '<img src="' + legendUrl + '"/>' : '';
                var legendDiv = $(checkboxEl).siblings('.context-layer-legend');
                if (checkboxEl.checked) {
                    legendDiv.html(legendHtml + '<p>' + selectedLayer.get('dataSourceOwner') + '</p>');
                } else {
                    legendDiv.html('');
                }
            };

            this.togglePolygons = function(checkboxEl) {

                // Check if the layer was already loaded
                if (polygonLayers[checkboxEl.value]) {
                    var currentLayer = polygonLayers[checkboxEl.value];
                    currentLayer.setVisible(checkboxEl.checked);
                    return;
                }

                // Load the layer if necessary
                var layerId = checkboxEl.value;
                var layerSettings = settings.polygonLayers[layerId];
                if (!layerSettings) {
                    return;
                }
                $.ajax(layerSettings.url).then(function (response) {
                    var geojsonFormat = new ol.format.GeoJSON();
                    var features = geojsonFormat.readFeatures(
                        response, {
                            dataProjection: 'EPSG:4326',
                            featureProjection: 'EPSG:3857'
                        });
                    var polygonSource = new ol.source.Vector();
                    polygonSource.addFeatures(features);
                    var polygonLayer = new ol.layer.Vector({
                        source: polygonSource,
                        name: layerId,
                        style: new ol.style.Style({
                            fill: new ol.style.Fill({
                                color: hexToRGB(layerSettings.color, 0.4)
                            }),
                            stroke: new ol.style.Stroke({
                                color: layerSettings.color,
                                width: 2,
                                lineCap: "round"
                            })
                        })
                    });
                    map.addLayer(polygonLayer);

                    // Store the layer so it does not need to be queried again
                    polygonLayers[layerId] = polygonLayer;
                });
            };

            /**
             * Draw a chart using ChartsJS in a div#chart. Required a data
             * object with arrays for keys "labels", "data" and "colors."
             *
             * @param chartData
             */
            function drawChart(chartData) {
                var ctx = document.getElementById("chart");
                var doughnutChart = new Chart(ctx, {
                    type: "doughnut",
                    data: {
                        labels: chartData.labels,
                        datasets: [
                            {
                                data: chartData.data,
                                backgroundColor: chartData.colors
                            }
                        ]
                    }
                });
            }

            /**
             *  x and y are intentionally flipped in this method, as this
             *  matches the existing data from the database.
             */
            this.zoomToExtent = function(minx, miny, maxx, maxy) {
                var extent = ol.proj.transformExtent(
                    [miny, minx, maxy, maxx], "EPSG:4326", "EPSG:3857"
                );
                map.getView().fit(extent, map.getSize());
            };

            this.highlightCountry = function(url) {
                $.ajax(url).then(function (response) {
                    var geojsonFormat = new ol.format.GeoJSON();
                    var features = geojsonFormat.readFeatures(
                        response, {featureProjection: "EPSG:3857"}
                    );
                    countrySource.addFeatures(features);
                });
                countryLayer.setVisible(true);
            };

            return this;
        }
    });

    function hexToRGB(hex, alpha) {
        // http://stackoverflow.com/a/28056903/841644
        var r = parseInt(hex.slice(1, 3), 16),
            g = parseInt(hex.slice(3, 5), 16),
            b = parseInt(hex.slice(5, 7), 16);

        if (alpha) {
            return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";
        } else {
            return "rgb(" + r + ", " + g + ", " + b + ")";
        }
    }

    /**
     * Handlebars helper to format number values: Add thousands separator or
     * return "-" if no value.
     */
    Handlebars.registerHelper('numberFormat', function(val) {
        // http://stackoverflow.com/a/2901298/841644
        return val ? val.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : '-';
    });
})(jQuery);
