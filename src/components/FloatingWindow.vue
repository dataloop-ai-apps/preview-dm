<template>
    <div>
        <VideoComponent
            v-if="typeOfContent.includes('video')"
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
            @video-error="$emit('video-error')"
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
            @image-error="$emit('image-error')"
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
        <DICOMViewer
            v-else-if="typeOfContent.includes('dicom')"
            :url="url"
            :loading="loading"
            :is-black-theme="isBlackTheme"
        />
        <PCDViewer
            v-else-if="typeOfContent.includes('pcd')"
            :url="url"
            :loading="loading"
            :is-black-theme="isBlackTheme"
        />
        <MeshViewer
            v-else-if="typeOfContent.includes('mesh')"
            :url="url"
            :loading="loading"
            :is-black-theme="isBlackTheme"
            :name="name"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

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
    name?: string
}>()

const emit = defineEmits<{
    'image-error': []
    'video-error': []
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
        let metadataLoaded = false
        
        video.addEventListener('loadedmetadata', () => {
            metadataLoaded = true
            videoWidth.value = video.videoWidth
            videoHeight.value = video.videoHeight + 100
        })
        video.addEventListener('error', () => {
            emit('video-error')
        })
        video.src = props.url
        
        setTimeout(() => {
            if (!metadataLoaded && !videoWidth.value) {
                emit('video-error')
            }
        }, 10000)
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
