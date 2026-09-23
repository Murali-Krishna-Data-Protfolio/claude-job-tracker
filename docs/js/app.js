(function(){
  var canvas = document.getElementById('network');
  var ctx = canvas.getContext('2d');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hero = document.querySelector('.hero');
  var w, h, pts = [];
  var N = 46;

  function size(){
    var rect = hero.getBoundingClientRect();
    w = canvas.width = rect.width * devicePixelRatio;
    h = canvas.height = rect.height * devicePixelRatio;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
  }

  function init(){
    pts = [];
    for (var i=0;i<N;i++){
      pts.push({
        x: Math.random()*w,
        y: Math.random()*h,
        vx: (Math.random()-0.5)*0.15*devicePixelRatio,
        vy: (Math.random()-0.5)*0.15*devicePixelRatio
      });
    }
  }

  function frame(){
    ctx.clearRect(0,0,w,h);
    for (var i=0;i<pts.length;i++){
      var p = pts[i];
      if (!reduce){ p.x += p.vx; p.y += p.vy; }
      if (p.x<0||p.x>w) p.vx*=-1;
      if (p.y<0||p.y>h) p.vy*=-1;
    }
    for (var i=0;i<pts.length;i++){
      for (var j=i+1;j<pts.length;j++){
        var a = pts[i], b = pts[j];
        var dx=a.x-b.x, dy=a.y-b.y;
        var d = Math.sqrt(dx*dx+dy*dy);
        var maxD = 130*devicePixelRatio;
        if (d < maxD){
          ctx.strokeStyle = 'rgba(27,63,115,' + (0.10*(1-d/maxD)) + ')';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(a.x,a.y);
          ctx.lineTo(b.x,b.y);
          ctx.stroke();
        }
      }
    }
    for (var i=0;i<pts.length;i++){
      ctx.fillStyle = i % 5 === 0 ? 'rgba(249,115,22,0.45)' : 'rgba(27,63,115,0.35)';
      ctx.beginPath();
      ctx.arc(pts[i].x, pts[i].y, 1.6*devicePixelRatio, 0, Math.PI*2);
      ctx.fill();
    }
    if (!reduce) requestAnimationFrame(frame);
  }

  try{
    size();
    init();
    frame();
    window.addEventListener('resize', function(){ size(); init(); if(reduce) frame(); });
  }catch(e){}
})();

(function(){
  try{
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches){
      var flow = document.getElementById('flowSvg');
      if (flow && flow.pauseAnimations) flow.pauseAnimations();
    }
  }catch(e){}
})();
