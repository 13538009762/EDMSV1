/**
 * 将录制的 Blob (通常是 WebM) 转换为讯飞要求的 PCM (16k, 16bit, 单声道)
 */
export async function convertToPcm(blob: Blob): Promise<ArrayBuffer> {
  const arrayBuffer = await blob.arrayBuffer();
  console.log(`[Audio Debug] Original Blob size: ${blob.size} bytes`);
  
  // 1. 使用基础 AudioContext 解码原始数据
  const tempCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  let audioBuffer: AudioBuffer;
  try {
    audioBuffer = await tempCtx.decodeAudioData(arrayBuffer);
  } finally {
    await tempCtx.close();
  }

  console.log(`[Audio Debug] Raw Decoded: duration=${audioBuffer.duration}s, rate=${audioBuffer.sampleRate}`);

  // 2. 使用 OfflineAudioContext 将其重采样为 16000Hz 单声道
  const targetSampleRate = 16000;
  const offlineCtx = new OfflineAudioContext(1, Math.ceil(audioBuffer.duration * targetSampleRate), targetSampleRate);
  
  const source = offlineCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(offlineCtx.destination);
  source.start();
  
  const resampledBuffer = await offlineCtx.startRendering();
  const channelData = resampledBuffer.getChannelData(0);
  
  console.log(`[Audio Debug] Resampled: length=${channelData.length} samples, duration=${resampledBuffer.duration}s`);

  // 💡 Debug: Check volume
  let maxAmp = 0;
  for (let i = 0; i < channelData.length; i++) {
    const abs = Math.abs(channelData[i]);
    if (abs > maxAmp) maxAmp = abs;
  }
  
  if (maxAmp < 0.01) {
    console.warn(`[Audio Debug] WARNING: Very low volume (Max amp: ${maxAmp.toFixed(4)})`);
  } else {
    console.log(`[Audio Debug] Sound detected! Max amp: ${maxAmp.toFixed(4)}`);
  }

  // 3. 转换为 16bit PCM
  const pcmBuffer = new ArrayBuffer(channelData.length * 2);
  const pcmView = new DataView(pcmBuffer);
  
  for (let i = 0; i < channelData.length; i++) {
    const s = Math.max(-1, Math.min(1, channelData[i]));
    pcmView.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
  
  return pcmBuffer;
}
