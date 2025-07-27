<template>
    <div class="usdz-viewer">
        <div v-if="loading" class="loading-container">
            <dl-spinner text="Loading 3D Model..." size="50px" />
        </div>
        <div v-else-if="error" class="error-container">
            <p>{{ error }}</p>
        </div>
        <div
            ref="containerRef"
            class="three-container"
            :style="{ display: loading ? 'none' : 'block' }"
        ></div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { USDZLoader } from 'three-usdz-loader'
import { DlSpinner } from '@dataloop-ai/components'

const props = defineProps<{
    url: string
    loading?: boolean
}>()

const containerRef = ref<HTMLElement>()
const loading = ref(true)
const error = ref('')

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let animationId: number
let model: THREE.Object3D

const initThreeJS = () => {
    if (!containerRef.value) return

    // Scene
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0xf0f0f0)

    // Camera
    camera = new THREE.PerspectiveCamera(
        75,
        containerRef.value.clientWidth / containerRef.value.clientHeight,
        0.1,
        1000
    )
    camera.position.set(0, 2, 5)

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(
        containerRef.value.clientWidth,
        containerRef.value.clientHeight
    )
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    containerRef.value.appendChild(renderer.domElement)

    // Lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(1, 1, 1)
    directionalLight.castShadow = true
    scene.add(directionalLight)

    // Mouse controls
    let isMouseDown = false
    let mouseX = 0
    let mouseY = 0

    const onMouseDown = (event: MouseEvent) => {
        isMouseDown = true
        mouseX = event.clientX
        mouseY = event.clientY
    }

    const onMouseUp = () => {
        isMouseDown = false
    }

    const onMouseMove = (event: MouseEvent) => {
        if (!isMouseDown || !model) return

        const deltaX = event.clientX - mouseX
        const deltaY = event.clientY - mouseY

        model.rotation.y += deltaX * 0.01
        model.rotation.x += deltaY * 0.01

        mouseX = event.clientX
        mouseY = event.clientY
    }

    renderer.domElement.addEventListener('mousedown', onMouseDown)
    renderer.domElement.addEventListener('mouseup', onMouseUp)
    renderer.domElement.addEventListener('mousemove', onMouseMove)
}

const loadModel = async () => {
    try {
        loading.value = true
        error.value = ''

        console.log('Parsing data URI...')
        const base64String = props.url.split(',')[1]
        const byteString = atob(base64String)
        const byteArray = new Uint8Array(byteString.length)
        for (let i = 0; i < byteString.length; i++) {
            byteArray[i] = byteString.charCodeAt(i)
        }
        const arrayBuffer = byteArray.buffer

        const blob = new Blob([arrayBuffer], {
            type: 'application/octet-stream'
        })
        const file = new File([blob], 'model.usdz', {
            type: 'application/octet-stream'
        })

        console.log('USDZ file ready, initializing loader...')

        // Initialize the USDZ loader with correct dependencies path
        // WebAssembly files are served from the public directory
        // Try without full URL to avoid DNS issues
        const loader = new USDZLoader('./')

        // Wait for the WebAssembly module to load
        const module = await loader.waitForModuleLoadingCompleted()
        if (!module) {
            throw new Error('Failed to load WebAssembly module')
        }

        console.log('WebAssembly module loaded, parsing USDZ...')

        // Create a group to hold the model
        const targetGroup = new THREE.Group()

        // Load the USDZ file
        const usdzInstance = await loader.loadFile(file, targetGroup)

        console.log('USDZ model loaded successfully')

        // Add the group to the scene
        scene.add(targetGroup)

        // Center and scale the model
        const box = new THREE.Box3().setFromObject(targetGroup)
        const center = box.getCenter(new THREE.Vector3())
        const size = box.getSize(new THREE.Vector3())

        // Center the model
        targetGroup.position.sub(center)

        // Scale the model to fit in viewport (max 3 units)
        const maxDim = Math.max(size.x, size.y, size.z)
        if (maxDim > 0) {
            const scale = 3 / maxDim
            targetGroup.scale.setScalar(scale)
        }

        // Enable shadows for all meshes in the model
        targetGroup.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
                child.castShadow = true
                child.receiveShadow = true
            }
        })

        model = targetGroup
        loading.value = false
    } catch (err) {
        console.error('Error loading USDZ file:', err)
        error.value = `Failed to load USDZ file: ${err.message}`
        loading.value = false

        // Fallback: Create a simple placeholder
        const geometry = new THREE.BoxGeometry(1, 1, 1)
        const material = new THREE.MeshPhongMaterial({
            color: 0xcccccc,
            shininess: 30
        })
        const cube = new THREE.Mesh(geometry, material)
        cube.castShadow = true
        cube.receiveShadow = true

        model = cube
        scene.add(model)
    }
}

const animate = () => {
    animationId = requestAnimationFrame(animate)

    // Auto-rotate the model
    if (model) {
        model.rotation.y += 0.005
    }

    renderer.render(scene, camera)
}

const handleResize = () => {
    if (!containerRef.value) return

    camera.aspect =
        containerRef.value.clientWidth / containerRef.value.clientHeight
    camera.updateProjectionMatrix()
    renderer.setSize(
        containerRef.value.clientWidth,
        containerRef.value.clientHeight
    )
}

onMounted(async () => {
    await new Promise((resolve) => setTimeout(resolve, 100))
    initThreeJS()
    await loadModel()
    animate()

    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    if (animationId) {
        cancelAnimationFrame(animationId)
    }

    if (renderer) {
        renderer.dispose()
    }

    window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.usdz-viewer {
    width: 100%;
    height: 500px;
    position: relative;
}

.loading-container,
.error-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    background-color: var(--dl-color-studio-panel);
    color: var(--dl-color-darker);
}

.three-container {
    width: 100%;
    height: 100%;
}

.three-container canvas {
    border-radius: 8px;
}

.error-container p {
    text-align: center;
    color: var(--dl-color-negative);
}
</style>
