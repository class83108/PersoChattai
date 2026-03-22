/* PersoChattai — Role Play conversation manager */

const STATES = ['idle', 'preparing', 'connecting', 'active', 'assessing', 'completed', 'failed'];
let currentState = 'idle';
let conversationId = null;
let timerInterval = null;
let timerSeconds = 0;
let audioContext = null;
let analyser = null;
let micStream = null;

// --- State Machine ---

function setState(newState) {
  currentState = newState;
  STATES.forEach((s) => {
    const el = document.getElementById(`state-${s}`);
    if (el) el.classList.toggle('hidden', s !== newState);
  });

  if (newState === 'active') {
    startTimer();
  } else {
    stopTimer();
  }
}

// --- Conversation Lifecycle ---

async function startConversation() {
  const sourceType = document.getElementById('source-type').value;
  const sourceRef = document.getElementById('source-ref').value.trim();
  const errorEl = document.getElementById('start-error');
  const errorMsg = document.getElementById('start-error-msg');

  errorEl.classList.add('hidden');

  if (!sourceRef) {
    errorMsg.textContent = '請輸入卡片 ID 或主題描述';
    errorEl.classList.remove('hidden');
    return;
  }

  // Check microphone
  const hasMic = await checkMicrophone();
  if (!hasMic) {
    errorMsg.textContent = '無法存取麥克風，請允許瀏覽器使用麥克風權限';
    errorEl.classList.remove('hidden');
    return;
  }

  setState('preparing');

  try {
    const resp = await fetch('/api/conversation/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: getUserId(),
        source_type: sourceType,
        source_ref: sourceRef,
      }),
    });

    if (resp.status === 409) {
      errorMsg.textContent = '你已有進行中的對話';
      errorEl.classList.remove('hidden');
      setState('idle');
      return;
    }

    if (!resp.ok) {
      throw new Error(`API error: ${resp.status}`);
    }

    const data = await resp.json();
    conversationId = data.conversation_id || data.id;

    setState('connecting');
    await connectWebRTC();
    setState('active');
    startAudioMonitor();
  } catch (err) {
    console.error('Start conversation failed:', err);
    document.getElementById('fail-msg').textContent = err.message || '啟動對話失敗';
    setState('failed');
  }
}

async function endConversation() {
  if (!conversationId) return;

  setState('assessing');
  stopAudioMonitor();

  try {
    await fetch(`/api/conversation/${conversationId}/end`, { method: 'POST' });
    disconnectWebRTC();
    setState('completed');
    refreshHistory();
  } catch (err) {
    console.error('End conversation failed:', err);
    setState('completed');
  }
}

async function cancelConversation() {
  if (!conversationId) return;

  stopAudioMonitor();
  disconnectWebRTC();

  try {
    await fetch(`/api/conversation/${conversationId}/cancel`, { method: 'POST' });
  } catch (err) {
    console.error('Cancel conversation failed:', err);
  }

  conversationId = null;
  setState('idle');
  refreshHistory();
}

function retryConversation() {
  setState('idle');
}

function resetToIdle() {
  conversationId = null;
  setState('idle');
}

// --- Timer ---

function startTimer() {
  timerSeconds = 0;
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    timerSeconds++;
    updateTimerDisplay();
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function updateTimerDisplay() {
  const m = String(Math.floor(timerSeconds / 60)).padStart(2, '0');
  const s = String(timerSeconds % 60).padStart(2, '0');
  const el = document.getElementById('timer');
  if (el) el.textContent = `${m}:${s}`;
}

// --- Microphone ---

async function checkMicrophone() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    return true;
  } catch {
    return false;
  }
}

// --- Audio Monitor (simple volume indicator) ---

function startAudioMonitor() {
  if (!micStream) return;

  try {
    audioContext = new AudioContext();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;

    const source = audioContext.createMediaStreamSource(micStream);
    source.connect(analyser);

    monitorAudioLevel();
  } catch (err) {
    console.warn('Audio monitor setup failed:', err);
  }
}

function monitorAudioLevel() {
  if (!analyser || currentState !== 'active') return;

  const data = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(data);

  const avg = data.reduce((sum, v) => sum + v, 0) / data.length;
  const indicator = document.getElementById('audio-indicator');
  if (indicator) {
    if (avg > 30) {
      indicator.classList.add('audio-active');
      indicator.classList.remove('audio-pulse');
    } else {
      indicator.classList.remove('audio-active');
      indicator.classList.add('audio-pulse');
    }
  }

  requestAnimationFrame(monitorAudioLevel);
}

function stopAudioMonitor() {
  if (audioContext) {
    audioContext.close().catch(() => {});
    audioContext = null;
    analyser = null;
  }
}

// --- WebRTC (FastRTC integration) ---

let peerConnection = null;

async function connectWebRTC() {
  micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

  peerConnection = new RTCPeerConnection();

  // Add mic track
  micStream.getTracks().forEach((track) => {
    peerConnection.addTrack(track, micStream);
  });

  // Handle remote audio
  peerConnection.ontrack = (event) => {
    const audio = new Audio();
    audio.srcObject = event.streams[0];
    audio.play().catch(() => {});
  };

  // Create offer
  const offer = await peerConnection.createOffer();
  await peerConnection.setLocalDescription(offer);

  // Wait for ICE gathering
  await new Promise((resolve) => {
    if (peerConnection.iceGatheringState === 'complete') {
      resolve();
    } else {
      peerConnection.addEventListener('icegatheringstatechange', () => {
        if (peerConnection.iceGatheringState === 'complete') resolve();
      });
    }
  });

  // Send offer to FastRTC signaling endpoint
  const resp = await fetch('/api/conversation/rtc/offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sdp: peerConnection.localDescription.sdp,
      type: peerConnection.localDescription.type,
    }),
  });

  if (!resp.ok) {
    throw new Error('WebRTC signaling failed');
  }

  const answer = await resp.json();
  await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
}

function disconnectWebRTC() {
  if (peerConnection) {
    peerConnection.close();
    peerConnection = null;
  }
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
}

// --- History refresh ---

function refreshHistory() {
  const el = document.getElementById('conversation-history');
  if (el) {
    htmx.ajax('GET', `/roleplay/partials/history?user_id=${getUserId()}`, { target: '#conversation-history', swap: 'innerHTML' });
  }
}
