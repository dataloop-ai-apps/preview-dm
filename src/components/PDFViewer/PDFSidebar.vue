<template>
  <aside ref="sidebarRef" class="pdf__sidebar bg-[#f9fbfc] overflow-auto">
    <div class="w-32 p-2 space-y-1">
      <button
        v-for="i in pdf?.numPages"
        ref="thumbsRef"
        :key="i"
        :data-page="i"
        :data-page-loaded="false"
        class="w-full rounded p-2 thumbWrapper"
        :class="[i === currentPage ? 'active' : '']"
        @click.stop.prevent="goToPage(i)"
      >
        <img
          class="w-full thumb-img border border-gray-200 rounded my-1"
          :style="{
            minHeight: THUMB_MIN_HEIGHT,
          }"
        />
        <p class="title text-xs font-medium text-gray-400">Page {{ i }}</p>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { inject, nextTick, onMounted, ref, toRaw } from 'vue'
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist'
import type {
  PDFLinkService,
  EventBus,
} from 'pdfjs-dist/types/web/pdf_link_service'

const THUMB_MIN_HEIGHT = '123px'

const pdfLinkService: PDFLinkService = inject('pdfLinkService')
const pdf: PDFDocumentProxy = inject('pdf')
const eventBus: EventBus = inject('eventBus')
const firstPagePromise = toRaw(pdf.value).getPage(1)
const viewport = ref(null)

await firstPagePromise.then((firstPdfPage) => {
  viewport.value = firstPdfPage.getViewport({ scale: 1 })
})

const currentPage = ref(pdfLinkService?.page || 1)
const sidebarRef = ref(null)
const thumbsRef = ref(null)

const observer = ref<IntersectionObserver>(null)

const renderPage = async (page: IntersectionObserverEntry) => {
  const {
    dataset: { page: pageId },
  } = page.target as HTMLElement
  const pdfPage: PDFPageProxy = await toRaw(pdf.value).getPage(parseInt(pageId))
  const canvas = document.createElement('canvas')
  const canvasContext = canvas.getContext('2d', { alpha: false })

  const renderContext = { canvasContext, viewport: toRaw(viewport.value) }
  canvas.height = toRaw(viewport.value).height
  canvas.width = toRaw(viewport.value).width

  const renderTask = pdfPage.render(renderContext).promise
  renderTask.then(() => {
    const src = canvas.toDataURL()
    const img = document.createElement('img')
    img.src = src
    thumbsRef.value[parseInt(pageId) - 1].firstChild.src = src

    // Zeroing the width and height causes Firefox to release graphics
    // resources immediately, which can greatly reduce memory consumption.
    canvas.width = 0
    canvas.height = 0
  })
}

const handleIntersect = (entries, observer) => {
  entries.forEach((entry: IntersectionObserverEntry) => {
    if (entry.isIntersecting) {
      const {
        dataset: { pageLoaded },
      } = entry.target
      const isPageLoaded = JSON.parse(pageLoaded)
      if (!isPageLoaded) {
        entry.target.setAttribute('data-page-loaded', 'true')
        renderPage(entry)
      }
    }
  })
}

const createInterserctionObserver = () => {
  const options: IntersectionObserverInit = {
    root: sidebarRef.value,
    rootMargin: '0px',
    threshold: 0,
  }
  observer.value = new IntersectionObserver(handleIntersect, options)
  for (let i = 0; i < pdf.value.numPages; i++) {
    observer.value.observe(toRaw(thumbsRef.value[i]))
  }
}

const goToPage = (page: number) => {
  pdfLinkService.goToPage(page)
  currentPage.value = page
}

const scrollToThumb = (page: number) => {
  thumbsRef.value[page].scrollIntoView()
}

onMounted(() => {
  createInterserctionObserver()
  eventBus.on('pagechanging', async ({ pageNumber }) => {
    await nextTick()
    if (pageNumber !== currentPage.value) {
      currentPage.value = pageNumber
      scrollToThumb(pageNumber - 1)
    }
  })
})
</script>

<style lang="scss" scoped>
.pdf__sidebar {
  /* IE and Edge */
  -ms-overflow-style: none;

  /* Firefox */
  scrollbar-width: none;

  /* Safari and Chrome */
  &::-webkit-scrollbar {
    display: none;
  }
}

.thumbWrapper:hover:not(.active) {
  @apply bg-blue-100;

  p.title {
    @apply text-blue-300;
  }
}
.active {
  @apply bg-blue-100;

  .thumb-img {
    @apply border-2 border-blue-500;
  }
  p.title {
    @apply text-blue-400;
  }
}
</style>
