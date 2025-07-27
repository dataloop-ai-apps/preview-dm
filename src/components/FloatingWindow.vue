<template>
    <div>
        <VideoComponent
            v-if="
                (typeOfContent.includes('video') &&
                    videoHeight &&
                    videoWidth) ||
                (typeOfContent.includes('video') && width && height)
            "
            :set-is-open="setIsOpen"
            :is-black-theme="isBlackTheme"
            :url="url"
            :top="top"
            :right="right"
            :type="type"
            :width="width"
            :height="height"
            :video-width="videoWidth"
            :video-height="videoHeight"
        />
        <ImageComponent
            v-else-if="typeOfContent.includes('image')"
            :set-is-open="setIsOpen"
            :loading="loading"
            :url="url"
            :top="top"
            :right="right"
            :width="width"
            :height="height"
            :img-width="imgWidth"
            :img-height="imgHeight"
        />
        <PDFComponent
            v-else-if="typeOfContent.includes('pdf')"
            :url="url"
            :loading="loading"
        />
        <AudioComponent
            v-else-if="
                typeOfContent.includes('audio') && !loading && url.length
            "
            :url="url"
        />
        <JSONViewer
            v-else-if="typeOfContent.includes('json')"
            :url="url"
            :loading="loading"
        />
        <TXTViewer
            v-else-if="
                typeOfContent.includes('plain') || typeOfContent.includes('txt')
            "
            :url="url"
            :loading="loading"
        />
        <USDZComponent
            v-else-if="typeOfContent.includes('usdz')"
            :url="url"
            :loading="loading"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import VideoComponent from './VideoComponent.vue'
import ImageComponent from './ImageComponent.vue'
import PDFComponent from './PDFComponent.vue'
import AudioComponent from './AudioComponent.vue'
import JSONViewer from './JSONViewer.vue'
import TXTViewer from './TXTViewer.vue'
import USDZComponent from './USDZComponent.vue'

const props = defineProps<{
    setIsOpen: (value: boolean) => void
    loading: boolean
    isBlackTheme?: boolean
    url: string
    top?: number
    right?: number
    type: string
    typeOfContent: string
    width?: number
    height?: number
}>()

const imgWidth = ref<number | null>(null)
const imgHeight = ref<number | null>(null)
const videoWidth = ref<number | null>(null)
const videoHeight = ref<number | null>(null)

onMounted(() => {
    if (
        props.typeOfContent.includes('video') &&
        !props.width &&
        !props.height
    ) {
        const video = document.createElement('video')
        video.addEventListener('loadedmetadata', () => {
            videoWidth.value = video.videoWidth
            videoHeight.value = video.videoHeight + 100
        })
        video.src = props.url
    } else if (
        props.typeOfContent.includes('image') &&
        !props.width &&
        !props.height
    ) {
        const img = new Image()
        img.onload = () => {
            imgWidth.value = img.naturalWidth
            imgHeight.value = img.naturalHeight
        }
        img.src = props.url
    }
})
</script>
