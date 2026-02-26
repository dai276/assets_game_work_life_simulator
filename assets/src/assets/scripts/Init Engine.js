{
cc.macro.ENABLE_WEBGL_ANTIALIAS = !0;
const s = cc.sys.os === cc.sys.OS_IOS && cc.sys.isBrowser && /(iPhone OS 14)|(Version\/14(\.|[0-9])*)|(iOS 14)/.test(window.navigator.userAgent), t = cc.sys.os === cc.sys.OS_IOS && cc.sys.isBrowser && /(iPhone OS 15)|(Version\/15(\.|[0-9])*)|(iOS 15)/.test(window.navigator.userAgent);
if (s || t) {
cc.MeshBuffer.prototype.checkAndSwitchBuffer = function(s) {
if (this.vertexOffset + s > 65535) {
this.uploadData();
this._batcher._flush();
}
};
cc.MeshBuffer.prototype.forwardIndiceStartToOffset = function() {
this.uploadData();
this.switchBuffer();
};
}
}