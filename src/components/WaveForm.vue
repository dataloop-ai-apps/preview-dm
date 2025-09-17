<template>
  <div ref="container" class="waveform scale-x-105 relative">
    <div ref="scrollContainer" class="scroll">
      <div ref="wrapper" class="wrapper" :class="{ 'is-open': show }">
        <div ref="canvasWrapper" class="canvases"></div>
        <div ref="progressWrapper" class="progress"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import resolveConfig from 'tailwindcss/resolveConfig'
import tailwindConfig from '../../tailwind.config.js'

type WaveOptions = {
  /** HTML element or CSS selector */
  container: HTMLElement | string
  /** The height of the waveform in pixels */
  height?: number
  /** The color of the waveform */
  waveColor?: string
  /** The color of the progress mask */
  progressColor?: string
  /** Render the waveform with bars like this: ▁ ▂ ▇ ▃ ▅ ▂ */
  barWidth?: number
  /** Spacing between bars in pixels */
  barGap?: number
  /** Rounded borders for bars */
  barRadius?: number
  /** A vertical scaling factor for the waveform */
  barHeight?: number
  /** Minimum pixels per second of audio (i.e. zoom level) */
  minPxPerSec?: number
  /** Stretch the waveform to fill the container, true by default */
  fillParent?: boolean
}

const props = defineProps({
  url: {
    type: String,
    required: true,
  },
  currentProgress: {
    type: Number,
    required: true,
  },
  show: Boolean,
  isPlaying: Boolean,
  isDragging: Boolean,
})

const defaultOptions = {
  height: 88,
  barWidth: 4,
  barGap: 4,
  barRadius: 3,
  barHeight: 3,
  minPxPerSec: 100,
  fillParent: true,
  sampleRate: 8000,
}

let options: WaveOptions | null = null

const container = ref(null)
const scrollContainer = ref(null)
const wrapper = ref(null)
const canvasWrapper = ref(null)
const progressWrapper = ref(null)

let timeouts: Array<{ timeout?: ReturnType<typeof setTimeout> }> = []
let audioData: AudioBuffer | null = null
let isScrolling = false

const fullConfig = resolveConfig(tailwindConfig)

const animate = () => {
  if (!props.isDragging) return
  renderProgress(props.currentProgress)

  window.requestAnimationFrame(animate)
}
watch(
  () => [props.isDragging],
  () => {
    window.requestAnimationFrame(animate)
  }
)

const createDelay = (delayMs = 10): ((fn: () => void) => void) => {
  const context: { timeout?: ReturnType<typeof setTimeout> } = {}
  timeouts.push(context)

  return (callback: () => void) => {
    context.timeout && clearTimeout(context.timeout)
    context.timeout = setTimeout(callback, delayMs)
  }
}

const renderWaveform = (
  channelData: Array<Float32Array | number[]>,
  options: WaveOptions,
  width: number
) => {
  // A container for canvases
  const canvasContainer = document.createElement('div')
  canvasContainer.style.height = `${options.height}px`
  canvasWrapper.value.appendChild(canvasContainer)

  // A container for progress canvases
  const progressContainer = canvasContainer.cloneNode() as HTMLElement
  progressWrapper.value.appendChild(progressContainer)

  const MAX_CANVAS_WIDTH = 4000
  const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value
  const len = channelData[0].length
  const scale = len / scrollWidth
  const viewportWidth = Math.min(MAX_CANVAS_WIDTH, clientWidth)
  const start = Math.floor(Math.abs(scrollLeft) * scale)
  const end = Math.ceil(start + viewportWidth * scale)
  const viewportLen = end - start

  // Draw a portion of the waveform from start peak to end peak
  const draw = (start: number, end: number) => {
    renderSingleCanvas(
      channelData,
      options,
      width,
      Math.max(0, start),
      Math.min(end, len),
      canvasContainer,
      progressContainer
    )
  }

  // Draw the waveform in viewport chunks, each with a delay
  const headDelay = createDelay()
  const tailDelay = createDelay()
  const renderHead = (fromIndex: number, toIndex: number) => {
    draw(fromIndex, toIndex)
    if (fromIndex > 0) {
      headDelay(() => {
        renderHead(fromIndex - viewportLen, toIndex - viewportLen)
      })
    }
  }
  const renderTail = (fromIndex: number, toIndex: number) => {
    draw(fromIndex, toIndex)
    if (toIndex < len) {
      tailDelay(() => {
        renderTail(fromIndex + viewportLen, toIndex + viewportLen)
      })
    }
  }

  renderHead(start, end)
  if (end < len) {
    renderTail(end, end + viewportLen)
  }
}

const renderSingleCanvas = (
  channelData: Array<Float32Array | number[]>,
  options: WaveOptions,
  width: number,
  start: number,
  end: number,
  canvasContainer: HTMLElement,
  progressContainer: HTMLElement
) => {
  const pixelRatio = window.devicePixelRatio || 1
  const height = options.height || 0
  const barWidth =
    options.barWidth != null && !isNaN(options.barWidth)
      ? options.barWidth * pixelRatio
      : 1
  const barGap =
    options.barGap != null && !isNaN(options.barGap)
      ? options.barGap * pixelRatio
      : options.barWidth
      ? barWidth / 2
      : 0
  const barRadius = options.barRadius || 0
  const barScale = options.barHeight || 1

  const isMono = channelData.length === 1
  const leftChannel = channelData[0]
  const rightChannel = isMono ? leftChannel : channelData[1]
  const useNegative = isMono && rightChannel.some((v: number) => v < 0)
  const length = leftChannel.length

  const barCount = Math.floor(width / (barWidth + barGap))
  const barIndexScale = barCount / length
  const halfHeight = height / 2

  let prevX = 0
  let prevLeft = 0
  let prevRight = 0

  const canvas = document.createElement('canvas')
  canvas.width = Math.round((width * (end - start)) / length)
  canvas.height = height
  canvas.style.width = `${Math.floor(canvas.width / pixelRatio)}px`
  canvas.style.height = `${options.height}px`
  canvas.style.left = `${Math.floor((start * width) / pixelRatio / length)}px`
  canvasContainer.appendChild(canvas)

  const ctx = canvas.getContext('2d', {
    desynchronized: true,
  }) as CanvasRenderingContext2D

  ctx.beginPath()
  ctx.fillStyle = options.waveColor

  // Firefox shim until 2023.04.11
  if (!ctx.roundRect) ctx.roundRect = ctx.fillRect

  for (let i = start; i < end; i++) {
    const barIndex = Math.round((i - start) * barIndexScale)

    if (barIndex > prevX) {
      const leftBarHeight = Math.round(prevLeft * halfHeight * barScale)
      const rightBarHeight = Math.round(prevRight * halfHeight * barScale)
      const barHeight = leftBarHeight + (rightBarHeight || 1)

      ctx.roundRect(
        prevX * (barWidth + barGap),
        height - barHeight,
        barWidth,
        barHeight,
        barRadius
      )

      prevX = barIndex
      prevLeft = 0
      prevRight = 0
    }

    const leftValue = useNegative ? leftChannel[i] : Math.abs(leftChannel[i])
    const rightValue = useNegative ? rightChannel[i] : Math.abs(rightChannel[i])

    if (leftValue > prevLeft) {
      prevLeft = leftValue
    }
    // If stereo, both channels are drawn as max values
    // If mono with negative values, the bottom channel will be the min negative values
    if (useNegative ? rightValue < -prevRight : rightValue > prevRight) {
      prevRight = rightValue < 0 ? -rightValue : rightValue
    }
  }

  ctx.fill()
  ctx.closePath()

  // Draw a progress canvas
  const progressCanvas = canvas.cloneNode() as HTMLCanvasElement
  progressContainer.appendChild(progressCanvas)
  const progressCtx = progressCanvas.getContext('2d', {
    desynchronized: true,
  }) as CanvasRenderingContext2D
  if (canvas.width > 0 && canvas.height > 0) {
    progressCtx.drawImage(canvas, 0, 0)
  }
  // Set the composition method to draw only where the waveform is drawn
  progressCtx.globalCompositeOperation = 'source-in'
  progressCtx.fillStyle = options.progressColor
  // This rectangle acts as a mask thanks to the composition method
  progressCtx.fillRect(0, 0, canvas.width, canvas.height)
}

const fetchArrayBuffer = async (url: string) => {
  return fetch(url).then((response) => response.arrayBuffer())
}

const decode = (
  audioData: ArrayBuffer,
  sampleRate: number
): Promise<AudioBuffer> => {
  const audioCtx = new AudioContext({ sampleRate })
  const decode = audioCtx.decodeAudioData(audioData)
  decode.finally(() => audioCtx.close())
  return decode
}
const loadAudio = async (url: string) => {
  const SAMPLE_RATE = 8000
  const audio = await fetchArrayBuffer(url)
  audioData = await decode(audio, SAMPLE_RATE)
}

const render = (audioData: AudioBuffer) => {
  // Clear previous timeouts
  timeouts.forEach(
    (context) => context.timeout && clearTimeout(context.timeout)
  )
  timeouts = []

  // Determine the width of the waveform
  const pixelRatio = window.devicePixelRatio || 1
  const parentWidth = scrollContainer.value.clientWidth
  const scrollWidth = Math.ceil(audioData.duration * (options.minPxPerSec || 0))

  // Whether the container should scroll
  isScrolling = scrollWidth > parentWidth
  const useParentWidth = options.fillParent && !isScrolling

  // Width and height of the waveform in pixels
  const width = (useParentWidth ? parentWidth : scrollWidth) * pixelRatio

  // Set the width of the wrapper
  wrapper.value.style.width = useParentWidth ? '100%' : `${scrollWidth}px`

  const channels = [audioData.getChannelData(0)]
  if (audioData.numberOfChannels > 1) channels.push(audioData.getChannelData(1))
  renderWaveform(channels, options, width)
}

const scrollIntoView = (progress: number) => {
  const { clientWidth, scrollWidth } = scrollContainer.value
  const progressWidth = scrollWidth * progress
  const sliderWidth = clientWidth * progress

  scrollContainer.value.scrollLeft = progressWidth - sliderWidth
}

const renderProgress = (progress: number) => {
  if (isNaN(progress)) return
  progressWrapper.value.style.width = `${progress * 100}%`

  if (isScrolling) {
    scrollIntoView(progress)
  }
}

onMounted(async () => {
  await loadAudio(props.url)
  options = Object.assign({}, defaultOptions, {
    container: container.value,
    waveColor: '#555',
    progressColor: fullConfig.theme.colors.primary as string,
  })

  render(audioData)
})
</script>

<style lang="scss">
.waveform {
  --mask: linear-gradient(
    90deg,
    rgba(0 0 0 / 10%) 0,
    rgba(0 0 0 / 90%) 20%,
    rgba(0, 0, 0, 1) 80%,
    rgba(0 0 0 / 90%) 80%,
    rgba(0 0 0 / 10%)
  );
  -webkit-mask: var(--mask);
  mask: var(--mask);

  .scroll {
    @apply overflow-x-auto overflow-y-hidden w-full relative;

    scrollbar-color: transparent;
    scrollbar-width: none;

    &::-webkit-scrollbar {
      display: none;
      -webkit-appearance: none;
    }

    .wrapper {
      @apply relative overflow-visible z-20;
      display: grid;
      grid-template-rows: 0fr;
      transition: grid-template-rows 0.1s ease-out;

      &.is-open {
        grid-template-rows: 1fr;
      }
      .canvases {
        @apply min-h-0;

        & > div {
          @apply relative;
        }
      }

      .progress {
        @apply absolute top-0 left-0 w-0 h-full overflow-hidden pointer-events-none z-20;

        & > div {
          @apply relative;
        }
      }

      canvas {
        @apply block absolute top-0;

        image-rendering: pixelated;
      }
    }
  }
}
</style>
