(async function () {
  const PIXI = window.PIXI;
  const Live2DModel = window.PIXI.live2d.Live2DModel;

  const canvas = document.getElementById('avatarCanvas');
  if (!canvas) {
    console.error('avatarCanvas not found');
    return;
  }

  const app = new PIXI.Application({
    view: canvas,
    width: 300,
    height: 500,
    backgroundAlpha: 0,
    antialias: true,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true,
  });

  let model = null;
  let pendingAction = null;
  let activeEmotion = null;

  let hideAnswerTimeout = null;

  function showAnswer(text) {
    try {
      const overlay = document.getElementById('answerOverlay');
      if (!overlay) return;

      const safeText = typeof text === 'string' ? text : String(text ?? '');
      overlay.textContent = safeText;
      overlay.classList.add('visible');

      clearTimeout(hideAnswerTimeout);
      hideAnswerTimeout = setTimeout(() => {
        overlay.classList.remove('visible');
      }, 3500);
    } catch (e) {
      console.warn('[avatar] showAnswer failed:', e);
    }
  }

  function applyEmotion(emotionName) {

    if (!model) {
      pendingAction = emotionName;
      return;
    }

    activeEmotion = emotionName;
    console.log(`[avatar] ---> АКТИВИРОВАНА ЭМОЦИЯ: ${emotionName} <---`);

    clearTimeout(app.__expressionTimeout);
    app.__expressionTimeout = setTimeout(() => {
      activeEmotion = null;
      console.log('[avatar] ---> ЭМОЦИЯ СБРОШЕНА В ДЕФОЛТ <---');
    }, 3000); 
  }

  function handleServerMessage(raw) {
    try {
      const msg = typeof raw === 'string' ? JSON.parse(raw) : JSON.parse(raw.toString());
      console.log('[avatar] handleServerMessage parsed:', msg);
      
      
      if (msg?.emotion) {
        applyEmotion(msg.emotion);
      }

      if (msg?.answer) {
        showAnswer(msg.answer);
      }

    } catch (e) {
      console.warn('[avatar] handleServerMessage failed to parse:', raw, e);
    }
  }

  try {
    model = await Live2DModel.from('model/mao_pro_en/runtime/mao_pro.model3.json');
    app.stage.addChild(model);

    const scaleX = app.screen.width / model.width;
    const scaleY = app.screen.height / model.height;
    const scale = Math.min(scaleX, scaleY);

    model.scale.set(scale, scale);
    model.anchor.set(0.3, 0.3);
    model.x = (app.screen.width - model.width * scale) / 2;
    model.y = (app.screen.height - model.height * scale) / 2;

    console.log('Live2D model loaded successfully');

    app.ticker.add(() => {
      const coreModel = model?.internalModel?.coreModel;
      if (!coreModel) return;

      if (activeEmotion === 'happy') {
        try {
          coreModel.setParameterValueById('ParamA', 0.6); // Приоткрываем рот (звук "А")
          coreModel.setParameterValueById('ParamMouthUp', 1); // Тянем уголки губ вверх
          coreModel.setParameterValueById('ParamMouthDown', 0);

          coreModel.setParameterValueById('ParamEyeLSmile', 1);
          coreModel.setParameterValueById('ParamEyeRSmile', 1);
          coreModel.setParameterValueById('ParamCheek', 0.5);

          coreModel.setParameterValueById('ParamBrowLForm', 0);
          coreModel.setParameterValueById('ParamBrowRForm', 0);
          coreModel.setParameterValueById('ParamBrowLAngle', 0);
          coreModel.setParameterValueById('ParamBrowRAngle', 0);

          coreModel.setParameterValueById('ParamEyeLOpen', 1);
          coreModel.setParameterValueById('ParamEyeROpen', 1);
        } catch (e) {}

      } else if (activeEmotion === 'sad') {
        try {
          coreModel.setParameterValueById('ParamA', 0);
          coreModel.setParameterValueById('ParamMouthUp', 0);
          coreModel.setParameterValueById('ParamMouthDown', 1);

          coreModel.setParameterValueById('ParamBrowLForm', -1);
          coreModel.setParameterValueById('ParamBrowRForm', -1);
          coreModel.setParameterValueById('ParamBrowLAngle', -1);
          coreModel.setParameterValueById('ParamBrowRAngle', -1);

          coreModel.setParameterValueById('ParamEyeLSmile', 0);
          coreModel.setParameterValueById('ParamEyeRSmile', 0);
          coreModel.setParameterValueById('ParamCheek', 0);
        } catch (e) {}

      } else if (activeEmotion === 'processing') {
        try {
          coreModel.setParameterValueById('ParamO', 0.4);
          coreModel.setParameterValueById('ParamA', 0);
          coreModel.setParameterValueById('ParamMouthUp', 0);
          coreModel.setParameterValueById('ParamMouthDown', 0);

          coreModel.setParameterValueById('ParamEyeBallX', -0.5);

          coreModel.setParameterValueById('ParamEyeLSmile', 0);
          coreModel.setParameterValueById('ParamEyeRSmile', 0);
          coreModel.setParameterValueById('ParamCheek', 0);
          coreModel.setParameterValueById('ParamBrowLForm', 0);
          coreModel.setParameterValueById('ParamBrowRForm', 0);
        } catch (e) {}

      } else {
        try {
          coreModel.setParameterValueById('ParamA', 0);
          coreModel.setParameterValueById('ParamO', 0);
          coreModel.setParameterValueById('ParamMouthUp', 0);
          coreModel.setParameterValueById('ParamMouthDown', 0);
          
          coreModel.setParameterValueById('ParamEyeBallX', 0);
          coreModel.setParameterValueById('ParamCheek', 0);

          coreModel.setParameterValueById('ParamBrowLForm', 0);
          coreModel.setParameterValueById('ParamBrowRForm', 0);
          coreModel.setParameterValueById('ParamBrowLAngle', 0);
          coreModel.setParameterValueById('ParamBrowRAngle', 0);

          coreModel.setParameterValueById('ParamEyeLSmile', 0);
          coreModel.setParameterValueById('ParamEyeRSmile', 0);
          coreModel.setParameterValueById('ParamEyeLOpen', 1);
          coreModel.setParameterValueById('ParamEyeROpen', 1);
        } catch (e) {}
      }
    });

    if (pendingAction) {
      const emotionToRun = pendingAction;
      pendingAction = null;
      applyEmotion(emotionToRun);
    }
  } catch (err) {
    console.error('Failed to load Live2D model:', err);
    return;
  }

  let reconnectAttempts = 0;
  let reconnectTimer = null;
  let ws = null;

  function connectWebSocket() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    
    const wsUrl = 'ws://127.0.0.1:8080';
    console.log(`[avatar] Connecting to ${wsUrl}... (attempt ${reconnectAttempts + 1})`);
    
    ws = new WebSocket(wsUrl);
    
    ws.addEventListener('open', () => {
      console.log('[avatar] WebSocket connected successfully!');
      reconnectAttempts = 0;
      
      const overlay = document.getElementById('answerOverlay');
      if (overlay) {
        overlay.textContent = 'Подключено к серверу! Говорите...';
        overlay.classList.add('visible');
        setTimeout(() => {
          if (overlay) overlay.classList.remove('visible');
        }, 2000);
      }
    });

    ws.addEventListener('message', (event) => {
      console.log('[avatar] WebSocket message raw:', event?.data);
      handleServerMessage(event.data);
    });

    ws.addEventListener('close', (event) => {
      console.warn(`[avatar] WebSocket closed: ${event.code} - ${event.reason}`);
      
      const overlay = document.getElementById('answerOverlay');
      if (overlay) {
        overlay.textContent = 'Потеряно соединение с сервером. Переподключение...';
        overlay.classList.add('visible');
      }
      
      const delay = Math.min(3000 * (reconnectAttempts + 1), 15000);
      reconnectAttempts++;
      
      console.log(`[avatar] Reconnecting in ${delay/1000}s... (attempt ${reconnectAttempts})`);
      
      reconnectTimer = setTimeout(() => {
        connectWebSocket();
      }, delay);
    });

    ws.addEventListener('error', (err) => {
      console.error('[avatar] WebSocket error:', err);
    });
    
    window.__avatarWs = ws;
  }

  connectWebSocket();
})();