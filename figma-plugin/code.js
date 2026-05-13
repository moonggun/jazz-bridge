try {
  figma.showUI(__html__, { width: 420, height: 560 });
} catch (e) {
  figma.notify('UI 오류: ' + String(e));
  figma.closePlugin();
}

var fontsLoaded = false;

var FONTS = [
  { family: 'Inter', style: 'Regular' },
  { family: 'Inter', style: 'Medium' },
  { family: 'Inter', style: 'Semi Bold' },
  { family: 'Inter', style: 'Bold' },
];

function toRGB(c) {
  if (!c) return { r: 0, g: 0, b: 0 };
  return { r: c.r, g: c.g, b: c.b };
}

function getFontName(weight) {
  if (weight >= 700) return { family: 'Inter', style: 'Bold' };
  if (weight >= 600) return { family: 'Inter', style: 'Semi Bold' };
  if (weight >= 500) return { family: 'Inter', style: 'Medium' };
  return { family: 'Inter', style: 'Regular' };
}

figma.ui.onmessage = function (msg) {
  if (!msg || !msg.type) return;

  if (msg.type === 'START') {
    Promise.all(FONTS.map(function (f) { return figma.loadFontAsync(f); }))
      .then(function () {
        fontsLoaded = true;
        figma.ui.postMessage({ type: 'FONTS_READY' });
      })
      .catch(function (e) {
        figma.notify('폰트 오류: ' + String(e));
        figma.ui.postMessage({ type: 'ERROR', error: String(e) });
      });
    return;
  }

  if (msg.type === 'CREATE_FRAME') {
    try {
      var frameWidth  = msg.width  || 375;
      var frameHeight = msg.height || 812;
      var elements    = msg.elements || [];
      var idx         = msg.index   || 0;

      var frame = figma.createFrame();
      frame.name = msg.name + ' — ' + msg.title;
      frame.resize(frameWidth, frameHeight);
      frame.x = idx * (frameWidth + 40);
      frame.y = 0;
      frame.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
      frame.clipsContent = true;

      for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        var x = Math.max(0, el.x || 0);
        var y = Math.max(0, el.y || 0);
        var w = Math.max(1, Math.min(el.w || 1, frameWidth  - x));
        var h = Math.max(1, Math.min(el.h || 1, frameHeight - y));

        if (el.text && !el.hasChildren) {
          try {
            var tn = figma.createText();
            tn.fontName = fontsLoaded ? getFontName(el.fontWeight) : { family: 'Inter', style: 'Regular' };
            tn.characters = String(el.text);
            tn.fontSize = Math.max(1, el.fontSize || 14);
            if (el.color) {
              tn.fills = [{ type: 'SOLID', color: toRGB(el.color) }];
            }
            tn.x = x;
            tn.y = y;
            frame.appendChild(tn);
          } catch (_te) { /* skip bad text node */ }

        } else if (el.bgColor || el.hasBorder || el.borderRadius > 0) {
          try {
            var rect = figma.createRectangle();
            rect.x = x;
            rect.y = y;
            rect.resize(w, h);

            if (el.bgColor) {
              var opacity = (el.bgOpacity !== undefined) ? el.bgOpacity : 1;
              rect.fills = [{ type: 'SOLID', color: toRGB(el.bgColor), opacity: opacity }];
            } else {
              rect.fills = [];
            }

            if (el.borderRadius > 0) {
              rect.cornerRadius = Math.min(el.borderRadius, Math.min(w, h) / 2);
            }

            if (el.hasBorder && el.borderColor) {
              rect.strokes = [{ type: 'SOLID', color: toRGB(el.borderColor) }];
              rect.strokeWeight = Math.max(0.5, el.borderWidth || 0.5);
              rect.strokeAlign = 'INSIDE';
            }

            frame.appendChild(rect);
          } catch (_re) { /* skip bad rect */ }
        }
      }

      figma.ui.postMessage({ type: 'FRAME_DONE', name: msg.name });
    } catch (e) {
      figma.notify('프레임 오류: ' + String(e));
      figma.ui.postMessage({ type: 'FRAME_ERROR', name: msg.name, error: String(e) });
    }
    return;
  }

  if (msg.type === 'ALL_DONE') {
    figma.notify('🎷 Jazz Bridge 18개 화면 생성 완료!');
    return;
  }
};
