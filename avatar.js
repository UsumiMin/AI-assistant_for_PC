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

  try {
    const model = await Live2DModel.from('model/mao_pro_en/runtime/mao_pro.model3.json');

    app.stage.addChild(model);

    const scaleX = app.screen.width / model.width;
    const scaleY = app.screen.height / model.height;
    const scale = Math.min(scaleX, scaleY);

    model.scale.set(scale, scale);
    model.anchor.set(0.3, 0.3);
    model.x = (app.screen.width - model.width * scale) / 2;
    model.y = (app.screen.height - model.height * scale) / 2;

    console.log('Live2D model loaded successfully');
  } catch (err) {
    console.error('Failed to load Live2D model:', err);
  }
})();

