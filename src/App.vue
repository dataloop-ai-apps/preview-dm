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
                    :set-is-open="(value) => (isOpen = value)"
                    :width="initialWidth"
                    :height="initialHeight"
                    :url="url"
                    :type="type"
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

const isDark = computed(() => currentTheme.value === ThemeType.DARK)

onMounted(async () => {
    console.log('onMounted')
    dl.on(DlEvent.READY, async () => {
        const settings = await dl.settings.get()
        currentTheme.value = settings.theme
        dl.on(DlEvent.THEME, (data) => {
            currentTheme.value = data
        })
        dl.on('items:selection:updated', async (data) => {
            console.log('SELECTION_UPDATED', data)
            message.value = ''
            if (data.length === 0) {
                message.value =
                    'Please select a single item without using the Select All option.'
            } else if (data.length > 1) {
                message.value =
                    'Please select a single item without using the Select All option.'
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
    const mimetype = item.metadata.system.mimetype
    const filename = item.name || ''

    // Check if it's a USDZ file (they often appear as application/zip)
    let actualMimetype = mimetype
    let actualTypeOfContent = mimetype

    if (
        mimetype === 'application/zip' &&
        filename.toLowerCase().endsWith('.usdz')
    ) {
        actualMimetype = 'application/usdz'
        actualTypeOfContent = 'usdz'
    }

    // Supported mimetypes based on FloatingWindow.vue
    const supported = [
        'video', // any video/*
        'image', // any image/*
        'pdf', // application/pdf
        'audio', // any audio/*
        'json', // application/json
        'plain', // text/plain
        'txt', // text/txt or similar
        'usdz' // USDZ 3D files
    ]

    // Check if mimetype is supported
    const isSupported = supported.some((type) =>
        actualTypeOfContent.includes(type)
    )
    if (!isSupported) {
        message.value = `This mimetype is not supported: ${mimetype}`
        loading.value = false
        url.value = ''
        type.value = ''
        typeOfContent.value = ''
        return
    }
    url.value = await dl.items.stream(item.stream, {
        timeout: 10000
    })
    type.value = actualMimetype
    typeOfContent.value = actualTypeOfContent
    // if mimetype is not supported, show a message
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
