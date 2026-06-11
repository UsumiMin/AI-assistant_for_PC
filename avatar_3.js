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
    width: 400,
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
      console.warn('[avatar_3] showAnswer failed:', e);
    }
  }

  function applyEmotion(emotionName) {
    if (!model) {
      pendingAction = emotionName;
      return;
    }

    activeEmotion = emotionName;
    console.log(`[avatar_3] ---> АКТИВИРОВАНА ЭМОЦИЯ: ${emotionName} <---`);

    clearTimeout(app.__expressionTimeout);
    app.__expressionTimeout = setTimeout(() => {
      activeEmotion = null;
      console.log('[avatar_3] ---> ЭМОЦИЯ СБРОШЕНА В ДЕФОЛТ <---');
    }, 3000); 
  }

  function handleServerMessage(raw) {
    try {
      const msg = typeof raw === 'string' ? JSON.parse(raw) : JSON.parse(raw.toString());
      console.log('[avatar_3] handleServerMessage parsed:', msg);
      
      if (msg?.emotion) {
        applyEmotion(msg.emotion);
      }
      if (msg?.answer) {
        showAnswer(msg.answer);
      }
    } catch (e) {
      console.warn('[avatar_3] handleServerMessage failed to parse:', raw, e);
    }
  }

  try {
    // Путь до второй модели из твоего запроса
    model = await Live2DModel.from('model_3/Reyna High Tracking/reynavt.model3.json');
    app.stage.addChild(model);

    // Сохраняем те же настройки сцены для совместимости с mini-mode
    const scaleX = app.screen.width / model.width;
    const scaleY = app.screen.height / model.height;
    const scale = Math.min(scaleX, scaleY) * 2;

    model.scale.set(scale, scale);
    model.anchor.set(0.3, 0.3);
    model.x = (app.screen.width - model.width * scale) / 5;
    model.y = (app.screen.height - model.height * scale) / 1.5;

    console.log('Live2D Model 3 (xl) loaded successfully');

    app.ticker.add(() => {
      const coreModel = model?.internalModel?.coreModel;
      if (!coreModel) return;

      // Предварительный сброс параметров новой модели для покадрового рендеринга //
      const paramsToReset = [
        'ParamMouthForm', 'Param14', 'ParamBrowRAngle', 'ParamBrowRForm', 'ParamBrowRY', 
        'ParamMouthForm', 'ParamBrowLAngle', 'ParamBrowLForm', 'ParamBrowLX',
        'ParamBrowRX', 'ParamBrowLY'
      ];
      paramsToReset.forEach(p => { try { coreModel.setParameterValueById(p, 0); } catch(e){} });

      try {
        coreModel.setParameterValueById('ParamEyeLOpen', 1);
        coreModel.setParameterValueById('ParamEyeROpen', 1);
      } catch(e) {}

      if (activeEmotion === 'happy') {
        try {
          coreModel.setParameterValueById('Param54', 30);
          coreModel.setParameterValueById('ParamMouthForm', 0.5);
        } catch (e) {}

      } else if (activeEmotion === 'sad' || activeEmotion === 'dispair') {
        try {
          coreModel.setParameterValueById('ParamEyeRSmile', 0.0);
          coreModel.setParameterValueById('ParamEyeLSmile', 0.0);
          coreModel.setParameterValueById('ParamBrowLAngle', -0.37902259826660159);
          coreModel.setParameterValueById('ParamBrowRAngle', -0.37902259826660159);
          coreModel.setParameterValueById('ParamMouthForm', -0.7201440334320068);
        } catch (e) {}

      } else if (activeEmotion === 'processing') {
        try {
          coreModel.setParameterValueById('Param55', -0.5);
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
    console.error('Failed to load Live2D Model 3:', err);
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

    ws.addEventListener('error', (err) => console.error('[avatar_3] WS error:', err));
    window.__avatarWs = ws;
  }

  connectWebSocket();
})();