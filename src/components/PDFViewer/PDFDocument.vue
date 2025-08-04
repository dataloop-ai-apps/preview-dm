<template>
  <section
    class="overflow-hidden flex-1 bg-[#f1f5f9] grid transition-all duration-75 ease-in"
    :style="{ 'grid-template-columns': `${showSidebar ? '8rem' : '0rem'} 1fr` }"
  >
    <Suspense>
      <PDFSidebar
        class="transition-all duration-75 ease-in-out"
        :class="{ opacity: +showSidebar }"
      />
    </Suspense>
    <div class="relative">
      <div id="viewerContainer" ref="containerRef">
        <div id="viewer" class="pdfViewer"></div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { inject, onBeforeUnmount, onMounted, ref, toRaw, watch } from 'vue'
import {
  type EventBus,
  PDFViewer,
  type PDFLinkService,
} from 'pdfjs-dist/web/pdf_viewer'
import { PDFDocumentProxy } from 'pdfjs-dist'

const emit = defineEmits(['on-pdf-viewer-set'])
const props = defineProps({
  showSidebar: Boolean,
  pageScaleValue: {
    type: String,
    required: true,
  },
})

const pdf: PDFDocumentProxy = inject('pdf')
const eventBus: EventBus = inject('eventBus')
const pdfLinkService: PDFLinkService = inject('pdfLinkService')
const pdfFindController = inject('pdfFindController')

const containerRef = ref<HTMLDivElement>(null)
const pdfViewer = ref(null)
watch(
  () => props.pageScaleValue,
  (newValue) => {
    toRaw(pdfViewer.value).currentScaleValue = newValue
  }
)

const resizePdf = () => {
  const currentScaleValue = toRaw(pdfViewer.value).currentScaleValue

  if (!currentScaleValue) return

  toRaw(pdfViewer.value).refresh()

  if (
    currentScaleValue === 'auto' ||
    currentScaleValue === 'page-fit' ||
    currentScaleValue === 'page-width'
  ) {
    toRaw(pdfViewer.value).currentScaleValue = currentScaleValue
  }

  toRaw(pdfViewer.value).update()
}

onMounted(() => {
  window.addEventListener('resize', resizePdf)

  pdfViewer.value = new PDFViewer({
    container: containerRef.value,
    eventBus,
    linkService: pdfLinkService,
    findController: pdfFindController,
  })
  toRaw(pdfLinkService).setViewer(toRaw(pdfViewer.value))

  eventBus.on('pagesinit', () => {
    setTimeout(() => {
      toRaw(pdfViewer.value).currentScaleValue = 'auto'
    }, 0)
  })

  toRaw(pdfViewer.value).setDocument(toRaw(pdf.value))
  toRaw(pdfLinkService).setDocument(toRaw(pdf.value), null)
  emit('on-pdf-viewer-set', toRaw(pdfViewer.value))
})

onBeforeUnmount(() => window.removeEventListener('resize', resizePdf))
</script>

<style lang="scss">
#viewerContainer {
  @apply absolute overflow-auto inset-0 outline-0 transition-all duration-200 ease-in box-content;

  *,
  ::before,
  ::after {
    @apply box-content;
  }
}

@import url('./pdf_viewer.css');
</style>
