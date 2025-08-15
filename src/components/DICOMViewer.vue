<template>
    <div v-if="!loading && url.length" class="dicomContainer">
        <div ref="dicomElement" class="dicomViewport"></div>
    </div>
    <div v-else class="content">No media found</div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, defineProps } from 'vue'
import cornerstone from 'cornerstone-core'
import cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader'
import dicomParser from 'dicom-parser'
import cornerstoneMath from 'cornerstone-math'

/* eslint-disable */
const props = defineProps<{
    url: string
    loading: boolean
    isBlackTheme?: boolean
}>()

const dicomElement = ref<HTMLDivElement | null>(null)

// Wire externals for the WADO image loader
cornerstoneWADOImageLoader.external.cornerstone = cornerstone as any
cornerstoneWADOImageLoader.external.dicomParser = dicomParser as any
cornerstoneWADOImageLoader.external.cornerstoneMath = cornerstoneMath as any

const enableAndDisplay = async (url: string) => {
    if (!dicomElement.value) return

    try {
        // Simpler setup: disable web workers to avoid bundler worker wiring
        cornerstoneWADOImageLoader.configure({ useWebWorkers: false })

        const element = dicomElement.value
        if (
            !(cornerstone as any).enabledElements?.find(
                (e: any) => e.element === element
            )
        ) {
            cornerstone.enable(element)
        }

        const imageId = `wadouri:${url}`
        const image = await cornerstone.loadAndCacheImage(imageId)
        const viewport = cornerstone.getDefaultViewportForImage(element, image)
        cornerstone.displayImage(element, image, viewport)
    } catch (e) {
        // eslint-disable-next-line no-console
        console.error('Failed to display DICOM', e)
    }
}

onMounted(() => {
    if (props?.url) enableAndDisplay(props.url)

    watch(
        () => props.url,
        (newUrl) => {
            if (newUrl) enableAndDisplay(newUrl)
        }
    )
})

onBeforeUnmount(() => {
    if (dicomElement.value) {
        try {
            cornerstone.disable(dicomElement.value)
        } catch (_) {
            // ignore
        }
    }
})
/* eslint-enable */
</script>

<style lang="scss">
.dicomContainer {
    overflow: hidden;
    background: var(--dl-color-bg);
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.dicomViewport {
    width: 100vw;
    height: 100vh;
    background-color: var(--dl-color-bg);
}

.dicomViewport canvas {
    background-color: var(--dl-color-bg) !important;
}

.content {
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    align-self: center;
}
</style>
