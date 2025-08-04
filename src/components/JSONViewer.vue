<template>
    <div v-if="!loading && jsonContent" class="json-viewer">
        <pre>{{ formattedJson }}</pre>
    </div>
    <div v-else-if="loading" class="content">Loading JSON...</div>
    <div v-else class="content">No JSON content found</div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps({
    url: {
        type: String,
        required: true
    },
    loading: Boolean
})

const jsonContent = ref<string | null>(null)
const formattedJson = ref<string>('')

const fetchJson = async () => {
    try {
        const response = await fetch(props.url)
        const data = await response.json()
        formattedJson.value = JSON.stringify(data, null, 2)
        jsonContent.value = formattedJson.value
    } catch (e) {
        formattedJson.value = 'Invalid JSON or failed to load.'
        jsonContent.value = null
    }
}

watch(() => props.url, fetchJson, { immediate: true })
</script>

export default {}

<style scoped>
.json-viewer {
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
