<template>
  <div class="thinking-nine-loader">
    <svg viewBox="0 0 100 100" fill="none" aria-hidden="true">
      <g id="group" ref="groupRef">
        <path id="path" ref="pathRef" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" opacity="0.1"></path>
        <circle v-for="i in config.particleCount" :key="i" fill="currentColor" :ref="el => setParticleRef(el, i - 1)"></circle>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const groupRef = ref<SVGGElement | null>(null);
const pathRef = ref<SVGPathElement | null>(null);
const particles: (SVGCircleElement | null)[] = [];

function setParticleRef(el: any, index: number) {
  particles[index] = el;
}

const config = {
  rotate: true,
  particleCount: 140,
  trailSpan: 0.39,
  durationMs: 4700,
  rotationDurationMs: 30000,
  pulseDurationMs: 4200,
  strokeWidth: 5.5,
  baseRadius: 7,
  detailAmplitude: 3,
  petalCount: 9,
  curveScale: 3.9,
  point(progress: number, detailScale: number, config: any) {
    const t = progress * Math.PI * 2;
    const petals = Math.round(config.petalCount);
    const x = config.baseRadius * Math.cos(t) - config.detailAmplitude * detailScale * Math.cos(petals * t);
    const y = config.baseRadius * Math.sin(t) - config.detailAmplitude * detailScale * Math.sin(petals * t);
    return {
      x: 50 + x * config.curveScale,
      y: 50 + y * config.curveScale,
    };
  },
};

let animationFrameId: number;
let startedAt: number;

function normalizeProgress(progress: number) {
  return ((progress % 1) + 1) % 1;
}

function getDetailScale(time: number) {
  const pulseProgress = (time % config.pulseDurationMs) / config.pulseDurationMs;
  const pulseAngle = pulseProgress * Math.PI * 2;
  return 0.52 + ((Math.sin(pulseAngle + 0.55) + 1) / 2) * 0.48;
}

function getRotation(time: number) {
  if (!config.rotate) return 0;
  return -((time % config.rotationDurationMs) / config.rotationDurationMs) * 360;
}

function buildPath(detailScale: number, steps = 480) {
  return Array.from({ length: steps + 1 }, (_, index) => {
    const point = config.point(index / steps, detailScale, config);
    return `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
  }).join(' ');
}

function getParticle(index: number, progress: number, detailScale: number) {
  const tailOffset = index / (config.particleCount - 1);
  const point = config.point(normalizeProgress(progress - tailOffset * config.trailSpan), detailScale, config);
  const fade = Math.pow(1 - tailOffset, 0.56);
  return {
    x: point.x,
    y: point.y,
    radius: 0.9 + fade * 2.7,
    opacity: 0.04 + fade * 0.96,
  };
}

function render(now: number) {
  if (!startedAt) startedAt = now;
  const time = now - startedAt;
  const progress = (time % config.durationMs) / config.durationMs;
  const detailScale = getDetailScale(time);
  
  if (groupRef.value) {
    groupRef.value.setAttribute('transform', `rotate(${getRotation(time)} 50 50)`);
  }
  
  if (pathRef.value) {
    pathRef.value.setAttribute('d', buildPath(detailScale));
  }
  
  particles.forEach((node, index) => {
    if (node) {
      const particle = getParticle(index, progress, detailScale);
      node.setAttribute('cx', particle.x.toFixed(2));
      node.setAttribute('cy', particle.y.toFixed(2));
      node.setAttribute('r', particle.radius.toFixed(2));
      node.setAttribute('opacity', particle.opacity.toFixed(3));
    }
  });
  
  animationFrameId = requestAnimationFrame(render);
}

onMounted(() => {
  if (pathRef.value) {
    pathRef.value.setAttribute('stroke-width', String(config.strokeWidth));
  }
  animationFrameId = requestAnimationFrame(render);
});

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
});
</script>

<style scoped>
.thinking-nine-loader {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  padding: 4px;
}

svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}
</style>
