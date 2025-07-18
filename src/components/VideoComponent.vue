<template>
    <div id="player" :ref="handleId">
        <div class="video-box">
            <video
                id="video-element"
                ref="videoElem"
                class="videoContainer"
                @ended="endedVideo()"
                @timeupdate="updateProgressBar()"
            >
                <source :src="url" :type="type" />
            </video>
        </div>
        <div id="controls">
            <div class="counters">
                <div class="currentTime">
                    {{ formatTime(currentTime()) }}
                </div>
                <div class="totalTime">
                    {{ formatTime(duration()) }}
                </div>
            </div>
            <div class="wrapperProgressbar" @click="skipVideo($event)">
                <progress
                    id="progress-bar"
                    ref="progressBar"
                    class="progressBar"
                    max="100"
                    min="0"
                    value="0"
                >
                    0% played
                </progress>
            </div>
            <div class="row">
                <div class="wrap">
                    <button
                        id="btnReplay"
                        :class="{ active: isActive }"
                        class="icon-dl-replay btnReplay"
                        @click="replayVideo()"
                    />
                    <span @click="changeSpeed()">x{{ speedValue }}</span>
                </div>
                <div class="buttons">
                    <button
                        id="btnStart"
                        class="icon-dl-back"
                        @click="resetPlayer()"
                    />
                    <button
                        id="btnPrevious"
                        class="icon-dl-back-frame"
                        @click="toPreviousFrame()"
                    />
                    <button
                        v-if="isPlayBtn"
                        id="btnPlay"
                        class="icon-dl-play"
                        @click="playPauseVideo()"
                    />
                    <button
                        v-else
                        id="btnPause"
                        class="icon-dl-pause"
                        @click="playPauseVideo()"
                    />
                    <button
                        id="btnNext"
                        class="icon-dl-next-frame"
                        @click="toNextFrame()"
                    />
                    <button
                        id="btnEnd"
                        class="icon-dl-next"
                        @click="toEndVideo()"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'VideoComponent',
    /* eslint-disable */
    props: [
        'setIsOpen',
        'isBlackTheme',
        'url',
        'top',
        'right',
        'type',
        'typeOfContent',
        'width',
        'height',
        'videoWidth',
        'videoHeight'
    ],
    /* eslint-enable */
    data() {
        return {
            isActive: false,
            isPlayBtn: true,
            speedValue: 1,
            handleId: 'handle-id'
        }
    },
    computed: {
        player() {
            return this.$refs.videoElem
        },
        progressBar() {
            return this.$refs.progressBar
        }
    },
    mounted() {
        const events = [
            'timeupdate',
            'volumechange',
            'seeked',
            'loadedmetadata'
        ]

        events.map((e) => {
            this.$refs.videoElem.addEventListener(e, () => {
                this.$forceUpdate()
            })
        })

        this.$refs.videoElem.addEventListener('loadedmetadata', () => {
            this.$refs.videoElem.volume = 0
            this.$forceUpdate()
        })
    },
    methods: {
        playPauseVideo() {
            if (this.player.paused || this.player.ended) {
                this.isPlayBtn = false
                this.player.play()
            } else {
                this.player.pause()
                this.isPlayBtn = true
            }
        },
        endedVideo() {
            this.isPlayBtn = true
        },
        progressPercentage() {
            return (this.currentTime() / this.duration()) * 100
        },
        skipVideo(event) {
            const wrapperOffset =
                event.currentTarget.getBoundingClientRect().left
            const clickedOffset = event.clientX - wrapperOffset
            const progress_width =
                (clickedOffset /
                    event.currentTarget.getBoundingClientRect().width) *
                100
            const newTime = (this.duration() / 100) * progress_width
            this.$refs.videoElem.currentTime = newTime
        },
        updateProgressBar() {
            const percentage = Math.floor(
                (100 / this.player.duration) * this.player.currentTime
            )
            this.progressBar.value = percentage
            this.progressBar.innerHTML = `${percentage}% played`
        },
        resetPlayer() {
            this.player.currentTime = 0
        },
        toEndVideo() {
            this.player.currentTime = this.player.duration
        },
        toPreviousFrame() {
            this.player.currentTime = this.player.currentTime - 1
        },
        toNextFrame() {
            this.player.currentTime = this.player.currentTime + 1
        },
        replayVideo() {
            this.isActive = !this.isActive
            this.isActive
                ? (this.player.loop = true)
                : (this.player.loop = false)
        },
        currentTime() {
            return this.$refs.videoElem?.currentTime || 0
        },
        duration() {
            return this.$refs.videoElem?.duration || 0
        },
        formatTime(time) {
            if (!time || !parseInt(time)) {
                return '00:00'
            }
            let hours
            let minutes
            let seconds
            ;((minutes = Math.floor((time / 60) % 60)),
                (seconds = Math.floor(time % 60)),
                (hours = Math.floor(time / 60 / 60)))

            if (minutes < 10) minutes = `0${minutes}`
            if (seconds < 10) seconds = `0${seconds}`

            return `${hours ? `${hours}:` : ''}${minutes}:${seconds}`
        },
        speedUp(value) {
            if (value === 0.5) {
                this.player.playbackRate = 0.5
            }
            if (value === 1) {
                this.player.playbackRate = 1
            }
            if (value === 2) {
                this.player.playbackRate = 2.0
            }
            if (value === 4) {
                this.player.playbackRate = 4.0
            }
            if (value > 4) {
                this.player.playbackRate = 0.5
            }
        },
        changeSpeed() {
            if (this.speedValue < 4) {
                this.speedValue *= 2
                this.speedUp(this.speedValue)
            } else {
                this.speedValue = 0.5
                this.speedUp(this.speedValue)
            }
        }
    }
}
</script>

<style>
#player {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100vh;
    max-height: 100vh;
    background-color: var(--dl-color-studio-panel);
    pointer-events: all;
    overflow: hidden;
}

.videoContainer {
    width: 90%;
    max-width: 100%;
    max-height: calc(100vh - 150px);
    object-fit: contain;
    border-radius: 2px;
}

button {
    background: none;
    border: 0;
    cursor: pointer;
}

#player button::before {
    color: var(--dl-color-icon-default);
}

#controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 30px;
    flex-shrink: 0;
}

.counters {
    display: flex;
    justify-content: space-between;
    width: 90%;
    margin-top: 5px;
    color: var(--dl-color-icon-default);
    font-weight: 500;
    font-size: 12px;
    font-family: Roboto;
    font-style: normal;
    line-height: 14px;
}

.buttons {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
}

.buttons button::before {
    font-size: 18px;
}

.btnReplay::before {
    color: var(--dl-color-panel-header);
}

.row {
    display: flex;
    flex-direction: row;
    justify-content: center;
    width: 90%;
    margin-top: 12px;
}

/* .row { */

/*    display: flex; */

/*    flex-direction: row; */

/*    margin-top: 12px; */

/*    width: 90%; */

/* } */

.wrap {
    position: absolute;
    left: 4%;
    display: flex;
    align-items: center;
    color: rgb(255 255 255 / 50%);
    font-weight: normal;
    font-size: 14px;
    font-family: Roboto;
    font-style: normal;
    line-height: 16px;
}

.wrap span {
    color: var(--dl-color-panel-header);
    cursor: pointer;
}

.wrap button::before {
    color: var(--dl-color-panel-header);
    cursor: pointer;
}

.closeBtn {
    position: absolute;
    right: 1%;
    width: 20px;
    height: 20px;
    margin: 5px;
    text-align: center;
}

.closeBtn::before {
    font-size: 12px;
}

.wrapperProgressbar {
    display: flex;
    width: 90%;
    height: 1px;
    padding: 8px;
    cursor: pointer;
}

.progressBar {
    width: 100%;
    height: 2px;
    margin: 0;
    background: rgb(255 255 255 / 25%);
    border-radius: 0;
}

.containerBlack progress[value]::-webkit-progress-value {
    background-color: #7c8cff;
}

.containerWhite progress[value]::-webkit-progress-value {
    background-color: #3452ff;
}

.containerBlack .active::before {
    color: #7c8cff;
}

.containerWhite .active::before {
    color: #3452ff;
}

.video-box {
    display: flex;
    flex-grow: 1;
    align-items: center;
    justify-content: center;
    margin-top: 30px;
    overflow: hidden;
}

.vdr {
    border: none;
}
</style>
