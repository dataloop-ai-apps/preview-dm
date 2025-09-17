<template>
  <div
    ref="wrapper"
    class="flex items-center justify-center cursor-pointer"
    :class="[isVertical ? 'h-full w-3' : 'w-full h-3']"
    @click.prevent.stop="onClick"
    @pointerdown.prevent.stop="onDragStart"
    @pointermove.prevent.stop="onDragMove"
    @pointerup.prevent.stop="onDragEnd"
  >
    <div
      class="bg-[#555] rounded-md relative z-10"
      :class="[isVertical ? 'h-full w-0.5' : 'w-full h-0.5 ']"
    >
      <div
        class="absolute bg-primary rounded-md"
        :class="[
          isVertical
            ? 'w-1 bottom-0 translate-x-1/2 right-1/2 '
            : `h-1 left-0 -translate-y-1/2 top-1/2`,
        ]"
        :style="`${isVertical ? 'height' : 'width'}:  ${
          currentProgress * 100
        }%`"
      >
        <div
          class="touch-none select-none cursor-pointer absolute w-3 h-3 rounded-full shadow-sm hover:scale-150 hover:shadow-md transition-all duration-75 ease-in bg-white"
          :class="[
            isVertical
              ? '-translate-x-1/2 left-1/2 -translate-y-1/2'
              : 'right-0 top-1/2 -translate-y-1/2 translate-x-1/2 ',
          ]"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: {
    type: Number,
    required: true,
  },
  position: {
    type: String,
    default: 'horizontal',
    required: false,
    validator: (value: string) => ['horizontal', 'vertical'].includes(value),
  },
})

const emit = defineEmits([
  'update:modelValue',
  'click',
  'dragStart',
  'dragMove',
  'dragEnd',
])

const isVertical = props.position === 'vertical'
const currentProgress = ref(10)
let currentCoordinate: number
let initCoordinate: number | null = null
const frameRequest: number | null = null
const rafPending = ref(false)

const wrapper = ref<HTMLDivElement>(null)

const value = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  },
})

watch(
  value,
  (newValue) => {
    currentProgress.value = newValue
  },
  { immediate: true }
)

watch(currentProgress, (newValue) => {
  value.value = newValue
})

const onClick = (event: MouseEvent) => {
  const { clientX, clientY } = event
  const { left, bottom, width, height } = wrapper.value.getBoundingClientRect()
  const coordinate = isVertical ? bottom - clientY : clientX - left
  const max = isVertical ? height : width
  const relativeCoordinate = Math.max(0, Math.min(1, coordinate / max))
  currentProgress.value = relativeCoordinate
  emit('click', relativeCoordinate)
}

const onDragStart = (event: PointerEvent) => {
  const { pointerId, clientX, clientY } = event
  initCoordinate = isVertical ? clientY : clientX
  wrapper.value.setPointerCapture(pointerId)
  emit('dragStart', initCoordinate)
}

const onAnimationFrame = () => {
  if (!currentCoordinate || !rafPending.value) return

  const { width, height, left, bottom } = wrapper.value.getBoundingClientRect()
  const maxValue = isVertical ? height : width

  const diff = isVertical
    ? bottom - currentCoordinate
    : currentCoordinate - left

  const res = Math.max(0, Math.min(1, diff / maxValue))

  currentProgress.value = res

  emit('dragMove', res)

  rafPending.value = false
}

const onDragMove = (event: PointerEvent) => {
  if (!initCoordinate || rafPending.value) return

  rafPending.value = true

  const { clientX, clientY } = event

  currentCoordinate = isVertical ? clientY : clientX
  window.requestAnimationFrame(onAnimationFrame)
}

const onDragEnd = (event: PointerEvent) => {
  wrapper.value.releasePointerCapture(event.pointerId)
  initCoordinate = null
  currentCoordinate = null
  rafPending.value = false
  emit('dragEnd', currentProgress.value)
}

onBeforeUnmount(() => {
  window.cancelAnimationFrame(frameRequest)
})
</script>
