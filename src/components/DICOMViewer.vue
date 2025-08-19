<template>
    <div v-if="!loading && url.length" class="dicomContainer">
        <div :ref="setDicomElement" class="dicomViewport"></div>
        <div v-if="dicomLoading" class="dicomOverlay">
            <dl-spinner text="Loading DICOM..." size="80px" type="grid" />
        </div>
    </div>
    <div v-else class="content">No media found</div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, defineProps } from 'vue'
import cornerstone from 'cornerstone-core'
import cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader'
import dicomParser from 'dicom-parser'
import cornerstoneMath from 'cornerstone-math'
import { DlSpinner } from '@dataloop-ai/components'

/* eslint-disable */
const props = defineProps<{
    url: string
    loading: boolean
    isBlackTheme?: boolean
}>()

let dicomElement: HTMLDivElement | null = null
const setDicomElement = (el: HTMLDivElement | null) => {
    dicomElement = el
}
const dicomLoading = ref<boolean>(false)

// Wire externals for the WADO image loader (v2 approach works best with direct file URLs)
;(cornerstoneWADOImageLoader as any).external.cornerstone = cornerstone as any
;(cornerstoneWADOImageLoader as any).external.dicomParser = dicomParser as any
;(cornerstoneWADOImageLoader as any).external.cornerstoneMath =
    cornerstoneMath as any

const enableAndDisplay = async (fileUrl: string) => {
    if (!dicomElement) return
    try {
        dicomLoading.value = true
        // Keep it simple: avoid extra worker/network requests and retries
        ;(cornerstoneWADOImageLoader as any).configure({
            useWebWorkers: false,
            retryAttempts: 0
        })

        const element = dicomElement
        if (
            !(cornerstone as any).enabledElements?.find(
                (e: any) => e.element === element
            )
        ) {
            cornerstone.enable(element)
        }

        // Fetch the DICOM once, then hand bytes to the loader (prevents multiple failed range requests)
        const response = await fetch(fileUrl)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const buffer = await response.arrayBuffer()
        const blob = new Blob([buffer], { type: 'application/dicom' })
        const file = new File([blob], 'image.dcm', {
            type: 'application/dicom'
        })

        // Determine number of frames from the DICOM header
        let numberOfFrames = 1
        try {
            const byteArray = new Uint8Array(buffer)
            const dataSet = (dicomParser as any).parseDicom(byteArray)
            const framesStr = dataSet?.string?.('x00280008')
            numberOfFrames = Math.max(1, parseInt(framesStr || '1', 10))
        } catch (_) {
            numberOfFrames = 1
        }

        // Create imageIds for each frame (frame indices are zero-based)
        const baseImageId = (
            cornerstoneWADOImageLoader as any
        ).wadouri.fileManager.add(file)
        const stackImageIds: string[] =
            numberOfFrames > 1
                ? Array.from(
                      { length: numberOfFrames },
                      (_, i) => `${baseImageId}?frame=${i}`
                  )
                : [baseImageId]

        // Render first frame
        const image = await (cornerstone as any).loadAndCacheImage(
            stackImageIds[0]
        )
        const viewport = (cornerstone as any).getDefaultViewportForImage(
            element,
            image
        )
        ;(cornerstone as any).displayImage(element, image, viewport)
        dicomLoading.value = false

        // Wire simple stack scrolling with mouse wheel and keyboard arrows
        let currentIndex = 0
        const maxIndex = stackImageIds.length - 1

        const renderIndex = async (newIndex: number) => {
            currentIndex = Math.max(0, Math.min(maxIndex, newIndex))
            const img = await (cornerstone as any).loadAndCacheImage(
                stackImageIds[currentIndex]
            )
            ;(cornerstone as any).displayImage(element, img)
        }

        const onWheel = (ev: WheelEvent) => {
            ev.preventDefault()
            const delta = ev.deltaY > 0 ? 1 : -1
            renderIndex(currentIndex + delta)
        }

        const onKeyDown = (ev: KeyboardEvent) => {
            if (ev.key === 'ArrowDown' || ev.key === 'ArrowRight') {
                renderIndex(currentIndex + 1)
            } else if (ev.key === 'ArrowUp' || ev.key === 'ArrowLeft') {
                renderIndex(currentIndex - 1)
            }
        }

        element.addEventListener('wheel', onWheel, { passive: false })
        window.addEventListener('keydown', onKeyDown)

        // Store cleanup on element for onBeforeUnmount
        ;(element as any).__stackCleanup__ = () => {
            element.removeEventListener('wheel', onWheel)
            window.removeEventListener('keydown', onKeyDown)
            delete (element as any).__stackCleanup__
        }
    } catch (err: any) {
        // eslint-disable-next-line no-console
        console.error('[DICOMViewer] Failed to load via WADO-URI', {
            message: err?.message,
            name: err?.name,
            stack: err?.stack
        })
        dicomLoading.value = false
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
    if (dicomElement) {
        try {
            if ((dicomElement as any).__stackCleanup__) {
                ;(dicomElement as any).__stackCleanup__()
            }
            cornerstone.disable(dicomElement)
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

.dicomOverlay {
    position: fixed;
    inset: 0;
    display: grid;
    place-items: center;
    background: rgba(0, 0, 0, 0.25);
    pointer-events: none;
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
