/* ==========================================================================
   논문 영상 캔버스 장면 (tools/video/engine/player.html의 장면 자리(__SCENES__)에 들어간다)
   - 좌표계 1600×900 (렌더 때 1.2배 → 1920×1080). 하단 25%는 자막 자리라 중요한 내용은 y < 680.
   - 장면 함수 (c, p): c = 2D 컨텍스트, p = 컷 안 진행도 0~1. 같은 p에는 항상 같은 그림(seek 결정성).
   - 쓸 수 있는 값: W, H, C(팔레트), F(글꼴), clamp, lerp, E(이징), seg(p,a,b), img[키](spec.images()), QT(인용), DATA.
   - motion 클립이 덮는 컷은 장면이 없어도 된다(기본 화면 렌더에서 빠진다). 미리보기용 간단한 장면은 두는 편이 좋다.
   - 인용(Q) 컷은 장면을 적지 않으면 PDF 지면 형광펜(quoteScene)이 자동으로 붙는다.
   - 이 파일이 시작 뼈대다(아래 그리기 도구 + 주석 처리한 장면 예). 장면 문법: rules/video_rules.md 7절
   ========================================================================== */

/* ---------- 그리기 도구 (공통 함수) ---------- */
function bg(c,col=C.bg){c.fillStyle=col;c.fillRect(0,0,W,H);}
function txt(c,s,x,y,size,col=C.ink,al='left',wt=400,alpha=1){c.save();c.globalAlpha*=alpha;c.fillStyle=col;c.font=`${wt} ${size}px ${F}`;c.textAlign=al;c.textBaseline='alphabetic';c.fillText(s,x,y);c.restore();}
function tag(c,s='도식'){c.save();c.font=`500 20px ${F}`;const w=c.measureText(s).width+28;c.strokeStyle='rgba(31,35,51,0.35)';c.lineWidth=1.5;
  c.beginPath();c.roundRect(40,H-74,w,32,16);c.stroke();c.fillStyle='rgba(31,35,51,0.55)';c.textAlign='center';c.fillText(s,40+w/2,H-51);c.restore();}
function vignette(c,a=.55){const g=c.createRadialGradient(W/2,H/2,H*.35,W/2,H/2,H*1.05);g.addColorStop(0,'rgba(30,32,60,0.0)');g.addColorStop(1,`rgba(30,32,60,${a*.3})`);c.fillStyle=g;c.fillRect(0,0,W,H);}
function cover(c,im,fx,fy,z,smooth=true,alpha=1){ if(!im)return null;const iw=im.width,ih=im.height,s=Math.max(W/iw,H/ih)*z,vw=W/s,vh=H/s;
  const sx=clamp(fx*iw-vw/2,0,iw-vw),sy=clamp(fy*ih-vh/2,0,ih-vh);c.save();c.globalAlpha=alpha;c.imageSmoothingEnabled=smooth;c.drawImage(im,sx,sy,vw,vh,0,0,W,H);c.restore();
  return (u,v)=>[(u*iw-sx)*s,(v*ih-sy)*s];}
function figure(c,im,fx,fy,z,box=[.86,.78]){ if(!im)return;const iw=im.width,ih=im.height,s=Math.min(W*box[0]/iw,H*box[1]/ih)*z;
  const m=clamp((z-1)*2.2), x=W/2-(.5+(fx-.5)*m)*iw*s, y=H/2-(.5+(fy-.5)*m)*ih*s;
  c.save();c.shadowColor='rgba(30,32,60,0.165)';c.shadowBlur=40;c.fillStyle='#fff';c.fillRect(x,y,iw*s,ih*s);c.restore();c.drawImage(im,x,y,iw*s,ih*s);}
function quoteScene(c,p,sid){bg(c,'#F3F2F7');const q=QT[sid],im=img['q_'+sid];if(!im)return;
  const z=1+.07*E(p),s=W*.9/im.width*z,hy=(q.hl[0][1]+q.hl[q.hl.length-1][3])/2,x=W/2-im.width*s/2,y=H*.46-hy*im.height*s;
  c.drawImage(im,x,y,im.width*s,im.height*s);
  c.save();c.globalCompositeOperation='multiply';const n=q.hl.length;
  q.hl.forEach((r,i)=>{const k=seg(p,.08+i*.72/n,.08+(i+1)*.72/n);if(k<=0)return;c.fillStyle='rgba(240,196,90,.55)';
    c.fillRect(x+r[0]*im.width*s,y+r[1]*im.height*s-2,(r[2]-r[0])*im.width*s*k,(r[3]-r[1])*im.height*s+4);});c.restore();
  const g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,'rgba(243,242,247,0.92)');g.addColorStop(.22,'rgba(243,242,247,0.0)');g.addColorStop(.7,'rgba(243,242,247,0.0)');g.addColorStop(1,'rgba(243,242,247,0.95)');
  c.fillStyle=g;c.fillRect(0,0,W,H);txt(c,`논문 원문 · ${q.page}쪽`,60,70,20,C.dim);}
function bars(c,p,items,opt){ // items: [label, value, color]; opt: {lo,hi,base,title,cap,x0,w,y0,h}
  bg(c);const o=Object.assign({lo:50,hi:66,x0:220,w:1160,y0:170,h:470},opt),n=items.length,bw=o.w/n*.62;
  const Y=v=>o.y0+o.h-(v-o.lo)/(o.hi-o.lo)*o.h;
  c.strokeStyle='rgba(31,35,51,0.12)';c.lineWidth=1;
  for(let v=Math.ceil(o.lo/2)*2;v<=o.hi;v+=2){if(v%4)continue;txt(c,String(v),o.x0-14,Y(v)+7,19,C.dim,'right');}
  if(o.base){c.setLineDash([8,8]);c.strokeStyle='rgba(31,35,51,0.35)';c.beginPath();c.moveTo(o.x0,Y(o.base));c.lineTo(o.x0+o.w,Y(o.base));c.stroke();c.setLineDash([]);txt(c,'기준 모델 '+o.base,o.x0+o.w,Y(o.base)-10,19,C.dim,'right');}
  items.forEach((it,i)=>{const k=E(seg(p,.08+i*.5/n,.28+i*.5/n)),x=o.x0+(i+.5)*o.w/n-bw/2,v=o.lo+(it[1]-o.lo)*k;
    c.fillStyle=it[2]||'rgba(93,98,117,0.5)';c.fillRect(x,Y(v),bw,Y(o.lo)-Y(v));
    txt(c,it[1].toFixed(1),x+bw/2,Y(v)-12,24,it[2]===C.amber?C.amber:it[2]===C.rose?C.rose:C.ink,'center',600,k);
    txt(c,it[0],x+bw/2,Y(o.lo)+34,20,C.dim,'center');});
  if(o.title)txt(c,o.title,o.x0,110,26,C.ink,'left',400);if(o.cap)txt(c,o.cap,o.x0,H-46,18,C.dim);}

/* ---------- 컷 → 장면 ---------- */
const S={
// c01:(c,p)=>{bg(c);cover(c,img.hero,.5,.5,1+.06*E(p));vignette(c);},
// c16:(c,p)=>figure(c,img.fig_2,.5,.5,1+.05*E(p)),
};
// 컷 목록에 보이는 화면 설명(기획 검토용)
const VIS={};
