'本包页面网格。侧栏、对话、右栏、文件树和根帧列都在页面网格样式这一份常量里。'

__all__=['页面网格样式','页面样式已登记','记下页面样式已登记']

已登记页面样式=False

def 页面样式已登记():
    '本进程是否已经把页面网格样式交给页面'
    return 已登记页面样式

def 记下页面样式已登记():
    '标记本进程已经登记过。之后再进入页面不再追加同一份样式。'
    global 已登记页面样式
    已登记页面样式=True

页面网格样式='''
html,body{height:100%;margin:0;overflow:hidden;background:var(--dsw-alias-bg-base,#f9fafb);color:var(--dsw-alias-label-primary,#111827);font-family:var(--dsw-font-family)}
.nicegui-content,.q-page{max-width:none !important;width:100% !important;height:100vh !important;margin:0 !important;padding:0 !important;overflow:hidden !important;background:var(--dsw-alias-bg-base)}
.页面{position:relative;display:grid;grid-template-columns:280px minmax(0,1fr) minmax(0,0px);grid-template-rows:minmax(0,1fr);width:100%;height:100%;margin:0;overflow:hidden;background:var(--dsw-alias-bg-base);color:var(--dsw-alias-label-primary)}
.页面[data-animating]{transition:grid-template-columns var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.页面[data-dragging],.页面[data-rightbar-fullscreen],.页面[data-rightbar-instant]{transition:none}
.拖柄{position:absolute;grid-area:1 / 1 / 2 / -1;top:0;bottom:0;width:8px;margin-left:-4px;cursor:col-resize;z-index:11;touch-action:none}
.页面[data-animating] .拖柄{transition:left var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.页面[data-dragging] .拖柄,.页面[data-rightbar-fullscreen] .拖柄,.页面[data-rightbar-instant] .拖柄{transition:none}
@media (prefers-reduced-motion:reduce){.页面[data-animating],.页面[data-animating] .拖柄{transition:none}}
.页面>.会话列{grid-column:1;grid-row:1;align-self:stretch}
.页面>.对话列{grid-column:2;grid-row:1}
.页面>.右栏轨{grid-column:3;grid-row:1}
.会话列{width:100%;min-width:0;min-height:0;height:100%;overflow:hidden;display:flex;flex-direction:column;background:var(--dsw-specific-sidebar-fill);border-right:0.5px solid var(--dsw-alias-border-l3)}
.侧栏根{min-height:0;width:100%;flex:1 1 auto}
.侧栏根{--dsh-sidebar-inline-padding:12px;--dsh-scrollbar-thumb:var(--dsw-alias-scrollbar-bg-l2);--dsh-scrollbar-thumb-hover:var(--dsw-alias-scrollbar-hover-l2);display:flex;flex-direction:column;height:100%;width:100%;box-sizing:border-box;padding:6px var(--dsh-sidebar-inline-padding);color:var(--dsw-alias-label-primary);font-size:14px}
.侧栏根.左栏收起{padding:18px 10px 6px}
.侧栏根.淡出>*{opacity:0;transition:opacity 150ms var(--ds-ease-in-out)}
.侧栏根.轨入 .图标钮,.侧栏根.轨入 .新会话条,.侧栏根.轨入 .浏览区{animation:轨入 150ms var(--ds-ease-in-out) backwards}
.侧栏根.轨入 .栏脚{animation:轨淡入 150ms var(--ds-ease-in-out) backwards}
@keyframes 轨入{from{opacity:0;transform:translateX(49px)}}
@keyframes 轨淡入{from{opacity:0}}
.侧栏根.静条{--dsh-scrollbar-thumb:transparent;--dsh-scrollbar-thumb-hover:transparent}
@media (prefers-reduced-motion:reduce){.侧栏根.淡出>*,.侧栏根.轨入 .图标钮,.侧栏根.轨入 .新会话条,.侧栏根.轨入 .浏览区,.侧栏根.轨入 .栏脚{transition:none;animation:none}}
.侧栏顶{display:flex;width:100%;height:60px;align-items:center;justify-content:flex-end;flex-wrap:nowrap;gap:8px;padding:8px 0 8px 4px;box-sizing:border-box;margin-bottom:4px}
.左栏收起 .侧栏顶{height:36px;padding:0;margin-bottom:12px;justify-content:flex-start}
button.q-btn.品牌{flex:1;min-width:0;min-height:24px;height:24px;padding:0;justify-content:flex-start;background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important}
button.q-btn.品牌:hover{background:transparent !important}
button.q-btn.品牌 .q-btn__content{justify-content:flex-start;flex-wrap:nowrap;gap:8px}
.品牌{flex:1;min-width:0;align-items:center;flex-wrap:nowrap;gap:8px;height:24px;color:var(--dsw-alias-label-primary);overflow:hidden}
.品牌名{display:inline-flex;align-items:center;min-width:0;height:24px;font-size:18px;font-weight:600;line-height:24px;letter-spacing:0.04em}
.左栏收起 .品牌{display:none}
.品牌 .鱼标,.品牌 .品牌字标,.英雄 .鱼标{display:flex;align-items:center;color:var(--dsw-alias-label-primary)}
.品牌 svg,.英雄 .鱼标 svg{display:block}
.工作区行{position:relative;width:100%;align-items:center;justify-content:flex-start;padding-left:8px;flex-wrap:nowrap}
.工作区菜单{position:absolute;left:8px;bottom:calc(100% + 4px);z-index:21;min-width:180px;padding:4px;border-radius:var(--dsw-radius-lg);background:var(--dsw-specific-menu);box-shadow:var(--dsw-elevation-panel)}
.对话活动 .工作区行{display:none}
button.q-btn.工作区钮{width:auto;max-width:min(100%,360px);height:28px;min-height:28px;padding:0 8px;background:transparent !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important;font-size:13px;line-height:20px;font-weight:500}
button.q-btn.工作区钮 .q-btn__content{gap:4px;flex-wrap:nowrap}
button.q-btn.工作区钮:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.工作区文{font-size:13px;line-height:20px;font-weight:500;white-space:nowrap}
button.q-btn.图标钮.内标{background-image:none !important}
button.q-btn.图标钮.内标 svg,button.q-btn.添加钮 svg,button.q-btn.发送钮 svg,button.q-btn.新会话条 svg,button.q-btn.设置钮 svg,button.q-btn.工作区钮 svg{display:block;flex:none}
button.q-btn.图标钮{width:28px;height:28px;min-height:28px;padding:0;border-radius:var(--dsw-radius-sm);background-color:transparent !important;background-image:var(--标) !important;background-repeat:no-repeat !important;background-position:center !important;background-size:16px 16px !important;color:var(--dsw-alias-label-secondary) !important;box-shadow:none !important}
button.q-btn.图标钮 .block{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
button.q-btn.侧栏开关{color:var(--dsw-alias-label-secondary) !important}
.侧栏开关 .轨标{display:none}
.左栏收起 button.q-btn.侧栏开关{width:36px;height:36px;min-height:36px;border-radius:var(--dsw-radius-md);color:var(--dsw-alias-label-primary) !important}
.左栏收起 .侧栏开关 .面板标{display:none}
.左栏收起 .侧栏开关 .轨标{display:flex}
.左栏收起 button.q-btn.侧栏开关:hover{background-color:transparent !important}
.左栏收起 .侧栏开关:hover .面板标{display:block}
.左栏收起 .侧栏开关:hover .轨标{display:none}
.新会话条 .轨标,.设置钮 .轨标{display:none}
.左栏收起 .新会话条 .宽标{display:none}
.左栏收起 .新会话条 .轨标{display:block}
.左栏收起 .设置钮 svg{width:18px;height:18px}
button.q-btn.右栏入口{margin-left:auto}
button.q-btn.右栏入口 svg{transform:scaleX(-1)}
button.q-btn.关闭钮{--标:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23111111' d='M6.4 5l5.6 5.6L17.6 5 19 6.4 13.4 12 19 17.6 17.6 19 12 13.4 6.4 19 5 17.6 10.6 12 5 6.4z'/%3E%3C/svg%3E")}
button.q-btn.图标钮:hover{background-color:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.新会话条{flex:none;width:100%;box-sizing:border-box;height:38px;margin:0 0 12px;padding:8px 12px;border:0.5px solid var(--dsw-alias-border-l3) !important;border-radius:var(--dsw-radius-md);background:var(--dsw-alias-button-elevated-fill) !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important;font-size:14px;font-weight:500;line-height:22px}
button.q-btn.新会话条 .q-btn__content{gap:6px;flex-wrap:nowrap}
button.q-btn.新会话条:hover{background:var(--dsw-alias-button-floating-hover) !important}
.左栏收起 button.q-btn.新会话条{width:36px;height:36px;min-height:36px;padding:0;margin:0 0 12px;border-color:transparent !important;background:transparent !important}
.左栏收起 button.q-btn.新会话条:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.左栏收起 .新会话文{display:none}
.浏览区{flex:1;min-height:0;width:100%;display:flex;flex-direction:column;margin-left:-4px;margin-right:calc(-1 * var(--dsh-sidebar-inline-padding));padding-left:4px;overflow:hidden}
.左栏收起 .浏览区{margin-left:0;margin-right:0;padding-left:0}
.栏脚{flex:none;display:flex;flex-direction:column;margin-top:auto;width:100%}
.左栏收起 .栏脚{align-items:center}
.会话清单{flex:1 1 auto;width:100%;min-height:0;overflow:auto;background:transparent;gap:0;margin-left:-4px;padding:0 8px 16px 4px;scrollbar-gutter:stable}
.会话清单>*+*{margin-top:2px}
.左栏收起 .会话清单{display:none}
.分区头{display:flex;width:100%;height:36px;align-items:center;justify-content:flex-end;flex-wrap:nowrap;gap:4px;padding-left:4px;margin:2px -4px 4px 0;box-sizing:border-box;border-radius:var(--dsw-radius-md);overflow:hidden;color:var(--dsw-alias-label-tertiary)}
.分区标{flex:none;max-width:45%;min-width:0;margin-right:auto;overflow:hidden;line-height:20px;font-size:14px;white-space:nowrap;opacity:1;transition:max-width 180ms var(--ds-ease-in-out),opacity 120ms var(--ds-ease-in-out)}
.分区标.分区标隐{max-width:0;opacity:0}
.会话搜索{flex:1;min-width:0}
.会话搜索 .q-field__control,.会话搜索 .q-field__native,.会话搜索 .q-field__marginal{min-height:32px;height:32px;background:transparent !important;border:none !important;box-shadow:none !important}
.会话搜索 input{font-size:13px;color:var(--dsw-alias-label-primary)}
button.q-btn.搜索钮{width:28px;height:28px;min-height:28px;min-width:28px;padding:0;border-radius:var(--dsw-radius-sm);background:transparent !important;color:var(--dsw-alias-label-secondary) !important;box-shadow:none !important}
button.q-btn.搜索钮:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.会话行{width:100%;height:32px;min-height:32px;margin:0;padding:0 8px;justify-content:flex-start;border-radius:var(--dsw-radius-md);background:transparent !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important;font-weight:400;font-size:14px}
button.q-btn.会话行 .q-btn__content{gap:0;justify-content:flex-start;flex-wrap:nowrap;width:100%;min-width:0}
.会话题{flex:1;min-width:0;margin:0 6px 0 4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;line-height:20px;text-align:left}
.状态槽{flex:none;width:16px;height:20px;display:inline-flex;align-items:center;justify-content:center}
button.q-btn.会话行:hover,button.q-btn.会话行.会话当前{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.设置钮{margin-top:auto;width:100%;height:42px;min-height:42px;padding:0 10px 0 8px;justify-content:flex-start;border-radius:var(--dsw-radius-md);background:transparent !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important;font-size:14px;line-height:22px}
button.q-btn.设置钮 .q-btn__content{gap:8px;justify-content:flex-start;flex-wrap:nowrap}
button.q-btn.设置钮:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.左栏收起 button.q-btn.设置钮{width:36px;height:36px;min-height:36px;padding:0;align-self:center}
.左栏收起 .设置文{display:none}
.对话列{position:relative;min-width:0;height:100%;display:flex;flex-direction:column;overflow:hidden;background:var(--dsw-alias-bg-base);color:var(--dsw-alias-label-primary)}
.对话头{flex:none;width:100%;min-height:0;align-items:center;flex-wrap:nowrap;padding:10px 28px 10px 20px;box-sizing:border-box;border-bottom:0.5px solid var(--dsw-alias-border-l3)}
.对话英雄 .对话头{border-bottom:none;padding-bottom:0}
.会话标题{flex:1;min-width:0;min-height:30px;display:flex;align-items:center;font-size:14px;font-weight:500;line-height:20px;padding:0}
.身{--dsh-chat-content-width:clamp(680px,64%,920px);--dsh-composer-card-max-width:calc(var(--dsh-chat-content-width) + 32px);--dsh-composer-side-clearance:16px;--dsh-composer-text-max-height:336px;flex:1 1 auto;width:100%;min-height:0;display:flex;flex-direction:column;align-items:stretch;overflow:hidden}
.对话英雄 .身{justify-content:center;align-items:center;gap:12px;overflow:auto}
.消息列{flex:1 1 auto;width:100%;min-height:0;overflow-x:hidden;overflow-y:auto;display:flex;flex-direction:column;align-items:center;background:transparent}
.对话英雄 .消息列{flex:none;overflow:visible;width:100%;max-width:var(--dsh-composer-card-max-width)}
.英雄{display:flex;width:100%;justify-content:center;align-items:center;flex-wrap:wrap;column-gap:10px;row-gap:12px}
.鱼标盒{display:inline-flex;flex:none;align-items:center;justify-content:center}
.鱼标盒 .鱼标{display:block;overflow:visible;transform-origin:50% 60%}
@keyframes 鱼游{0%,100%{transform:none}35%{transform:rotate(-4deg) translate(-0.4px,-0.9px)}70%{transform:rotate(1.6deg) translate(0.3px,0.2px)}}
@media (hover:hover) and (prefers-reduced-motion:no-preference){.鱼标盒:hover .鱼标{animation:鱼游 1.6s ease-in-out infinite}}
.标题组{display:inline-flex;width:auto;flex:none;align-items:center;justify-content:flex-start;flex-wrap:nowrap;column-gap:7px}
.英雄标题{font-size:26px;line-height:32px;font-weight:500;color:var(--dsw-alias-label-primary);white-space:nowrap}
.会话标题{white-space:nowrap}
.预览徽{margin-top:2px;padding:1px 7px 0;border:0.5px solid var(--dsw-alias-interactive-bg-hover);border-radius:999px;background:var(--dsw-alias-state-business-tertiary);color:var(--dsw-alias-label-primary-bluish);font-family:var(--ds-font-family-code);font-size:12px;line-height:18px;font-weight:500}
.对话活动 .消息列{width:100%;max-width:none;margin:0;gap:0;padding:16px calc(var(--dsh-composer-side-clearance) + 16px);align-items:stretch;container-type:inline-size}
.消息内{width:100%;max-width:var(--dsh-chat-content-width);margin:0 auto;align-items:stretch;gap:0}
.消息内>*+*{margin-top:6px}
.消息内>.助手行{margin-top:12px}
.用户行{align-self:flex-end;align-items:flex-end;max-width:min(calc(var(--dsh-chat-content-width, 748px) * 0.702),82%);gap:6px}
.消息动作{display:flex;align-items:center;gap:8px;height:calc(28px + var(--dsh-content-font-delta,0px));color:var(--dsw-alias-label-tertiary)}
.消息动作尾{margin-left:0}
button.q-btn.消息钮{width:calc(28px + var(--dsh-content-font-delta,0px));height:calc(28px + var(--dsh-content-font-delta,0px));min-width:0;min-height:0;padding:6px;border-radius:var(--dsw-radius-sm);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-tertiary) !important}
button.q-btn.消息钮 svg{width:calc(15px + var(--dsh-content-font-delta,0px));height:calc(15px + var(--dsh-content-font-delta,0px))}
.消息动作尾 button.q-btn.消息钮 svg{width:calc(17px + var(--dsh-content-font-delta,0px));height:calc(17px + var(--dsh-content-font-delta,0px))}
button.q-btn.消息钮:hover{background:var(--dsw-alias-interactive-bg-hover) !important;color:var(--dsw-alias-label-secondary) !important}
@media (hover:hover){.用户行 .消息动作{opacity:0;transition:opacity 80ms ease}.用户行:hover .消息动作,.用户行:focus-within .消息动作{opacity:1}}
.气泡{max-width:100%;background:var(--dsw-specific-bubble);border-radius:var(--dsw-radius-xl);padding:10px 16px;font-size:var(--dsh-content-font-size,14px);line-height:calc(22px + (var(--dsh-content-font-size,14px) - 14px));color:var(--dsw-alias-label-primary);white-space:pre-wrap;word-break:break-word}
.助手行{align-self:stretch;width:100%;display:flex;flex-direction:column;gap:16px}
.助手文{min-width:0;overflow-wrap:anywhere;font-size:var(--dsh-content-font-size,14px);line-height:calc(24px + (var(--dsh-content-font-size,14px) - 14px));color:var(--dsw-alias-label-primary)}
.助手文 p{margin:16px 0}
.助手文 h1,.助手文 h2,.助手文 h3{margin:32px 0 16px}
.助手文 h4,.助手文 h5,.助手文 h6{margin:16px 0}
.助手文 strong{font-weight:600}
.助手文 a{color:var(--dsw-alias-link);font-weight:500;text-decoration:none}
.助手文 a:hover{text-decoration:underline dotted var(--dsw-alias-link);text-underline-offset:3px}
.助手文 pre{margin:16px 0;padding:12px;border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-1);overflow:auto}
.助手文 code,.助手文 pre{font-family:var(--ds-font-family-code)}
.工具调用{display:flex;flex-direction:column;width:100%;min-width:0}
.工具行头{position:relative;width:100%;height:calc(24px + var(--dsh-content-font-delta,0px));align-items:center;flex-wrap:nowrap;min-width:0;color:var(--dsw-alias-label-tertiary);cursor:pointer}
.工具行头:hover{color:var(--dsw-alias-label-secondary)}
.工具调用 .题{flex:none;font-weight:400;font-size:var(--dsh-content-font-size-secondary,13px);line-height:calc(24px + var(--dsh-content-font-delta,0px))}
.工具调用 .点{flex:none;width:2px;height:2px;margin:0 8px;border-radius:1px;background:var(--dsw-alias-label-caption)}
.工具调用 .要,.工具调用 .要尾{font-size:var(--dsh-content-font-size-secondary,13px);line-height:calc(24px + var(--dsh-content-font-delta,0px))}
.工具调用 .要{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.工具调用 .要尾{flex:none;margin-left:4px;white-space:nowrap}
.工具调用 .要错{color:var(--dsw-alias-state-error-primary)}
.工具调用 .要止{color:var(--dsw-alias-state-warn-label)}
button.q-btn.文件链{position:relative;z-index:1;flex:0 1 auto;min-width:0;height:auto;min-height:0;margin:0;padding:0;background:none !important;box-shadow:none !important;color:inherit !important;font-size:var(--dsh-content-font-size-secondary,13px);line-height:calc(24px + var(--dsh-content-font-delta,0px));text-decoration:underline dotted;text-underline-offset:3px}
button.q-btn.检视{align-self:flex-start;height:auto;min-height:0;margin:4px 0 2px 4px;padding:2px 8px;border:0.5px solid var(--dsw-alias-border-l3) !important;border-radius:999px;background:var(--dsw-alias-bg-base) !important;color:var(--dsw-alias-label-secondary) !important;box-shadow:none !important;font-size:11px;line-height:16px;opacity:0}
.工具调用:hover button.q-btn.检视{opacity:1}
button.q-btn.检视:hover{background:var(--dsw-alias-interactive-bg-hover-solid) !important;color:var(--dsw-alias-label-primary) !important}
.进出卡{display:flex;flex-direction:column;margin:4px 0 4px 4px;border:0.5px solid var(--dsw-alias-border-l1);border-radius:var(--dsw-radius-lg);background:var(--dsw-alias-markdown-code-block);overflow:hidden}
.进出节{display:grid;grid-template-columns:max-content 1fr;column-gap:14px;align-items:baseline;padding:12px 16px;max-height:150px;overflow:auto}
.进出标{color:var(--dsw-alias-label-caption)}
.进出文{min-width:0;white-space:pre-wrap;word-break:break-word;color:var(--dsw-alias-label-secondary)}
.进出线{flex:none;height:0.5px;background:var(--dsw-alias-border-l2)}
.消息角色{font-size:12px;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.消息正文{white-space:pre-wrap;word-break:break-word;font-size:var(--dsh-content-font-size,14px);line-height:calc(24px + (var(--dsh-content-font-size,14px) - 14px));color:var(--dsw-alias-label-primary)}
.作曲席{flex:none;width:100%;display:flex;justify-content:center;box-sizing:border-box;padding:0 var(--dsh-composer-side-clearance) 4px;background:linear-gradient(180deg,transparent 0px,var(--dsw-alias-bg-base) 36px)}
.对话英雄 .作曲席,.对话英雄 .英雄,.对话英雄 .工作区行{width:100%;max-width:var(--dsh-composer-card-max-width)}
.对话英雄 .作曲席{padding:0 var(--dsh-composer-side-clearance);background:none;gap:12px;align-items:stretch}
.输入卡{position:relative;width:100%;max-width:var(--dsh-composer-card-max-width);margin-left:auto;margin-right:auto;display:flex;flex-direction:column;gap:12px;padding-top:8px;border-radius:var(--dsw-radius-panel);background:var(--dsw-specific-input-major);box-shadow:var(--dsw-elevation-soft);--dsw-elevation-stroke-color:var(--dsw-alias-border-l2);font-size:var(--dsh-content-font-size,14px);line-height:calc(24px + (var(--dsh-content-font-size,14px) - 14px))}
.指令菜单{position:absolute;left:0;right:0;bottom:calc(100% + 4px);z-index:20;max-height:400px;overflow:auto;padding:4px;gap:0;border-radius:var(--dsw-radius-lg);background:var(--dsw-specific-menu);box-shadow:var(--dsw-elevation-panel)}
.指令节{padding:5px 8px 2px;color:var(--dsw-alias-label-tertiary);font-size:11px;font-weight:500;line-height:16px}
button.q-btn.指令项{width:100%;min-height:34px;padding:6px 8px;border-radius:var(--dsw-radius-md);background:transparent !important;color:var(--dsw-alias-label-primary) !important}
button.q-btn.指令项 .q-btn__content{width:100%;justify-content:space-between;flex-wrap:nowrap;gap:8px}
button.q-btn.指令项:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.指令名{font-size:13px;line-height:20px;color:var(--dsw-alias-label-primary)}
.指令述{color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;text-align:right}
.路径卡{min-width:360px;padding:16px;gap:12px;background:var(--dsw-alias-bg-layer-1);color:var(--dsw-alias-label-primary)}
.路径题{font-size:14px;font-weight:500}
.路径框{width:100%}
.路径框 .q-field__control{height:36px;border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-0);color:var(--dsw-alias-label-primary)}
.工具行{display:flex;width:100%;align-items:center;justify-content:flex-end;flex-wrap:nowrap;gap:12px;padding:2px 8px 6px;box-sizing:border-box}
.尾组{display:flex;width:auto;margin-left:auto;align-items:center;flex-wrap:nowrap;justify-content:flex-end}
button.q-btn.添加钮{width:28px;height:28px;min-width:28px;min-height:28px;padding:0;border-radius:999px;background:var(--dsw-specific-selector) !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important}
button.q-btn.添加钮:hover{background:var(--dsw-alias-interactive-bg-hover-solid) !important}
.输入卡 .q-field,.输入卡 .草稿{width:100%}
.输入卡 .q-field__control,.输入卡 .q-field__control:before,.输入卡 .q-field__control:after,.输入卡 .q-field__native{border:none !important;background:transparent !important;box-shadow:none !important}
.输入卡 .q-field__control::before,.输入卡 .q-field__control::after{display:none !important}
.输入卡 textarea{min-height:52px;max-height:var(--dsh-composer-text-max-height);padding:4px 8px 0 14px;font-family:var(--dsw-font-family);font-size:inherit;line-height:inherit;color:var(--dsw-alias-label-primary)}
.对话活动 .输入卡 textarea{min-height:36px}
.输入卡 textarea::placeholder{color:var(--dsw-alias-label-caption)}
button.q-btn.发送钮{width:34px;height:34px;min-height:34px;min-width:34px;margin:0;padding:0;border-radius:999px;background:var(--dsw-alias-button-info-fill) !important;color:#fff !important;box-shadow:none !important;transform:translateY(-2px)}
button.q-btn.发送钮:hover{background:var(--dsw-alias-button-info-hover) !important}
button.q-btn.发送钮.发送空{opacity:0.4}
.右栏轨{min-width:0;height:100%;overflow:visible}
.页面>.右栏{position:absolute;top:0;right:0;bottom:0;z-index:10;width:var(--dsh-rightbar-width,0px);display:flex;flex-direction:column;box-sizing:border-box;padding:0;border-left:0.5px solid var(--dsw-alias-border-l3);background:var(--dsw-alias-bg-base);color:var(--dsw-alias-label-primary);transform:translateX(100%);visibility:hidden;transition:transform var(--ds-transition-duration-slow) var(--ds-ease-in-out),visibility 0s linear var(--ds-transition-duration-slow)}
.页面>.右栏:not(.右栏收起){transform:none;visibility:visible;transition:transform var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.页面>.右栏.右栏全屏{left:0;width:auto;z-index:40;transform:none;visibility:visible;border:none}
.页面[data-dragging]>.右栏,.页面[data-rightbar-instant]>.右栏,.页面[data-rightbar-fullscreen]>.右栏{transition:none}
@media (prefers-reduced-motion:reduce){.页面>.右栏{transition:none}}
.页签条{flex:none;width:100%;height:38px;align-items:center;flex-wrap:nowrap;gap:4px;padding:10px 6px 0 10px;box-sizing:border-box}
.页签芯片{flex:0 1 auto;min-width:0;max-width:170px;height:28px;align-items:center;gap:5px;padding:0 10px;color:var(--dsw-alias-label-primary);font-size:13px;line-height:1.4;white-space:nowrap}
.页签尾{margin-left:auto;align-items:center;flex-wrap:nowrap;gap:4px}
.右栏正文{flex:1 1 auto;width:100%;min-height:0;overflow:auto}
.向导{width:100%;min-height:100%;align-items:center;justify-content:center;gap:14px;padding:0 24px;box-sizing:border-box}
.向导::after{content:'';flex:0 1 10%}
.罗盘{margin-bottom:16px;color:var(--dsw-static-neutral-200)}
body[data-ds-dark-theme] .罗盘{color:var(--dsw-static-neutral-700)}
button.q-btn.入口胶囊{width:380px;max-width:100%;min-height:56px;padding:14px 20px;justify-content:flex-start;border:0.5px solid var(--dsw-alias-border-l3) !important;border-radius:var(--dsw-radius-xl);background:var(--dsw-alias-bg-layer-1) !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important}
button.q-btn.入口胶囊:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.入口胶囊 .q-btn__content{gap:14px;justify-content:flex-start;flex-wrap:nowrap;width:100%}
.入口文{align-items:flex-start;min-width:0;gap:3px}
button.q-btn.入口胶囊 svg{flex:none;width:26px;height:26px;color:var(--dsw-alias-label-secondary)}
.入口题{overflow:hidden;font-size:14px;line-height:1.4;font-weight:400;white-space:nowrap;text-overflow:ellipsis;color:var(--dsw-alias-label-primary)}
.入口述{overflow:hidden;font-size:11px;line-height:1.4;white-space:nowrap;text-overflow:ellipsis;color:var(--dsw-alias-label-tertiary)}
.右栏状态{margin:0;padding:12px 10px;color:var(--dsw-alias-label-secondary);font-size:var(--dsh-content-font-size-secondary,13px);line-height:1.6}
.文件树{display:flex;flex:1 1 auto;flex-direction:column;width:100%;height:100%;min-height:0;padding:0;gap:0;color:var(--dsw-alias-label-primary);font-size:var(--dsh-content-font-size-secondary,13px);line-height:1.5}
.文件头{flex:0 0 auto;width:100%;height:38px;align-items:center;flex-wrap:nowrap;padding:0 6px 0 16px;box-sizing:border-box;border-bottom:0.5px solid var(--dsw-alias-border-l3)}
.文件根名{margin:0;padding:0;font-size:inherit;font-weight:400;line-height:1.5;color:inherit}
.文件体{flex:1 1 auto;width:100%;min-height:0;margin-right:2px;padding:8px 0 8px 8px;overflow:auto;scrollbar-gutter:stable;gap:0}
button.q-btn.文件行{width:100%;height:auto;min-height:0;justify-content:flex-start;padding:5px 10px;border-radius:var(--dsw-radius-md);background:transparent !important;box-shadow:none !important;color:inherit !important;font-size:inherit;line-height:1.5;font-weight:400}
button.q-btn.文件行 .q-btn__content{justify-content:flex-start;flex-wrap:nowrap;min-width:0;overflow:hidden;text-overflow:ellipsis}
button.q-btn.文件行:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.文件名{display:flex;align-items:center;width:100%;min-width:0;min-height:0;padding:5px 10px;box-sizing:border-box;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;color:inherit;font-size:inherit;line-height:1.5}
.终端栏{display:flex;flex:1 1 auto;flex-direction:column;width:100%;height:100%;min-height:0;padding:8px 8px 0;box-sizing:border-box;gap:0;background:var(--dsw-alias-bg-base);color:var(--dsw-alias-label-primary);font-size:13px}
.终端出列{flex:1 1 auto;width:100%;min-height:0;overflow:auto;padding:8px;gap:0;background:var(--dsw-alias-bg-base)}
.终端出{white-space:pre-wrap;font-family:var(--ds-font-family-code);font-size:13px;line-height:18px;color:var(--dsw-alias-label-primary)}
.终端入{width:100%;background:var(--dsw-alias-bg-l2)}
.终端入 .q-field__control{height:32px;padding:0 12px;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-bg-l2)}
.q-card.设置卡{width:min(800px,calc(100vw - 48px)) !important;max-width:none !important;height:min(800px,calc(100vh - 48px));background:var(--dsw-alias-bg-layer-2);color:var(--dsw-alias-label-primary);border-radius:var(--dsw-radius-panel);box-shadow:var(--dsw-elevation-prominent);overflow:hidden}
.设置头{width:100%;height:54px;align-items:flex-start;justify-content:flex-end;flex-wrap:nowrap;gap:8px;padding:20px 14px 8px 10px;box-sizing:border-box}
.设置标题{padding:0 12px;font-size:16px;line-height:24px;font-weight:500;color:var(--dsw-alias-label-primary)}
.设置身{width:100%;flex:1;min-height:0;align-items:stretch;flex-wrap:nowrap}
.设置右{flex:1 1 auto;min-width:0;min-height:0;height:100%}
.设置导航{flex:0 0 188px;width:188px;height:100%;padding:22px 12px 0;box-sizing:border-box;gap:18px}
.设置导航列{width:100%;min-height:0;gap:4px;overflow:auto}
.设置内容{flex:1 1 auto;width:100%;min-width:0;min-height:0;overflow:auto;align-items:stretch;padding:0 24px 24px;box-sizing:border-box}
.设置内容>.nicegui-column,.设置内容>.column{width:100%;align-items:stretch}
button.q-btn.设置项{width:100%;height:40px;min-height:40px;padding:9px 16px 9px 12px;justify-content:flex-start;border-radius:var(--dsw-radius-md);background:transparent !important;box-shadow:none !important;font-weight:400;font-size:14px;line-height:22px}
button.q-btn.设置项 .q-btn__content{gap:8px;justify-content:flex-start;flex-wrap:nowrap}
button.q-btn.设置项 svg{flex:none;color:var(--dsw-alias-label-primary)}
.设置项文{flex:1;min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
button.q-btn.设置项:hover{background:var(--dsw-specific-sidebar-nav-item-hover) !important}
button.q-btn.设置项.设置当前{background:var(--dsw-specific-sidebar-nav-item-active) !important}
button.q-btn.关闭钮{width:28px;height:28px;min-width:28px;min-height:28px;padding:0;border-radius:var(--dsw-radius-sm);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important}
button.q-btn.关闭钮:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.设置行{width:100%;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:24px;padding:16px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2);box-sizing:border-box}
.设置行文{flex:1;min-width:0;gap:4px}
.设置行题{font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary)}
.设置行述{font-size:12px;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.回车行{position:relative}
.回车钮{position:relative}
button.q-btn.回车钮{height:36px;min-height:36px;padding:0 14px;border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-module-platform) !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important}
button.q-btn.回车钮 .q-btn__content{gap:12px;flex-wrap:nowrap}
.回车菜单{position:absolute;right:0;top:40px;z-index:5;min-width:140px;padding:4px;border-radius:var(--dsw-radius-lg);background:var(--dsw-specific-menu);box-shadow:var(--dsw-elevation-panel)}
.根帧{position:relative;display:grid;grid-template-columns:280px minmax(0,1fr) minmax(0,0px);grid-template-rows:minmax(0,1fr) auto;width:100%;height:100vh;overflow:hidden;background:var(--dsw-alias-bg-base,#f9fafb)}
.根帧[data-animating]{transition:grid-template-columns var(--ds-transition-duration-slow,240ms) ease}
.根帧[data-dragging],.根帧[data-rightbar-fullscreen],.根帧[data-rightbar-instant]{transition:none}
.根帧 .拖柄{position:absolute;grid-area:1 / 1 / 2 / -1;top:0;bottom:0;width:8px;margin-left:-4px;cursor:col-resize;z-index:11;touch-action:none}
.根帧列{min-width:0;min-height:0;height:100%;overflow:hidden;display:flex;flex-direction:column}
.主栏{display:flex;flex-direction:column;height:100%;min-height:0;width:100%;background:var(--dsw-alias-bg-base,#fff)}
.主栏>.聊天视图{flex:1 1 auto;min-height:0;overflow:auto}
.主栏>.输入栏{flex:none;width:100%;box-sizing:border-box;padding:8px 16px 16px}
.输入栏{width:100%}
.输入栏 .草稿,.输入栏 .q-textarea{width:100%}
.根帧底{grid-column:1 / -1}
.根帧罩{position:absolute;inset:0;pointer-events:none;z-index:20}
.根帧罩>*{pointer-events:auto}
.会话失败{display:block;box-sizing:border-box;margin:24px;max-width:36rem;padding:12px 14px;border:1px solid #b42318;border-radius:8px;background:#fff4f2;color:#7a271a;font-size:14px;line-height:22px;white-space:pre-wrap}
'''
