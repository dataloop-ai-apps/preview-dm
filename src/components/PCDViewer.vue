<template>
    <div class="pcdContainer">
        <div ref="viewport" class="pcdViewport"></div>
    </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, defineProps, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { PCDLoader } from 'three/examples/jsm/loaders/PCDLoader.js'

/* eslint-disable */
const props = defineProps<{
    url: string
    loading: boolean
    isBlackTheme?: boolean
}>()

const viewport = ref<HTMLDivElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let frameId: number | null = null
let pointCloud: THREE.Points | null = null
let lastCenter: THREE.Vector3 | null = null
let lastMaxSize: number | null = null

const dispose = () => {
    if (frameId) cancelAnimationFrame(frameId)
    if (controls) controls.dispose()
    if (pointCloud && scene) scene.remove(pointCloud)
    if (renderer) {
        renderer.dispose()
        const canvas = renderer.domElement
        if (canvas && canvas.parentElement)
            canvas.parentElement.removeChild(canvas)
    }
    renderer = null
    controls = null
    scene = null
    camera = null

    pointCloud = null
    lastCenter = null
    lastMaxSize = null
}

const fitCameraToObject = (object: THREE.Object3D, factor = 2) => {
    if (!camera || !renderer) return
    const box = new THREE.Box3().setFromObject(object)
    const size = new THREE.Vector3()
    const center = new THREE.Vector3()
    box.getSize(size)
    box.getCenter(center)

    const maxSize = Math.max(size.x, size.y, size.z)
    const fitHeightDistance =
        maxSize / (2 * Math.atan((Math.PI * camera.fov) / 360))
    const fitWidthDistance = fitHeightDistance / camera.aspect
    const distance = factor * Math.max(fitHeightDistance, fitWidthDistance)

    camera.position.set(center.x, center.y, center.z + 2 * distance)
    camera.near = distance / 100
    camera.far = distance * 100
    camera.updateProjectionMatrix()

    if (controls) {
        controls.target.copy(center)
        controls.update()
    }
}

const animate = () => {
    if (!renderer || !scene || !camera) return
    if (controls) controls.update()
    renderer.render(scene, camera)
    frameId = requestAnimationFrame(animate)
}

const getCssVarColor = (varName: string) => {
    let value = getComputedStyle(document.documentElement)
        .getPropertyValue(varName)
        .trim()

    // Normalize CSS color for three.js (no alpha in hex)
    if (value.startsWith('#')) {
        if (value.length === 9) value = value.slice(0, 7) // #RRGGBBAA -> #RRGGBB
        if (value.length === 5) value = `#${value[1]}${value[2]}${value[3]}` // #RGBA -> #RGB
    } else if (value.startsWith('rgba')) {
        const parts = value
            .replace(/^rgba\(|\)$/g, '')
            .split(',')
            .map((p) => p.trim())
        value = `rgb(${parts[0]}, ${parts[1]}, ${parts[2]})`
    }

    const color = new THREE.Color()
    try {
        color.set(value || '#444')
    } catch (e) {
        color.set('#444')
    }
    return color
}

const init = () => {
    if (!viewport.value) return
    const width = viewport.value.clientWidth
    const height = viewport.value.clientHeight

    scene = new THREE.Scene()
    camera = new THREE.PerspectiveCamera(60, width / height, 0.01, 1000)
    camera.position.set(0, 0, 2)

    // Background follows app theme via CSS; keep renderer transparent
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)
    viewport.value.appendChild(renderer.domElement)

    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true

    const ambient = new THREE.AmbientLight(0xffffff, 1)
    scene.add(ambient)

    const loader = new PCDLoader()
    loader.load(
        props.url,
        (points) => {
            // Tweak point size a bit for visibility
            const material = points.material as THREE.PointsMaterial
            if (material) {
                material.size = material.size || 1
                material.sizeAttenuation = true
                const geom = points.geometry as THREE.BufferGeometry
                const hasColors = !!geom.getAttribute('color')
                if (!hasColors) {
                    material.vertexColors = false
                    material.color.set(getCssVarColor('--dl-color-darker'))
                }
            }

            pointCloud = points
            scene!.add(points)

            // Compute framing metrics relative to the point cloud
            const box = new THREE.Box3().setFromObject(points)
            const size = new THREE.Vector3()
            const center = new THREE.Vector3()
            box.getSize(size)
            box.getCenter(center)
            const maxSize = Math.max(size.x || 1, size.y || 1, size.z || 1)
            lastCenter = center.clone()
            lastMaxSize = maxSize

            fitCameraToObject(points, 1)
            animate()
            // Apply theme-driven colors in case theme is dark
            applyTheme()
        },
        undefined,
        (err) => {
            // eslint-disable-next-line no-console
            console.error('Failed to load PCD:', err)
        }
    )

    const onResize = () => {
        if (!renderer || !camera || !viewport.value) return
        const w = viewport.value.clientWidth
        const h = viewport.value.clientHeight
        renderer.setSize(w, h)
        camera.aspect = w / h
        camera.updateProjectionMatrix()
    }
    window.addEventListener('resize', onResize)

    // store for cleanup
    ;(init as any)._onResize = onResize
}

const applyTheme = () => {
    // Update fallback material color (no per-point colors)
    if (pointCloud) {
        const material = pointCloud.material as THREE.PointsMaterial
        const geom = pointCloud.geometry as THREE.BufferGeometry
        const hasColors = !!geom.getAttribute('color')
        if (material && !hasColors) {
            material.color.set(getCssVarColor('--dl-color-darker'))
            material.needsUpdate = true
        }
    }

    // No grid; only adjust materials on theme change
}

watch(
    () => props.isBlackTheme,
    () => {
        applyTheme()
    }
)

onMounted(() => {
    init()
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', (init as any)._onResize)
    dispose()
})
/* eslint-enable */
</script>

<style lang="scss">
.pcdContainer {
    width: 100vw;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--dl-color-bg);
}

.pcdViewport {
    width: 100vw;
    height: 100vh;
    background: var(--dl-color-bg);
}

.pcdViewport canvas {
    width: 100% !important;
    height: 100% !important;
    display: block;
}
</style>
