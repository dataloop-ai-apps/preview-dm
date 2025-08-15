<template>
    <div class="meshContainer">
        <div ref="viewport" class="meshViewport"></div>
    </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, defineProps, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js'
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js'
import { TDSLoader } from 'three/examples/jsm/loaders/TDSLoader.js'

/* eslint-disable */
const props = defineProps<{
    url: string
    loading: boolean
    isBlackTheme?: boolean
    name?: string
}>()

const viewport = ref<HTMLDivElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let frameId: number | null = null
let rootObject: THREE.Object3D | null = null
let lastCenter: THREE.Vector3 | null = null
let lastMaxSize: number | null = null

const dispose = () => {
    if (frameId) cancelAnimationFrame(frameId)
    if (controls) controls.dispose()
    if (rootObject && scene) scene.remove(rootObject)
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
    rootObject = null
    lastCenter = null
    lastMaxSize = null
}

const getCssVarColor = (varName: string) => {
    let value = getComputedStyle(document.documentElement)
        .getPropertyValue(varName)
        .trim()
    // Normalize CSS color for three.js (drop alpha from hex/rgba)
    if (value.startsWith('#')) {
        if (value.length === 9) value = value.slice(0, 7)
        if (value.length === 5) value = `#${value[1]}${value[2]}${value[3]}`
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

const fitCameraToObject = (object: THREE.Object3D, factor = 1.1) => {
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

    lastCenter = center
    lastMaxSize = Math.max(maxSize, 1)
}

const animate = () => {
    if (!renderer || !scene || !camera) return
    if (controls) controls.update()
    renderer.render(scene, camera)
    frameId = requestAnimationFrame(animate)
}

const applyFallbackMaterials = (obj: THREE.Object3D) => {
    obj.traverse((child) => {
        // @ts-ignore
        const mesh = child as THREE.Mesh
        if (mesh && (mesh.isMesh || mesh.isLineSegments || mesh.isPoints)) {
            // If it's a mesh without material, give it a basic PBR material
            if ((mesh as any).isMesh && !mesh.material) {
                mesh.material = new THREE.MeshStandardMaterial({
                    color: getCssVarColor('--dl-color-darker'),
                    metalness: 0.0,
                    roughness: 0.9
                })
            }
            if ((mesh as any).isPoints) {
                const m = mesh.material as THREE.PointsMaterial
                if (
                    m &&
                    !(mesh.geometry as THREE.BufferGeometry).getAttribute(
                        'color'
                    )
                ) {
                    m.color.set(getCssVarColor('--dl-color-darker'))
                    m.needsUpdate = true
                }
            }
        }
    })
}

const init = () => {
    if (!viewport.value) return
    const width = viewport.value.clientWidth
    const height = viewport.value.clientHeight

    scene = new THREE.Scene()
    camera = new THREE.PerspectiveCamera(60, width / height, 0.01, 2000)
    camera.position.set(0, 0, 2)

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)
    viewport.value.appendChild(renderer.domElement)

    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true

    scene.add(new THREE.AmbientLight(0xffffff, 1))
    const dir = new THREE.DirectionalLight(0xffffff, 0.8)
    dir.position.set(2, 2, 3)
    scene.add(dir)

    const ext = (() => {
        const src = (props.name || props.url).split('?')[0].split('#')[0]
        const parts = src.toLowerCase().split('.')
        return parts.length > 1 ? parts.pop() || '' : ''
    })()

    const onLoaded = (obj: THREE.Object3D) => {
        rootObject = obj
        scene!.add(obj)
        applyFallbackMaterials(obj)
        fitCameraToObject(obj, 1.05)
        animate()
    }

    if (ext === 'glb' || ext === 'gltf') {
        const loader = new GLTFLoader()
        loader.load(
            props.url,
            (gltf) => onLoaded(gltf.scene || gltf.scenes[0]),
            undefined,
            (e) => console.error('GLTF load error', e)
        )
    } else if (ext === 'obj') {
        const loader = new OBJLoader()
        loader.load(
            props.url,
            (obj) => onLoaded(obj),
            undefined,
            (e) => console.error('OBJ load error', e)
        )
    } else if (ext === 'stl') {
        const loader = new STLLoader()
        loader.load(
            props.url,
            (geom) => {
                const mesh = new THREE.Mesh(
                    geom,
                    new THREE.MeshStandardMaterial({
                        color: getCssVarColor('--dl-color-darker'),
                        metalness: 0.0,
                        roughness: 0.9
                    })
                )
                onLoaded(mesh)
            },
            undefined,
            (e) => console.error('STL load error', e)
        )
    } else if (ext === 'ply') {
        const loader = new PLYLoader()
        loader.load(
            props.url,
            (geom) => {
                if (geom.getAttribute('normal') || geom.getIndex()) {
                    const mesh = new THREE.Mesh(
                        geom,
                        new THREE.MeshStandardMaterial({
                            vertexColors: !!geom.getAttribute('color'),
                            color: geom.getAttribute('color')
                                ? undefined
                                : getCssVarColor('--dl-color-darker'),
                            metalness: 0.0,
                            roughness: 0.9
                        })
                    )
                    onLoaded(mesh)
                } else {
                    const points = new THREE.Points(
                        geom,
                        new THREE.PointsMaterial({
                            size: 1,
                            vertexColors: !!geom.getAttribute('color'),
                            color: geom.getAttribute('color')
                                ? undefined
                                : getCssVarColor('--dl-color-darker')
                        })
                    )
                    onLoaded(points)
                }
            },
            undefined,
            (e) => console.error('PLY load error', e)
        )
    } else if (ext === 'fbx') {
        const loader = new FBXLoader()
        loader.load(
            props.url,
            (obj) => onLoaded(obj),
            undefined,
            (e) => console.error('FBX load error', e)
        )
    } else if (ext === '3ds') {
        const loader = new TDSLoader()
        loader.load(
            props.url,
            (obj) => onLoaded(obj),
            undefined,
            (e) => console.error('3DS load error', e)
        )
    } else {
        console.error('Unsupported mesh extension:', ext)
    }

    const onResize = () => {
        if (!renderer || !camera || !viewport.value) return
        const w = viewport.value.clientWidth
        const h = viewport.value.clientHeight
        renderer.setSize(w, h)
        camera.aspect = w / h
        camera.updateProjectionMatrix()
    }
    window.addEventListener('resize', onResize)
    ;(init as any)._onResize = onResize
}

const applyTheme = () => {
    if (rootObject) applyFallbackMaterials(rootObject)
}

watch(
    () => props.isBlackTheme,
    () => applyTheme()
)

onMounted(() => init())

onBeforeUnmount(() => {
    window.removeEventListener('resize', (init as any)._onResize)
    dispose()
})
/* eslint-enable */
</script>

<style lang="scss">
.meshContainer {
    width: 100vw;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--dl-color-bg);
}

.meshViewport {
    width: 100vw;
    height: 100vh;
    background: var(--dl-color-bg);
}

.meshViewport canvas {
    width: 100% !important;
    height: 100% !important;
    display: block;
}
</style>
