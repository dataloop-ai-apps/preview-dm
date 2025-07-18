<template>
  <PDFViewer v-if="!loading && url.length" :url="url" />
  <div v-if="!url.length" class="content">No media found</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import PDFViewer from './PDFViewer/PDFViewer.vue'

defineProps({
  url: {
    type: String,
    required: true,
  },
  loading: Boolean,
})

const width = ref(window.innerWidth)
const height = ref(window.innerHeight)

const onResize = () => {
  width.value = window.innerWidth
  height.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
})
</script>
