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
    width: 450,
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
      console.warn('[avatar_2] showAnswer failed:', e);
    }
  }

  function applyEmotion(emotionName) {
    if (!model) {
      pendingAction = emotionName;
      return;
    }

    activeEmotion = emotionName;
    console.log(`[avatar_2] ---> АКТИВИРОВАНА ЭМОЦИЯ: ${emotionName} <---`);

    clearTimeout(app.__expressionTimeout);
    app.__expressionTimeout = setTimeout(() => {
      activeEmotion = null;
      console.log('[avatar_2] ---> ЭМОЦИЯ СБРОШЕНА В ДЕФОЛТ <---');
    }, 3000); 
  }

  function handleServerMessage(raw) {
    try {
      const msg = typeof raw === 'string' ? JSON.parse(raw) : JSON.parse(raw.toString());
      console.log('[avatar_2] handleServerMessage parsed:', msg);
      
      if (msg?.emotion) {
        applyEmotion(msg.emotion);
      }
      if (msg?.answer) {
        showAnswer(msg.answer);
      }
    } catch (e) {
      console.warn('[avatar_2] handleServerMessage failed to parse:', raw, e);
    }
  }

  try {
    model = await Live2DModel.from('model_2/Pichu/Pichu.model3.json');
    app.stage.addChild(model);

    const scaleX = app.screen.width / model.width;
    const scaleY = app.screen.height / model.height;
    const scale = Math.min(scaleX, scaleY) * 1;

    model.scale.set(scale, scale);
    model.anchor.set(0.3, 0.3);
    model.x = (app.screen.width - model.width * scale) / 3;
    model.y = (app.screen.height - model.height * scale) / 2;

    console.log('Live2D Model 2 (Pichu) loaded successfully');

    app.ticker.add(() => {
      const coreModel = model?.internalModel?.coreModel;
      if (!coreModel) return;

      const paramsToReset = [
        'Param6', 'Param5', 'ShockMouthEXP', 'HappyEXP', 
        'ParamMouthForm', 'Param2', 'ParamCheek', 'ParamEyeBallX'
      ];
      paramsToReset.forEach(p => { try { coreModel.setParameterValueById(p, 0); } catch(e){} });

      try {
        coreModel.setParameterValueById('ParamEyeLOpen', 1);
        coreModel.setParameterValueById('ParamEyeROpen', 1);
      } catch(e) {}

      if (activeEmotion === 'happy') {
        try {
          coreModel.setParameterValueById('HappyEXP', 30);
          coreModel.setParameterValueById('ParamMouthForm', 0.5);
        } catch (e) {}

      } else if (activeEmotion === 'sad' || activeEmotion === 'dispair') {
        try {
          coreModel.setParameterValueById('Param6', 30);
          coreModel.setParameterValueById('Param5', 30);
          coreModel.setParameterValueById('ShockMouthEXP', 30);
        } catch (e) {}

      } else if (activeEmotion === 'angry') {
        try {
          coreModel.setParameterValueById('Param2', 30);
          coreModel.setParameterValueById('Param5', 0);
          coreModel.setParameterValueById('ParamMouthForm', -0.942);
          coreModel.setParameterValueById('ParamCheek', 30);
        } catch (e) {}

      } else if (activeEmotion === 'processing') {
        try {
          coreModel.setParameterValueById('ParamEyeBallX', -0.5);
        } catch (e) {}

      } else {
        try {
          coreModel.setParameterValueById('ParamEyeBallX', 0);
          coreModel.setParameterValueById('ParamMouthForm', 0);
        } catch (e) {}
      }
    });

    if (pendingAction) {
      const emotionToRun = pendingAction;
      pendingAction = null;
      applyEmotion(emotionToRun);
    }
  } catch (err) {
    console.error('Failed to load Live2D Model 2:', err);
    return;
  }

  let reconnectAttempts = 0;
  let reconnectTimer = null;
  let ws = null;

  function connectWebSocket() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    
    const wsUrl = 'ws://127.0.0.1:8080';
    ws = new WebSocket(wsUrl);
    
    ws.addEventListener('open', () => {
      reconnectAttempts = 0;
      showAnswer('Подключено к серверу! Можете говорить...');
    });

    ws.addEventListener('message', (event) => handleServerMessage(event.data));

    ws.addEventListener('close', () => {
      showAnswer('Потеряно соединение с сервером. Переподключение...');
      const delay = Math.min(3000 * (reconnectAttempts + 1), 15000);
      reconnectAttempts++;
      reconnectTimer = setTimeout(connectWebSocket, delay);
    });

    ws.addEventListener('error', (err) => console.error('[avatar_2] WS error:', err));
    window.__avatarWs = ws;
  }

  connectWebSocket();
})();