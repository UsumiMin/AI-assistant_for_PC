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
  let activeEmotion = null; // Хранит текущую активную эмоцию ('happy', 'sad', 'processing' или null)

  function applyEmotion(emotionName) {
    if (!model) {
      pendingAction = emotionName;
      return;
    }

    activeEmotion = emotionName;
    console.log(`[avatar] ---> АКТИВИРОВАНА ЭМОЦИЯ: ${emotionName} <---`);

    // Таймер сброса эмоции обратно в дефолтное состояние через 3 секунды
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
      
      // Считываем эмоцию, пришедшую от сервера
      if (msg?.emotion) {
        applyEmotion(msg.emotion);
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

    // Главный тикер рендеринга PIXI — гарантирует, что параметры не затрутся анимацией покоя
    app.ticker.add(() => {
      const coreModel = model?.internalModel?.coreModel;
      if (!coreModel) return;

      if (activeEmotion === 'happy') {
        try {
          // Улыбка с открытым ртом
          coreModel.setParameterValueById('ParamA', 0.6); // Приоткрываем рот (звук "А")
          coreModel.setParameterValueById('ParamMouthUp', 1); // Тянем уголки губ вверх
          coreModel.setParameterValueById('ParamMouthDown', 0);

          // Радостный прищур глаз и легкий румянец
          coreModel.setParameterValueById('ParamEyeLSmile', 1);
          coreModel.setParameterValueById('ParamEyeRSmile', 1);
          coreModel.setParameterValueById('ParamCheek', 0.5);

          // Брови в нейтрально-приподнятом положении
          coreModel.setParameterValueById('ParamBrowLForm', 0);
          coreModel.setParameterValueById('ParamBrowRForm', 0);
          coreModel.setParameterValueById('ParamBrowLAngle', 0);
          coreModel.setParameterValueById('ParamBrowRAngle', 0);

          // Глаза остаются открытыми, но теплыми за счет Smile-параметров
          coreModel.setParameterValueById('ParamEyeLOpen', 1);
          coreModel.setParameterValueById('ParamEyeROpen', 1);
        } catch (e) {}

      } else if (activeEmotion === 'sad') {
        try {
          // Грусть: рот закрыт, уголки опущены вниз
          coreModel.setParameterValueById('ParamA', 0);
          coreModel.setParameterValueById('ParamMouthUp', 0);
          coreModel.setParameterValueById('ParamMouthDown', 1);

          // Брови домиком (значения -1 взяты на основе exp_06.json)
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
          // Ожидание/Думает: рот слегка приоткрыт округлой формой "О"
          coreModel.setParameterValueById('ParamO', 0.4);
          coreModel.setParameterValueById('ParamA', 0);
          coreModel.setParameterValueById('ParamMouthUp', 0);
          coreModel.setParameterValueById('ParamMouthDown', 0);

          // Отводим взгляд зрачков влево
          coreModel.setParameterValueById('ParamEyeBallX', -0.5);

          coreModel.setParameterValueById('ParamEyeLSmile', 0);
          coreModel.setParameterValueById('ParamEyeRSmile', 0);
          coreModel.setParameterValueById('ParamCheek', 0);
          coreModel.setParameterValueById('ParamBrowLForm', 0);
          coreModel.setParameterValueById('ParamBrowRForm', 0);
        } catch (e) {}

      } else {
        // ПОЛНЫЙ СБРОС В ДЕФОЛТ (Когда нет активных команд от сервера)
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

  // Настройка WebSocket подключения
  try {
    if (window.__avatarWs) {
      console.log('[avatar] Closing old global WebSocket connection...');
      window.__avatarWs.close();
    }

    const wsUrl = 'ws://127.0.0.1:8080';
    const ws = new WebSocket(wsUrl);
    window.__avatarWs = ws;

    ws.addEventListener('open', () => {
      console.log('[avatar] WebSocket connected:', wsUrl);
    });

    ws.addEventListener('message', (event) => {
      console.log('[avatar] WebSocket message raw:', event?.data);
      handleServerMessage(event.data);
    });

    ws.addEventListener('close', (e) => {
      console.warn('[avatar] WebSocket closed:', e?.code, e?.reason);
    });

    ws.addEventListener('error', (err) => {
      console.error('[avatar] WebSocket error:', err);
    });

  } catch (err) {
    console.error('[avatar] Failed to setup WebSocket:', err);
  }
})();