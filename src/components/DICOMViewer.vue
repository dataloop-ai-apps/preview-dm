<template>
    <div v-if="!loading && url.length" class="dicomContainer">
        <div :ref="setDicomElement" class="dicomViewport"></div>
        <div v-if="dicomLoading" class="dicomOverlay">
            <dl-spinner text="Loading DICOM..." size="80px" type="grid" />
        </div>
        <div class="dicomHelp">
            <div class="infoIcon">i</div>
            <div class="panel">
                <div class="lines">
                    <div>
                        <b>Left drag</b>: Adjust brightness/contrast
                        (Window/Level)
                    </div>
                    <div><b>Right/Middle drag</b>: Move image (Pan)</div>
                    <div><b>Ctrl/Cmd + Wheel</b>: Zoom in/out</div>
                    <div><b>Wheel</b> or <b>Arrow keys</b>: Scroll frames</div>
                    <div><b>Double-click</b> or <b>R</b>: Reset view</div>
                    <div><b>I</b>: Invert colors</div>
                </div>
            </div>
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
const resetViewport = () => {
    if (!dicomElement) return
    try {
        const enabled = (cornerstone as any).getEnabledElement(dicomElement)
        const image = enabled?.image
        if (!image) return
        const defaultVp = (cornerstone as any).getDefaultViewportForImage(
            dicomElement,
            image
        )
        ;(cornerstone as any).setViewport(dicomElement, defaultVp)
    } catch (_) {
        // ignore
    }
}

// Wire externals for the WADO image loader (v2 approach works best with direct file URLs)
;(cornerstoneWADOImageLoader as any).external.cornerstone = cornerstone as any
;(cornerstoneWADOImageLoader as any).external.dicomParser = dicomParser as any
;(cornerstoneWADOImageLoader as any).external.cornerstoneMath =
    cornerstoneMath as any
// Register the metadata provider so multi-frame and other tags are available
// Remove custom provider registration to avoid runtime errors in this setup

const enableAndDisplay = async (fileUrl: string) => {
    if (!dicomElement) return
    try {
        dicomLoading.value = true
        // Prefer WADO-URI with HTTP Range for faster first-pixel; keep workers off to avoid bundler issues
        ;(cornerstoneWADOImageLoader as any).configure({
            useWebWorkers: false,
            retryAttempts: 0,
            strict: false,
            requestPoolSize: {
                decode: 1,
                retrieve: 6
            }
        })

        const element = dicomElement
        if (
            !(cornerstone as any).enabledElements?.find(
                (e: any) => e.element === element
            )
        ) {
            cornerstone.enable(element)
        }

        // Original approach: fetch the entire file, then use fileManager
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
        let stackImageIds: string[] =
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

        // Interaction: stack scroll, zoom, pan, WW/WL
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
            if (ev.ctrlKey || ev.metaKey) {
                // Zoom with wheel when holding Ctrl/Cmd
                const viewport = (cornerstone as any).getViewport(element)
                const zoomFactor = ev.deltaY > 0 ? 0.9 : 1.1
                viewport.scale = Math.max(
                    0.1,
                    Math.min(20, viewport.scale * zoomFactor)
                )
                ;(cornerstone as any).setViewport(element, viewport)
                return
            }
            const delta = ev.deltaY > 0 ? 1 : -1
            if (maxIndex > 0) renderIndex(currentIndex + delta)
        }

        // Window/Level (left-drag), Pan (right- or middle-drag)
        let isWwwc = false
        let isPanning = false
        let lastX = 0
        let lastY = 0

        const onMouseDown = (ev: MouseEvent) => {
            if (ev.button === 0) {
                isWwwc = true
            } else if (ev.button === 2 || ev.button === 1) {
                isPanning = true
            }
            lastX = ev.clientX
            lastY = ev.clientY
        }

        const onMouseMove = (ev: MouseEvent) => {
            if (!isWwwc && !isPanning) return
            const dx = ev.clientX - lastX
            const dy = ev.clientY - lastY
            lastX = ev.clientX
            lastY = ev.clientY

            const viewport = (cornerstone as any).getViewport(element)
            if (isWwwc) {
                const ww = viewport.voi?.windowWidth ?? 400
                const wc = viewport.voi?.windowCenter ?? 40
                const wwDelta = dx * 2
                const wcDelta = -dy * 2
                viewport.voi = {
                    windowWidth: Math.max(1, ww + wwDelta),
                    windowCenter: wc + wcDelta
                }
                ;(cornerstone as any).setViewport(element, viewport)
            } else if (isPanning) {
                viewport.translation = {
                    x: (viewport.translation?.x || 0) + dx,
                    y: (viewport.translation?.y || 0) + dy
                }
                ;(cornerstone as any).setViewport(element, viewport)
            }
        }

        const onMouseUp = () => {
            isWwwc = false
            isPanning = false
        }

        const onDblClick = () => {
            resetViewport()
        }

        const onContextMenu = (ev: MouseEvent) => {
            // Prevent native context menu to allow right-drag panning
            ev.preventDefault()
        }

        const onKeyDown = (ev: KeyboardEvent) => {
            if (ev.key === 'ArrowDown' || ev.key === 'ArrowRight') {
                renderIndex(currentIndex + 1)
            } else if (ev.key === 'ArrowUp' || ev.key === 'ArrowLeft') {
                renderIndex(currentIndex - 1)
            } else if (ev.key.toLowerCase() === 'i') {
                // Toggle invert
                const viewport = (cornerstone as any).getViewport(element)
                viewport.invert = !viewport.invert
                ;(cornerstone as any).setViewport(element, viewport)
            } else if (ev.key.toLowerCase() === 'r') {
                onDblClick()
            }
        }

        element.addEventListener('wheel', onWheel, { passive: false })
        element.addEventListener('mousedown', onMouseDown)
        element.addEventListener('mousemove', onMouseMove)
        window.addEventListener('mouseup', onMouseUp)
        element.addEventListener('dblclick', onDblClick)
        element.addEventListener('contextmenu', onContextMenu)
        window.addEventListener('keydown', onKeyDown)

        // Store cleanup on element for onBeforeUnmount
        ;(element as any).__stackCleanup__ = () => {
            element.removeEventListener('wheel', onWheel)
            element.removeEventListener('mousedown', onMouseDown)
            element.removeEventListener('mousemove', onMouseMove)
            window.removeEventListener('mouseup', onMouseUp)
            element.removeEventListener('dblclick', onDblClick)
            element.removeEventListener('contextmenu', onContextMenu)
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

.dicomHelp {
    position: fixed;
    left: 0;
    bottom: 0;
    pointer-events: auto;
}

.dicomHelp .infoIcon {
    pointer-events: auto;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-weight: 700;
    font-family:
        ui-sans-serif,
        system-ui,
        -apple-system,
        Segoe UI,
        Roboto,
        Helvetica,
        Arial,
        'Apple Color Emoji',
        'Segoe UI Emoji';
    color: #fff;
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid #ffffff33;
    cursor: default;
}

.dicomHelp .panel {
    position: absolute;
    left: 0;
    bottom: 32px;
    display: flex;
    gap: 12px;
    align-items: center;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    border-radius: 8px;
    padding: 10px 12px;
    backdrop-filter: blur(4px);
    width: max-content;
    opacity: 0;
    transform: translateY(4px);
    transition:
        opacity 120ms ease,
        transform 120ms ease;
    pointer-events: none;
}

.dicomHelp .panel .lines {
    font-size: 12px;
    line-height: 1.4;
}

.dicomHelp .panel .lines > div {
    white-space: nowrap;
}

.dicomHelp:hover .panel {
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
}
</style>
