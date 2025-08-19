<template>
    <dl-theme-provider :is-dark="isDark">
        <div class="full-screen">
            <div v-if="loading" class="loading-spinner">
                <dl-spinner text="Loading App..." size="100px" type="grid" />
            </div>

            <div v-else>
                <div v-if="message" class="message">
                    {{ message }}
                </div>
                <FloatingWindow
                    v-if="!message"
                    :loading="loading"
                    :type-of-content="typeOfContent"
                    :is-black-theme="isDark"
                    :set-is-open="(value) => (isOpen = value)"
                    :width="initialWidth"
                    :height="initialHeight"
                    :url="url"
                    :type="type"
                    :name="fileName"
                />
            </div>
        </div>
    </dl-theme-provider>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue-demi'
import FloatingWindow from './components/FloatingWindow.vue'
import { DlEvent, ThemeType } from '@dataloop-ai/jssdk'
import { DlThemeProvider, DlSpinner } from '@dataloop-ai/components'

defineProps({
    msg: {
        type: String,
        default: ''
    }
})

const isOpen = ref(false)
const loading = ref(true)
const typeOfContent = ref('image')
const initialWidth = null
const initialHeight = null
const type = ref('image/png')
const url = ref('')
const currentTheme = ref(ThemeType.LIGHT)
const message = ref('')
const fileName = ref('')

const isDark = computed(() => currentTheme.value === ThemeType.DARK)

onMounted(async () => {
    console.log('onMounted')
    await dl.init()
    dl.on(DlEvent.READY, async () => {
        const settings = await window.dl.settings.get()
        currentTheme.value = settings.theme
        dl.on(DlEvent.THEME, (data) => {
            currentTheme.value = data
        })
        dl.on('items:selection:updated', async (data) => {
            console.log('SELECTION_UPDATED', data)
            message.value = ''
            if (data.length === 0) {
                message.value = 'Select a single file to preview its content'
            } else if (data.length > 1) {
                message.value = 'Select a single file to preview its content'
            } else {
                await setItem(data[0])
            }
            loading.value = false
        })
    })
})

const setItem = async (itemId) => {
    loading.value = true
    const item = await dl.items.get(itemId, {
        timeout: 10000
    })
    fileName.value = item?.name || ''

    const mimetype = item.metadata.system.mimetype || ''
    // Supported types based on FloatingWindow.vue
    const supportedMimes = [
        'video', // any video/*
        'image', // any image/*
        'pdf', // application/pdf
        'audio', // any audio/*
        'json', // application/json
        'plain', // text/plain
        'txt', // text/txt or similar
        'dicom', // application/dicom, image/dicom, or similar
        'pcd' // point cloud
    ]
    const supportedExts = [
        '.pcd',
        '.glb',
        '.gltf',
        '.obj',
        '.stl',
        '.ply',
        '.fbx',
        '.3ds'
    ]
    const lowerName = (item?.name || '').toLowerCase()

    // Check if mimetype or extension is supported
    const isSupported =
        supportedMimes.some((type) => mimetype?.includes(type)) ||
        supportedExts.some((ext) => lowerName.endsWith(ext))
    if (!isSupported) {
        const supportedList =
            'images, videos, audio, pdf, json, txt, dicom, pcd, glb/gltf/obj/stl/ply/fbx/3ds'
        message.value = `This file type is not supported. Name: ${item?.name || '(unknown)'} | Mimetype: ${mimetype}. Supported: ${supportedList}.`
        loading.value = false
        url.value = ''
        type.value = ''
        typeOfContent.value = ''
        return
    }
    url.value = await dl.items.stream(item.stream, {
        timeout: 50000
    })
    type.value = mimetype
    // Normalize DICOM/PCD detection
    if (
        mimetype.includes('dicom') ||
        mimetype === 'application/dicom' ||
        mimetype === 'application/dicom+json'
    ) {
        typeOfContent.value = 'dicom'
    } else if (
        (item?.name && item.name.toLowerCase().endsWith('.pcd')) ||
        mimetype.includes('pcd') ||
        mimetype === 'application/pcd'
    ) {
        typeOfContent.value = 'pcd'
    } else if (item?.name) {
        const name = item.name.toLowerCase()
        if (
            name.endsWith('.glb') ||
            name.endsWith('.gltf') ||
            name.endsWith('.obj') ||
            name.endsWith('.stl') ||
            name.endsWith('.ply') ||
            name.endsWith('.fbx') ||
            name.endsWith('.3ds')
        ) {
            typeOfContent.value = 'mesh'
        } else {
            typeOfContent.value = mimetype
        }
    } else {
        typeOfContent.value = mimetype
    }
}
</script>

<style scoped>
.loading-spinner {
    display: grid;
    place-items: center;
    height: 100vh;
    background-color: var(--dl-color-studio-panel);
    color: var(--dl-color-darker);
}
.content {
    display: grid;
    width: 100%;
    height: 100%;
    place-items: center;
}
.message {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: var(--dl-color-darker);
}
</style>
