<template>
    <div v-if="!loading && url.length" class="imageContainer">
        <img
            :src="url"
            ref="imgElem"
            @mousedown="handleMouseDown"
            @mouseup="handleMouseUp"
            @mousemove="handleMouseMove"
            @wheel="handleWheel"
        />
    </div>
    <div v-if="!url.length" class="content">No media found</div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

/* eslint-disable */
defineProps([
    'setIsOpen',
    'isBlackTheme',
    'url',
    'loading',
    'top',
    'right',
    'width',
    'height',
    'imgWidth',
    'imgHeight'
])
const panning = ref(false)
const imgElem = ref<HTMLImageElement>()
const coords = reactive({ x: 0, y: 0, scale: 1 })
let start = { x: 0, y: 0 }

const handleMouseDown = (e: MouseEvent) => {
    e.preventDefault()
    if (imgElem.value) imgElem.value.style.cursor = 'grabbing'

    start.x = e.clientX - coords.x
    start.y = e.clientY - coords.y
    panning.value = true
}
const handleMouseUp = (e: MouseEvent) => {
    e.preventDefault()
    if (imgElem.value) imgElem.value.style.cursor = 'grab'
    panning.value = false
}

const handleMouseMove = (e: MouseEvent) => {
    e.preventDefault()
    if (!panning.value === true) return
    coords.x = e.clientX - start.x
    coords.y = e.clientY - start.y
}

const handleWheel = (e: WheelEvent) => {
    e.preventDefault()
    const xs = (e.clientX - coords.x) / coords.scale
    const ys = (e.clientY - coords.y) / coords.scale

    e.deltaY < 0 ? (coords.scale *= 1.2) : (coords.scale /= 1.2)

    coords.x = e.clientX - xs * coords.scale
    coords.y = e.clientY - ys * coords.scale
}

watch(coords, () => {
    if (imgElem.value)
        imgElem.value.style.transform =
            'translate(' +
            coords.x +
            'px, ' +
            coords.y +
            'px) scale(' +
            coords.scale +
            ')'
})

/* eslint-enable */
</script>

export default {}

<style lang="scss">
.imageContainer {
    overflow: auto;
    background: var(--dl-color-studio-panel);
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;

    img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        transform-origin: center center;
        transform: scale(1) translate(0px, 0px);
        cursor: grab;
    }
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
