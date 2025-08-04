<template>
    <div
        class="relative bg-[#161b22] w-full h-screen flex items-center justify-center z-10"
    >
        <div class="mask"></div>
        <div
            ref="shineRef"
            class="absolute bg-[#939aff] blur-[180px] will-change-transform mix-blend-overlay rounded-[300px] pointer-events-none -z-10 top-0 w-[80rem] h-[80rem]"
            :class="{ 'animate-blob': isPlaying }"
            style="animation-delay: 2s"
        ></div>

        <div
            class="max-w-lg w-full backdrop-blur-3xl bg-black/10 rounded-md p-4 shadow-lg border border-[#ffa3b80d]"
        >
            <div
                v-if="error"
                class="absolute z-20 w-full h-full backdrop-blur bg-black/80 inset-0 flex items-center justify-center rounded-md"
            >
                <p class="text-lg text-center text-medium text-pink-700">
                    {{ error }}
                </p>
            </div>
            <audio ref="audio" :src="url"></audio>
            <div class="audio-controls">
                <div class="progress-container w-full">
                    <WaveForm
                        :url="url"
                        :show="isDraggingProgress"
                        :current-progress="currentProgress"
                        :is-playing="isPlaying"
                        :is-dragging="isDraggingProgress"
                    />
                    <Slider
                        v-model="currentProgress"
                        :is-playing="isPlaying"
                        @drag-start="onDragStart"
                        @drag-move="onDragMove"
                        @drag-end="onDragEnd"
                        @click="onProgressClick"
                    />
                    <div
                        class="flex justify-between text-white/80 font-semibold text-sm pt-1 select-none"
                    >
                        <p>{{ getTimeString(currentTime) }}</p>
                        <p>{{ getTimeString(duration) }}</p>
                    </div>
                </div>

                <div class="my-0.5">
                    <div
                        class="flex items-center justify-center text-white w-full relative"
                    >
                        <button
                            class="transition-all duration-75 ease-in active:scale-95 stroke-slate-300 hover:stroke-slate-50 px-4 outline-none"
                            title="Rewind by 10 seconds [j]"
                            @click="rewindSecBy(10)"
                        >
                            <svg
                                aria-hidden="true"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke-width="1.5"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                class="h-6 w-6"
                            >
                                <path
                                    d="M8 5L5 8M5 8L8 11M5 8H13.5C16.5376 8 19 10.4624 19 13.5C19 15.4826 18.148 17.2202 17 18.188"
                                ></path>
                                <path d="M5 15V19"></path>
                                <path
                                    d="M8 18V16C8 15.4477 8.44772 15 9 15H10C10.5523 15 11 15.4477 11 16V18C11 18.5523 10.5523 19 10 19H9C8.44772 19 8 18.5523 8 18Z"
                                ></path>
                            </svg>
                        </button>
                        <div
                            class="flex items-center justify-center w-16 h-16 p-2"
                        >
                            <button
                                class="rounded-full p-3 transition-all duration-75 ease-in active:scale-95 outline-none"
                                :class="[
                                    isPlaying
                                        ? 'scale-125 bg-black text-white hover:bg-primary'
                                        : 'bg-white text-black hover:bg-primary hover:text-white '
                                ]"
                                :title="isPlaying ? 'Pause [k]' : 'Play [k]'"
                                @click="togglePlay"
                            >
                                <i-heroicons-pause-20-solid
                                    v-if="isPlaying"
                                    class="w-6 h-6"
                                />
                                <i-mingcute-play-fill v-else class="w-5 h-5" />
                            </button>
                        </div>
                        <button
                            class="transition-all duration-75 ease-in active:scale-95 stroke-slate-300 hover:stroke-slate-50 px-4 outline-none"
                            title="Forward by 10 seconds [l]"
                            @click="forwardSecBy(10)"
                        >
                            <svg
                                aria-hidden="true"
                                viewBox="0 0 24 24"
                                fill="none"
                                class="h-6 w-6"
                            >
                                <path
                                    d="M16 5L19 8M19 8L16 11M19 8H10.5C7.46243 8 5 10.4624 5 13.5C5 15.4826 5.85204 17.2202 7 18.188"
                                    stroke-width="1.5"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                ></path>
                                <path
                                    d="M13 15V19"
                                    stroke-width="1.5"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                ></path>
                                <path
                                    d="M16 18V16C16 15.4477 16.4477 15 17 15H18C18.5523 15 19 15.4477 19 16V18C19 18.5523 18.5523 19 18 19H17C16.4477 19 16 18.5523 16 18Z"
                                    stroke-width="1.5"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                ></path>
                            </svg>
                        </button>
                        <div
                            class="absolute inset-y-0 right-0 flex items-center"
                        >
                            <button
                                class="relative transition-colors duration-75 ease-in hover:text-gray-100 z-40 select-none mr-4 outline-none"
                                title="Change playback rate [>]"
                                @click.prevent.stop="changeSpeed"
                            >
                                <div
                                    class="flex text-xs font-bold"
                                    :class="[
                                        playbackRate !== 1
                                            ? 'text-white'
                                            : 'text-white/50'
                                    ]"
                                >
                                    <Transition name="slide-up" mode="out-in">
                                        <p v-if="playbackRate === 1">1</p>
                                        <p v-else-if="playbackRate === 1.5">
                                            1.5
                                        </p>
                                        <p v-else-if="playbackRate === 2">2</p>
                                    </Transition>
                                    <p>x</p>
                                </div>
                            </button>
                            <button
                                class="volume__button relative transition-colors duration-75 ease-in hover:text-gray-100 z-40 text-white/50 outline-none"
                                :title="
                                    volume === 0 ? 'unmute [m]' : 'mute [m]'
                                "
                                @click.prevent.stop="muteVolume"
                            >
                                <i-iconamoon-volume-up-fill
                                    v-if="volume > 0.5"
                                />
                                <i-iconamoon-volume-down-fill
                                    v-else-if="volume < 0.5 && volume > 0"
                                />
                                <i-iconamoon-volume-off-fill v-else />
                                <div
                                    class="volume__menu opacity-0 w-fit invisible absolute transition-all duration-500 ease-linear bottom-full pb-2 -translate-x-1/2 left-1/2"
                                >
                                    <div
                                        class="bg-[#171e3d] w-full h-36 p-3 py-6 rounded shadow flex items-center justify-center border border-black/10"
                                    >
                                        <Slider
                                            v-model="volume"
                                            position="vertical"
                                            class="slider"
                                        />
                                    </div>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import IIconamoonVolumeUpFill from '~icons/iconamoon/volume-up-fill'
import IIconamoonVolumeDownFill from '~icons/iconamoon/volume-down-fill'
import IIconamoonVolumeOffFill from '~icons/iconamoon/volume-off-fill'

defineProps({
    url: {
        type: String,
        required: true
    },
    loading: Boolean
})
const audioContext = ref<AudioContext | null>(null)
const error = ref<null | string>(null)
const audio = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const currentProgress = ref(0)
const volume = ref(1)
const oldVolume = ref(null)
const playbackRate = ref(1)
const pausedByDragEvent = ref(false)
const isDraggingProgress = ref(false)

const shineRef = ref<HTMLElement | null>(null)

watch(volume, (value) => {
    audio.value.volume = value
})

const getTimeString = (time: number) => {
    const secs = `${parseInt(`${time % 60}`, 10)}`.padStart(2, '0')
    const min = parseInt(`${(time / 60) % 60}`, 10)

    return `${min}:${secs}`
}

const togglePlay = async () => {
    if (audioContext.value.state === 'suspended') {
        await audioContext.value.resume()
    }
    if (isPlaying.value) {
        audio.value.pause()
    } else {
        audio.value.play()
    }
}

const seekTo = (value: number) => {
    audio.value.currentTime = value
}

const rewindSecBy = (value: number) => {
    seekTo(audio.value.currentTime - value)
}

const forwardSecBy = (value: number) => {
    seekTo(audio.value.currentTime + value)
}

const onDragStart = () => {
    audio.value.pause()
    if (isPlaying.value) pausedByDragEvent.value = true
}

const onDragMove = (value: number) => {
    isDraggingProgress.value = true
    currentTime.value = value * duration.value
}

const onDragEnd = (value: number) => {
    isDraggingProgress.value = false
    seekTo(value * duration.value)
    if (pausedByDragEvent.value) audio.value.play()
    pausedByDragEvent.value = false
}

const onProgressClick = (value: number) => {
    seekTo(value * duration.value)
}

const setPlaybackRate = (rate: number) => {
    audio.value.playbackRate = rate
    playbackRate.value = rate
}

const changeSpeed = () => {
    const playbackRate = audio.value.playbackRate
    if (playbackRate === 1) {
        setPlaybackRate(1.5)
    } else if (playbackRate === 1.5) {
        setPlaybackRate(2)
    } else {
        setPlaybackRate(1)
    }
}

const muteVolume = () => {
    if (volume.value > 0) {
        oldVolume.value = volume.value
        volume.value = 0
    } else {
        volume.value = oldVolume.value ?? 50
    }
}

const onLoadedMetaData = () => {
    duration.value = audio.value.duration
}

const onError = () => {
    error.value = audio.value.error.message
    throw new Error(error.value)
}

const onTimeUpdate = () => {
    currentTime.value = audio.value.currentTime
    currentProgress.value = currentTime.value / duration.value
}

const onPlay = () => {
    isPlaying.value = true
}

const onPause = () => {
    isPlaying.value = false
}

const onEnded = () => {
    isPlaying.value = false
}

const onKeyDown = (event: KeyboardEvent) => {
    switch (event.key.toLowerCase()) {
        case 'm':
            muteVolume()
            break
        case 'k':
        case ' ': // space
            togglePlay()
            break
        case 'j':
        case 'arrowleft':
            rewindSecBy(10)
            break
        case 'l':
        case 'arrowright':
            forwardSecBy(10)
            break
        case '>':
            changeSpeed()
            break
        default:
            break
    }
}

const attachEvents = () => {
    const audioEl: HTMLAudioElement = audio.value
    audioEl.addEventListener('loadedmetadata', onLoadedMetaData)
    audioEl.addEventListener('error', onError)
    audioEl.addEventListener('timeupdate', onTimeUpdate)
    audioEl.addEventListener('play', onPlay)
    audioEl.addEventListener('pause', onPause)
    audioEl.addEventListener('ended', onEnded)

    window.addEventListener('keydown', onKeyDown)
}

const detachEvents = () => {
    const audioEl: HTMLAudioElement = audio.value
    audioEl.removeEventListener('loadedmetadata', onLoadedMetaData)
    audioEl.removeEventListener('error', onError)
    audioEl.removeEventListener('timeupdate', onTimeUpdate)
    audioEl.removeEventListener('play', onPlay)
    audioEl.removeEventListener('pause', onPause)
    audioEl.removeEventListener('ended', onEnded)

    window.removeEventListener('keydown', onKeyDown)
}

onMounted(async () => {
    attachEvents()

    audioContext.value = new AudioContext()
})

onBeforeUnmount(() => {
    detachEvents()
})
</script>

export default {}

<style lang="scss" scoped>
.volume__button {
    &:hover {
        .volume__menu {
            @apply opacity-100 visible duration-75;
        }
    }

    .slider {
        @apply relative;

        &::before,
        &::after {
            @apply block absolute top-1/2 h-px w-[3px] bg-[#a1a1a1] z-[1];

            content: '';
        }

        &::before {
            @apply -left-[3px];
        }

        &::after {
            @apply -right-[3px];
        }
    }
}

.slide-up-enter-active,
.slide-up-leave-active {
    transition: all 0.25s ease-out;
}

.slide-up-enter-from {
    opacity: 0;
    transform: translateY(10px);
}

.slide-up-leave-to {
    opacity: 0;
    transform: translateY(-10px);
}

.mask {
    @apply absolute inset-0;

    mask-image: linear-gradient(to bottom, transparent, black, transparent);
    -webkit-mask-image: linear-gradient(
        to bottom,
        transparent,
        black,
        transparent
    );
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32' fill='none' stroke='rgb(148 163 184 / 0.05)'%3e%3cpath d='M0 .5H31.5V32'/%3e%3c/svg%3e");
}
</style>
