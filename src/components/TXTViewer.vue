<template>
    <dl-typography v-if="!loading && textContent" class="txt-viewer">
        <pre>{{ textContent }}</pre>
    </dl-typography>
    <dl-typography v-else-if="loading" class="content"
        >Loading text...</dl-typography
    >
    <dl-typography v-else class="content">No text content found</dl-typography>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { DlTypography } from '@dataloop-ai/components'

const props = defineProps({
    url: {
        type: String,
        required: true
    },
    loading: Boolean
})

const textContent = ref<string | null>(null)

const fetchText = async () => {
    try {
        const response = await fetch(props.url)
        textContent.value = await response.text()
    } catch (e) {
        textContent.value = 'Failed to load text.'
    }
}

watch(() => props.url, fetchText, { immediate: true })
</script>

export default {}

<style scoped>
.txt-viewer {
    background: var(--dl-color-bg);
    color: var(--dl-color-darker);
    padding: 1.5rem;
    border-radius: 0.5rem;
    font-family: 'Fira Mono', 'Consolas', monospace;
    font-size: 1rem;
    overflow-x: auto;
    max-width: 100vw;
    max-height: 100vh;
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
