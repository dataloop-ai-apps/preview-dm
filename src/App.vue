<template>
    <dl-theme-provider :is-dark="isDark">
        <div class="full-screen">
            <div v-if="loading && !errorState" class="loading-spinner">
                <dl-spinner text="Loading App..." size="100px" type="grid" />
            </div>

            <div v-else>
                <!-- Scenario 1: Preview service failed to load -->
                <div v-if="errorState === 'SERVICE_LOAD_FAILED'" class="error-container">
                    <div class="error-content">
                        <h2 class="error-title">Preview unavailable</h2>
                        <p class="error-body">The preview service couldn't be loaded.</p>
                        <button class="error-retry-button" @click="retryServiceLoad">
                            Retry
                        </button>
                    </div>
                </div>

                <!-- Scenario 2: File type not supported -->
                <div v-else-if="errorState === 'FILE_TYPE_NOT_SUPPORTED'" class="error-container">
                    <div class="error-content">
                        <div class="error-title-with-icon">
                            <Icon icon="mdi:file-alert" class="error-icon" />
                            <h2 class="error-title">File type not supported</h2>
                        </div>
                    </div>
                </div>

                <!-- Scenario 3: Unexpected preview failure -->
                <div v-else-if="errorState === 'PREVIEW_FAILED'" class="error-container">
                    <div class="error-content">
                        <h2 class="error-title">Preview unavailable</h2>
                        <p class="error-body">Something went wrong while generating the preview.</p>
                        <button class="error-retry-button" @click="retryPreview">
                            Retry
                        </button>
                    </div>
                </div>

                <!-- Normal message (no selection, multiple selection) -->
                <div v-else-if="message && !errorState" class="message">
                    {{ message }}
                </div>

                <!-- Normal preview -->
                <FloatingWindow
                    v-else-if="!message && !errorState"
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
import { Icon } from '@iconify/vue'
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
const errorState = ref(null) // 'SERVICE_LOAD_FAILED' | 'FILE_TYPE_NOT_SUPPORTED' | 'PREVIEW_FAILED'
const lastItemId = ref(null) // Store last item ID for retry

const isDark = computed(() => currentTheme.value === ThemeType.DARK)

const initializeApp = async () => {
    try {
        errorState.value = null
        loading.value = true
        await dl.init()
        dl.on(DlEvent.READY, async () => {
            try {
                const settings = await window.dl.settings.get()
                currentTheme.value = settings.theme
                dl.on(DlEvent.THEME, (data) => {
                    currentTheme.value = data
                })
                dl.on('items:selection:updated', async (data) => {
                    errorState.value = null
                    message.value = ''
                    if (data.length === 0) {
                        message.value = 'Select a single file to preview its content'
                        loading.value = false
                    } else if (data.length > 1) {
                        message.value = 'Select a single file to preview its content'
                        loading.value = false
                    } else {
                        await setItem(data[0])
                    }
                })
                loading.value = false
            } catch (error) {
                console.error('Error in READY handler:', error)
                errorState.value = 'SERVICE_LOAD_FAILED'
                loading.value = false
            }
        })
    } catch (error) {
        console.error('Error initializing preview service:', error)
        errorState.value = 'SERVICE_LOAD_FAILED'
        loading.value = false
    }
}

const retryServiceLoad = () => {
    initializeApp()
}

onMounted(() => {
    initializeApp()
})

const isUsdFile = (name) => {
    const validExts = ['.usd', '.usdz', '.usda', '.usdb']
    return validExts.some((ext) => name.toLowerCase().endsWith(ext))
}

const isOfficeFile = (name) => {
    const validExts = [
        '.doc',
        '.docx',
        '.rtf',
        '.odt',
        '.xls',
        '.xlsx',
        '.xlsm',
        '.xlsb',
        '.ods',
        '.ppt',
        '.pptx',
        '.odp'
    ]
    return validExts.some((ext) => name.toLowerCase().endsWith(ext))
}

const setItem = async (itemId) => {
    try {
        errorState.value = null
        loading.value = true
        lastItemId.value = itemId
        
        let item = await dl.items.get(itemId, {
            timeout: 10000
        })

        if (isUsdFile(item.name) || isOfficeFile(item.name)) {
            const previewModality = item.metadata.system?.modalities?.find(
                (m) => m.type === 'preview'
            )
            if (previewModality) {
                item = await dl.items.get(previewModality.ref, {
                    timeout: 10000
                })
            } else {
                var modalitytype = 'USD'
                if (isOfficeFile(item.name)) {
                    modalitytype = 'Office'
                }
                message.value =
                    'No preview modality found for ' + modalitytype + ' file'
                loading.value = false
                url.value = ''
                type.value = ''
                typeOfContent.value = ''
                return
            }
        }
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
            // Scenario 2: File type not supported
            errorState.value = 'FILE_TYPE_NOT_SUPPORTED'
            loading.value = false
            url.value = ''
            type.value = ''
            typeOfContent.value = ''
            return
        }
        
        // Try to stream the item - this can fail for supported types
        url.value = await dl.items.stream(item.stream, {
            timeout: 50000
        })
        type.value = mimetype
        // Normalize DICOM/PCD detection
        if (
            mimetype.includes('dicom') ||
            (item?.name && item.name.toLowerCase().endsWith('.dcm'))
        ) {
            typeOfContent.value = 'dicom'
        } else if (
            (item?.name && item.name.toLowerCase().endsWith('.pcd')) ||
            mimetype.includes('pcd')
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
        loading.value = false
    } catch (error) {
        console.error('Error loading preview:', error)
        // Scenario 3: Unexpected preview failure (supported type but something went wrong)
        errorState.value = 'PREVIEW_FAILED'
        loading.value = false
        url.value = ''
        type.value = ''
        typeOfContent.value = ''
    }
}

const retryPreview = () => {
    if (lastItemId.value) {
        setItem(lastItemId.value)
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
.error-container {
    display: grid;
    place-items: center;
    height: 100vh;
    width: 100%;
    background-color: var(--dl-color-studio-panel);
}
.error-content {
    text-align: center;
    max-width: 400px;
    padding: 2rem;
}
.error-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: var(--dl-color-darker);
}
.error-title-with-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 0;
}
.error-icon {
    font-size: 2rem;
    color: var(--dl-color-darker);
}
.error-body {
    font-size: 1rem;
    margin: 0 0 1.5rem 0;
    color: var(--dl-color-darker);
    opacity: 0.8;
}
.error-retry-button {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 500;
    background-color: var(--dl-color-primary, #007bff);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}
.error-retry-button:hover {
    background-color: var(--dl-color-primary-dark, #0056b3);
}
.error-retry-button:active {
    transform: scale(0.98);
}
</style>
