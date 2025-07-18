<template>
  <nav
    class="relative flex items-center justify-between shadow-md gap-1 p-1 z-40"
  >
    <!-- left side -->
    <div class="flex md:w-1/3 items-center gap-x-2">
      <button
        class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90 text-gray-500"
        :class="{ 'bg-sky-100': showSidebar }"
        @click="$emit('on-toggle-sidebar')"
      >
        <i-fluent-panel-left-48-regular class="w-5 h-5" />
      </button>

      <div class="flex items-center">
        <button
          class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 enabled:active:scale-90 text-gray-500 disabled:opacity-75 disabled:cursor-default"
          :disabled="inputValue === 1"
          @click="$emit('on-page-prev')"
        >
          <i-carbon-chevron-up class="w-5 h-5" />
        </button>
        <button
          class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 enabled:active:scale-90 text-gray-500 disabled:opacity-75 disabled:cursor-default"
          :disabled="inputValue === numPages"
          @click="$emit('on-page-next')"
        >
          <i-carbon-chevron-down class="w-5 h-5" />
        </button>
        <div class="flex items-center ml-2">
          <input
            :value="inputValue"
            type="number"
            min="1"
            :max="numPages"
            class="text-gray-600 appearance-none m-0 w-14 text-sm text-center border-2 rounded"
            @focus="(e) => (e.target as HTMLInputElement).select()"
            @change.prevent.stop="changeInputValue"
          />
          <span class="text-gray-600 font-thin ml-2 text-sm whitespace-nowrap"
            >of {{ numPages }}</span
          >
        </div>
      </div>

      <div class="flex items-center ml-2 gap-1">
        <button
          class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 enabled:active:scale-90 text-gray-500 disabled:opacity-75 disabled:cursor-default"
          :disabled="pageZoom === MIN_SCALE"
          @click="emit('on-zoom-out')"
        >
          <i-carbon-zoom-out />
        </button>

        <button
          class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 enabled:active:scale-90 text-gray-500 disabled:opacity-75 disabled:cursor-default"
          :disabled="pageZoom === MAX_SCALE"
          @click="emit('on-zoom-in')"
        >
          <i-carbon-zoom-in />
        </button>
        <button
          v-if="pageScaleValue === 'page-fit'"
          class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90 text-gray-500"
          @click="$emit('on-page-scale-change', 'page-width')"
        >
          <i-carbon-fit-to-width />
        </button>

        <button
          v-else
          class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90 text-gray-500"
          @click="$emit('on-page-scale-change', 'page-fit')"
        >
          <i-carbon-fit-to-screen />
        </button>
      </div>
    </div>

    <!-- center -->
    <div class="md:w-1/3 hidden lg:flex justify-center">
      <p
        class="text-center font-medium text-gray-700 text-md truncate"
        :title="title"
      >
        {{ title }}
      </p>
    </div>

    <!-- rigth side -->
    <div class="flex md:w-1/3 items-center justify-end gap-x-2">
      <button
        class="relative p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90 text-gray-500"
        :class="{ 'bg-sky-100': showSearch }"
        @click.stop.prevent="toggleSearch"
      >
        <i-carbon-search />
      </button>
      <a
        class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90 text-gray-500"
        :href="title"
        download
      >
        <i-carbon-download />
      </a>
    </div>

    <div
      v-show="showSearch"
      class="bg-white p-1 px-2 z-40 shadow-xl rounded absolute top-full border right-0"
    >
      <div class="flex flex-col space-y-1 py-1">
        <div class="space-x-2 flex items-center">
          <button
            class="text-xs bg-gray-50 p-1 px-2 rounded text-gray-600 select-none transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90"
            :class="{ 'bg-sky-100 hover:bg-sky-100': highlightAll }"
            @click="highlightAll = !highlightAll"
          >
            Highlight All
          </button>
          <button
            class="text-xs bg-gray-50 p-1 px-2 rounded text-gray-600 select-none transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90"
            :class="{ 'bg-sky-100 hover:bg-sky-100': matchCase }"
            @click="matchCase = !matchCase"
          >
            Match Case
          </button>
          <button
            class="text-xs bg-gray-50 p-1 px-2 rounded text-gray-600 select-none transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90"
            :class="{ 'bg-sky-100 hover:bg-sky-100': matchDiacritics }"
            @click="matchDiacritics = !matchDiacritics"
          >
            Match Diacritics
          </button>
          <button
            class="text-xs bg-gray-50 p-1 px-2 rounded text-gray-600 select-none transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90"
            :class="{ 'bg-sky-100 hover:bg-sky-100': wholeWords }"
            @click="wholeWords = !wholeWords"
          >
            Whole Words
          </button>
        </div>
        <div class="flex flex-row gap-1">
          <div class="relative w-full">
            <input
              id="search"
              ref="searchInput"
              v-model="searchText"
              type="text"
              class="w-full border-2 border-sky-500 focus:outline-none rounded px-1"
              placeholder="Find in document..."
              @input="findString"
              @keyup.enter="onEnter"
            />
            <div
              v-if="searchText"
              class="absolute inset-y-0 right-2 my-1 text-xs text-gray-500"
            >
              <div
                v-if="
                  findState === FindState.FOUND ||
                  findState === FindState.WRAPPED
                "
                class="bg-green-100 w-full h-full flex items-center rounded px-2 text-green-400"
              >
                <span> {{ matchesCurrent }} of {{ matchesCountTotal }} </span>
              </div>
              <div
                v-else-if="findState === FindState.NOT_FOUND"
                class="bg-red-100 w-full h-full flex items-center rounded px-2 text-red-400"
              >
                <span>Phrase not found</span>
              </div>
              <div
                v-else-if="findState === FindState.PENDING"
                class="bg-amber-100 w-full h-full flex items-center rounded px-2 text-amber-500"
              >
                Loading
              </div>
            </div>
          </div>
          <button
            class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90 text-gray-500"
            @click="findPrev"
          >
            <i-carbon-chevron-up class="w-5 h-5" />
          </button>
          <button
            class="p-1 rounded transition-all duration-75 ease-in hover:bg-gray-200 active:scale-90 text-gray-500"
            @click="findNext"
          >
            <i-carbon-chevron-down class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import type { EventBus, PDFLinkService } from 'pdfjs-dist/web/pdf_viewer'
import {
  computed,
  inject,
  nextTick,
  onMounted,
  onBeforeUnmount,
  ref,
  watch,
} from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },

  numPages: {
    type: Number,
    required: true,
    default: 1,
  },
  showSidebar: Boolean,
  pageScaleValue: {
    type: String,
    required: true,
    validator: (value: string) => {
      return ['page-width', 'page-fit'].includes(value)
    },
  },
  pageZoom: {
    type: Number,
    required: true,
    default: 1,
    validator: (value: number) => {
      return value >= 0.1 && value <= 10
    },
  },
})

const emit = defineEmits([
  'on-zoom-in',
  'on-zoom-out',
  'on-page-prev',
  'on-page-next',
  'on-page-change',
  'on-toggle-sidebar',
  'on-page-scale-change',
])

const pdfLinkService: PDFLinkService = inject('pdfLinkService')
const eventBus: EventBus = inject('eventBus')

const MIN_SCALE = 0.1
const MAX_SCALE = 10
const FindState = {
  FOUND: 0,
  NOT_FOUND: 1,
  WRAPPED: 2,
  PENDING: 3,
}

const inputValue = ref(1)
const showSearch = ref(false)
const searchText = ref('')

const matchesCountTotal = ref(0)
const matchesCurrent = ref(0)
const findState = ref(0)

// search options
const highlightAll = ref(true)
const matchCase = ref(false)
const matchDiacritics = ref(false)
const wholeWords = ref(false)
const findOptions = computed(() => ({
  // source: evt.source,
  type: '',
  query: searchText.value,
  caseSensitive: matchCase.value,
  entireWord: wholeWords.value,
  highlightAll: highlightAll.value,
  findPrevious: false,
  matchDiacritics: matchDiacritics.value,
}))

const searchInput = ref(null)

const handleEvent = (type: string, findPrevious = false) => {
  eventBus.dispatch('find', { ...findOptions.value, type, findPrevious })
}

const onEnter = (event: KeyboardEvent) => {
  handleEvent('again', event.shiftKey)
}

const findPrev = () => {
  handleEvent('again', true)
}

const findNext = () => {
  handleEvent('again')
}
const toggleSearch = async () => {
  showSearch.value = !showSearch.value

  if (showSearch.value) {
    await nextTick()
    searchInput.value.focus()
  } else {
    eventBus.dispatch('find', { ...findOptions.value, query: '' })
  }
}

const findString = () => {
  eventBus.dispatch('find', findOptions.value)
}

const changeInputValue = (event: Event) => {
  const oldValue = inputValue.value
  const newValue = +(event.target as HTMLInputElement).value
  const validatedValue =
    newValue < 1 || newValue > props.numPages ? oldValue : newValue
  inputValue.value = validatedValue
  event.target.value = validatedValue
  pdfLinkService.goToPage(validatedValue)
}

watch([highlightAll, matchCase, matchDiacritics, wholeWords], () => {
  findString()
})

function isEditingContent(event: KeyboardEvent): boolean {
  const element = event.target as HTMLElement
  const tagName = element.tagName

  return (
    element.isContentEditable ||
    tagName === 'INPUT' ||
    tagName === 'SELECT' ||
    tagName === 'TEXTAREA'
  )
}

const onKeyDown = (event: KeyboardEvent) => {
  if (
    (event.key === 'Escape' && showSearch.value) ||
    // The `Cmd+K` shortcut both opens and closes the modal.
    (event.key.toLowerCase() === 'f' && (event.metaKey || event.ctrlKey)) ||
    // The `/` shortcut opens but doesn't close the modal because it's
    // a character.
    (!isEditingContent(event) && event.key === '/' && !showSearch.value)
  ) {
    event.preventDefault()
    toggleSearch()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)

  eventBus.on(
    'pagechanging',
    ({ pageNumber }) => (inputValue.value = pageNumber)
  )

  eventBus.on('updatefindmatchescount', ({ matchesCount }) => {
    const { current, total } = matchesCount
    matchesCurrent.value = current
    matchesCountTotal.value = total
  })

  eventBus.on('updatefindcontrolstate', ({ matchesCount, state }) => {
    const { current, total } = matchesCount
    matchesCurrent.value = current
    matchesCountTotal.value = total
    findState.value = state
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<style scoped>
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  margin: 0;
  appearance: none;
}

/* Firefox */
input[type='number'] {
  appearance: textfield;
}
</style>
