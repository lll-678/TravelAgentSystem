<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import type { Attraction } from '@/types'

interface Props {
  attractions: Attraction[]
  city?: string
}

const props = defineProps<Props>()

const mapContainer = ref<HTMLDivElement>()
let map: any = null  // AMap.Map 实例
let markers: any[] = []  // 存储标记

// 高德配置 - 替换成你自己的
const AMAP_KEY = '7f8da3bd5ec2b78beb8f679d07cb7339'
const AMAP_SECURITY_CODE = '50575f4fb19b0a9862155c6faa1ee39b'

// 配置安全密钥（必须）
window._AMapSecurityConfig = {
  securityJsCode: AMAP_SECURITY_CODE
}

// 预设城市中心坐标 [经度, 纬度]
const cityCenters: Record<string, [number, number]> = {
  '北京': [116.4074, 39.9042],
  '上海': [121.4737, 31.2304],
  '广州': [113.2644, 23.1291],
  '深圳': [114.0579, 22.5431],
  '杭州': [120.1551, 30.2741],
  '南京': [118.7969, 32.0603],
  '成都': [104.0668, 30.5728],
  '西安': [108.9398, 34.3416],
  '重庆': [106.5516, 29.5630],
  '武汉': [114.3054, 30.5931],
  '苏州': [120.5853, 31.2989],
  '天津': [117.2009, 39.0842],
}

// 初始化地图（只执行一次）
const initMap = () => {
  if (!mapContainer.value) return
  
  // 确定地图中心 [经度, 纬度]
  let center: [number, number] = [116.4074, 39.9042] // 默认北京
  if (props.city && cityCenters[props.city]) {
    center = cityCenters[props.city]
  } else if (props.attractions.length > 0 && props.attractions[0].location) {
    const loc = props.attractions[0].location
    center = [loc.longitude, loc.latitude]
  }
  
  AMapLoader.load({
    key: AMAP_KEY,
    version: '2.0',
    plugins: []  // 需要插件时可添加，如 'AMap.Scale', 'AMap.ToolBar'
  }).then((AMap) => {
    // 创建地图实例
    map = new AMap.Map(mapContainer.value, {
      center: center,
      zoom: 12,
      mapStyle: 'amap://styles/dark'  // 深色主题，可替换为 normal/light/whitesmoke
    })
    // 添加标记
    updateMarkers()
  }).catch((err) => {
    console.error('高德地图加载失败:', err)
  })
}

// 清除所有标记
const clearMarkers = () => {
  if (map && markers.length) {
    map.remove(markers)
    markers = []
  }
}

// 更新标记
const updateMarkers = () => {
  if (!map) return
  
  // 过滤有效景点
  const validAttractions = props.attractions.filter(
    a => a.location && typeof a.location.latitude === 'number' && typeof a.location.longitude === 'number'
  )
  
  if (validAttractions.length === 0) return
  
  // 清除旧标记
  clearMarkers()
  
  // 获取 AMap 对象（从已有地图实例获取）
  const AMap = (map as any).constructor
  
  // 用于计算视野的边界
  const bounds = new AMap.Bounds()
  
  // 添加新标记
  validAttractions.forEach((attraction, index) => {
    const { longitude, latitude } = attraction.location
    const position = new AMap.LngLat(longitude, latitude)
    
    // 创建自定义标记（使用高德的默认标记，可自定义样式）
    const marker = new AMap.Marker({
      position: position,
      title: attraction.name,
      label: {
        content: `<div style="background: #f97316; color: white; padding: 4px 8px; border-radius: 16px; font-size: 12px;">${index + 1}</div>`,
        offset: new AMap.Pixel(0, -30)
      }
    })
    
    // 绑定点击弹窗
    marker.on('click', () => {
      const infoWindow = new AMap.InfoWindow({
        content: `
          <div style="padding: 8px 12px;">
            <h4 style="margin: 0 0 8px 0; color: #333;">${attraction.name}</h4>
            <p style="margin: 0; color: #666; font-size: 12px;">${attraction.description || ''}</p>
          </div>
        `,
        offset: new AMap.Pixel(0, -30)
      })
      infoWindow.open(map, position)
    })
    
    marker.setMap(map)
    markers.push(marker)
    bounds.extend(position)
  })
  
  // 调整视野包含所有标记
  if (validAttractions.length > 1) {
    map.setBounds(bounds, false, false, [50, 50, 50, 50])
  }
}

// 监听景点变化
watch(() => props.attractions, () => {
  updateMarkers()
}, { deep: true })

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 320px;
  border-radius: 16px;
  overflow: hidden;
}
</style>