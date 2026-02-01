import { useEffect, useRef, useCallback, useState } from 'react'

export default function MapView({ bounds, jobId, onMapClick, onLayersLoaded }) {
  const mapRef = useRef(null)
  const viewRef = useRef(null)
  const layersRef = useRef({ vector: [], raster: [] })
  const layerListRef = useRef(null)
  const [viewReady, setViewReady] = useState(false)

  // 生成年份颜色映射
  const generateYearColors = useCallback((SimpleFillSymbol, startYear, endYear, startColor, endColor) => {
    const colors = []
    const range = endYear - startYear
    for (let year = startYear; year <= endYear; year++) {
      const t = (year - startYear) / range
      const r = Math.round(startColor[0] + t * (endColor[0] - startColor[0]))
      const g = Math.round(startColor[1] + t * (endColor[1] - startColor[1]))
      const b = Math.round(startColor[2] + t * (endColor[2] - startColor[2]))
      colors.push({
        value: year,
        symbol: new SimpleFillSymbol({
          color: [r, g, b, 0.6],
          outline: { color: [r * 0.7, g * 0.7, b * 0.7], width: 1 }
        }),
        label: `${year}`
      })
    }
    return colors
  }, [])

  const initMap = useCallback(() => {
    if (!mapRef.current || viewRef.current) return

    const require = window.require
    if (!require) {
      console.error('ArcGIS API 未加载，请检查 index.html 中的 CDN 引用')
      return
    }

    console.log('开始初始化 ArcGIS 地图...')

    require([
      "esri/Map",
      "esri/views/MapView",
      "esri/widgets/LayerList",
      "esri/geometry/support/webMercatorUtils",
      "esri/geometry/Extent",
      "esri/layers/GeoJSONLayer",
      "esri/layers/WebTileLayer",
      "esri/renderers/UniqueValueRenderer",
      "esri/renderers/SimpleRenderer",
      "esri/symbols/SimpleFillSymbol",
      "esri/Graphic",
      "esri/geometry/Polygon",
    ], (Map, MapView, LayerList, webMercatorUtils, Extent, GeoJSONLayer, WebTileLayer,
        UniqueValueRenderer, SimpleRenderer, SimpleFillSymbol, Graphic, Polygon) => {

      console.log('✓ ArcGIS 模块加载成功')

      const map = new Map({ basemap: "osm" })

      const view = new MapView({
        container: mapRef.current,
        map,
        center: [110, 35],
        zoom: 6,
      })

      // 保存引用到全局
      viewRef.current = view
      window.arcgisView = view
      window.arcgisMap = map
      window.ArcGISExtent = Extent
      window.ArcGISGraphic = Graphic
      window.ArcGISPolygon = Polygon
      window.ArcGISGeoJSONLayer = GeoJSONLayer
      window.ArcGISWebTileLayer = WebTileLayer
      window.ArcGISLayerList = LayerList
      window.ArcGISSimpleRenderer = SimpleRenderer
      window.ArcGISSimpleFillSymbol = SimpleFillSymbol
      window.ArcGISUniqueValueRenderer = UniqueValueRenderer
      window.generateYearColors = (start, end, startColor, endColor) =>
        generateYearColors(SimpleFillSymbol, start, end, startColor, endColor)

      // 等待 view 完全就绪
      view.when(() => {
        console.log('✓ ArcGIS MapView 已就绪')
        setViewReady(true)
      }).catch(err => {
        console.error('MapView 初始化失败:', err)
      })

      // 点击事件 - 使用 ref 获取最新的 callback
      view.on("click", (evt) => {
        const p = evt.mapPoint
        if (!p) return

        const geo = p.spatialReference.isWebMercator
          ? webMercatorUtils.webMercatorToGeographic(p)
          : p

        // 通过 window 获取最新的回调
        if (window._mapClickHandler) {
          window._mapClickHandler({ lon: geo.longitude, lat: geo.latitude, mapPoint: p })
        }
      })
    })
  }, [generateYearColors])

  // 更新点击回调到 window
  useEffect(() => {
    window._mapClickHandler = onMapClick
    return () => {
      window._mapClickHandler = null
    }
  }, [onMapClick])

  useEffect(() => {
    initMap()
    return () => {
      if (viewRef.current) {
        viewRef.current.destroy()
        viewRef.current = null
        setViewReady(false)
      }
    }
  }, [initMap])

  // 当 bounds 变化时，跳转到数据区域并添加边界框
  useEffect(() => {
    if (!bounds || !viewRef.current || !viewReady) return

    const view = viewRef.current
    const Extent = window.ArcGISExtent
    const Graphic = window.ArcGISGraphic
    const Polygon = window.ArcGISPolygon

    console.log('跳转到数据区域:', bounds)

    if (Extent) {
      const extent = new Extent({
        xmin: bounds.west,
        ymin: bounds.south,
        xmax: bounds.east,
        ymax: bounds.north,
        spatialReference: { wkid: 4326 },
      })

      view.goTo(extent, { duration: 1500, easing: "ease-in-out" }).then(() => {
        console.log('✓ 视图跳转完成')
      }).catch(err => {
        console.warn('goTo 失败:', err)
      })
    }

    // 添加边界框
    if (Graphic && Polygon) {
      view.graphics.removeAll()
      const polygon = new Polygon({
        rings: [[
          [bounds.west, bounds.south],
          [bounds.west, bounds.north],
          [bounds.east, bounds.north],
          [bounds.east, bounds.south],
          [bounds.west, bounds.south],
        ]],
        spatialReference: { wkid: 4326 },
      })

      const graphic = new Graphic({
        geometry: polygon,
        symbol: {
          type: "simple-fill",
          color: [37, 99, 235, 0.1],
          outline: { color: [37, 99, 235, 1], width: 2 },
        },
        attributes: { name: "数据范围" }
      })
      view.graphics.add(graphic)
      console.log('✓ 已添加数据边界框')
    }
  }, [bounds, viewReady])

  // 当 jobId 变化时，加载结果图层
  useEffect(() => {
    if (!jobId || !viewRef.current || !viewReady) return

    const map = window.arcgisMap
    const view = viewRef.current
    const GeoJSONLayer = window.ArcGISGeoJSONLayer
    const SimpleRenderer = window.ArcGISSimpleRenderer
    const SimpleFillSymbol = window.ArcGISSimpleFillSymbol
    const UniqueValueRenderer = window.ArcGISUniqueValueRenderer
    const WebTileLayer = window.ArcGISWebTileLayer
    const LayerList = window.ArcGISLayerList

    if (!map || !GeoJSONLayer) {
      console.error('ArcGIS 模块未就绪')
      return
    }

    console.log('=== 开始加载结果图层 ===', jobId)

    // 移除旧图层
    layersRef.current.vector.forEach(l => {
      if (l) map.remove(l)
    })
    layersRef.current.raster.forEach(l => {
      if (l) map.remove(l)
    })
    layersRef.current = { vector: [], raster: [] }

    // 销毁旧的 LayerList
    if (layerListRef.current) {
      layerListRef.current.destroy()
      layerListRef.current = null
    }

    const baseUrl = window.location.origin

    // 矢量图层 - 扰动区域 (红色)
    const disturbanceMaskLayer = new GeoJSONLayer({
      url: `${baseUrl}/api/result-geojson/${jobId}/disturbance_mask`,
      title: "扰动区域 (矢量)",
      renderer: new SimpleRenderer({
        symbol: new SimpleFillSymbol({
          color: [220, 38, 38, 0.5],
          outline: { color: [185, 28, 28], width: 1 },
        }),
      }),
      popupTemplate: {
        title: "扰动区域",
        content: "该区域检测到采矿扰动"
      }
    })

    // 矢量图层 - 扰动年份 (按年份渐变)
    const disturbanceYearLayer = new GeoJSONLayer({
      url: `${baseUrl}/api/result-geojson/${jobId}/disturbance_year`,
      title: "扰动年份 (矢量)",
      visible: false,
      renderer: new UniqueValueRenderer({
        field: "year",
        defaultSymbol: new SimpleFillSymbol({
          color: [128, 128, 128, 0.5],
          outline: { color: [100, 100, 100], width: 1 }
        }),
        uniqueValueInfos: window.generateYearColors(2010, 2045, [255, 100, 100], [139, 0, 0])
      }),
      popupTemplate: {
        title: "扰动年份",
        content: "扰动发生年份: {year}"
      }
    })

    // 矢量图层 - 恢复年份 (绿色渐变)
    const recoveryYearLayer = new GeoJSONLayer({
      url: `${baseUrl}/api/result-geojson/${jobId}/recovery_year`,
      title: "恢复年份 (矢量)",
      visible: false,
      renderer: new UniqueValueRenderer({
        field: "year",
        defaultSymbol: new SimpleFillSymbol({
          color: [128, 128, 128, 0.5],
          outline: { color: [100, 100, 100], width: 1 }
        }),
        uniqueValueInfos: window.generateYearColors(2010, 2045, [144, 238, 144], [0, 100, 0])
      }),
      popupTemplate: {
        title: "恢复年份",
        content: "恢复发生年份: {year}"
      }
    })

    layersRef.current.vector = [disturbanceMaskLayer, disturbanceYearLayer, recoveryYearLayer]
    map.addMany(layersRef.current.vector)

    // 栅格图层
    const rasterConfigs = [
      { name: "disturbance_mask", title: "扰动区域 (栅格)" },
      { name: "disturbance_year", title: "扰动年份 (栅格)" },
      { name: "recovery_year", title: "恢复年份 (栅格)" },
    ]

    rasterConfigs.forEach(config => {
      const layer = new WebTileLayer({
        urlTemplate: `${baseUrl}/api/tiles/${jobId}/${config.name}/{level}/{col}/{row}.png`,
        title: config.title,
        visible: false,
        copyright: "Mining Detection Platform"
      })
      layersRef.current.raster.push(layer)
    })

    map.addMany(layersRef.current.raster)
    console.log('✓ 所有图层已添加到地图')

    // 保存图层引用到全局，供显示模式切换使用
    window.vectorLayers = layersRef.current.vector
    window.rasterLayers = layersRef.current.raster

    // 等待所有矢量图层加载完成后初始化 LayerList
    Promise.all([
      disturbanceMaskLayer.when(),
      disturbanceYearLayer.when(),
      recoveryYearLayer.when()
    ]).then(() => {
      console.log('✓ 所有矢量图层加载完成')

      // 延迟初始化 LayerList，确保 DOM 存在
      setTimeout(() => {
        const layerListDiv = document.getElementById("layerListDiv")
        if (layerListDiv && LayerList) {
          // 清空容器
          layerListDiv.innerHTML = ''
          layerListRef.current = new LayerList({
            view,
            container: layerListDiv
          })
          console.log('✓ LayerList 控件已初始化')
        }

        // 通知父组件图层已加载
        if (onLayersLoaded) {
          onLayersLoaded()
        }
      }, 100)
    }).catch(err => {
      console.warn('部分图层加载失败:', err)
    })

  }, [jobId, viewReady, onLayersLoaded])

  return (
    <div
      ref={mapRef}
      id="viewDiv"
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0
      }}
    />
  )
}

// 导出打开弹窗的辅助函数
export function openMapPopup(mapPoint, data) {
  const view = window.arcgisView
  if (!view) return

  view.popup.open({
    title: "像元信息",
    location: mapPoint,
    content: `
      <div style="font-size:12px;">
        <div><b>坐标:</b> ${data.lon.toFixed(6)}, ${data.lat.toFixed(6)}</div>
        <div><b>扰动年份:</b> <span style="color:#dc2626;font-weight:bold;">${data.disturbance_year ?? "无"}</span></div>
        <div><b>恢复年份:</b> <span style="color:#16a34a;font-weight:bold;">${data.recovery_year ?? "无"}</span></div>
        <div style="color:#666;margin-top:8px;border-top:1px solid #e5e7eb;padding-top:6px;">👈 左侧面板查看 NDVI 时间序列曲线</div>
      </div>
    `
  })
}
