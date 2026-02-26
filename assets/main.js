'use strict';
function getPatchPath() {
    var writablePath = jsb.fileUtils.getWritablePath();
    var patchPath;

    // check last char
    var lastChar = writablePath.substr(writablePath.length - 1, 1);
    if (lastChar == "/" || lastChar == "\\") {
        patchPath = writablePath + "patch/";
    } else {
        patchPath = writablePath + "/patch/";
    }
    return patchPath;
}


// 注入searchPath，优先读取补丁库中的文件
function injectSearchPath() {
    if (!jsb) return;
    console.log("main.js injectSearchPath");

    var fileUtilsSearchPaths = jsb.fileUtils.getSearchPaths();
    var searchPath = getPatchPath();

    // delete repeat searchPath
    for (var j = fileUtilsSearchPaths.length - 1; j >= 0; j--) {
        if (fileUtilsSearchPaths[j] == searchPath) {
            fileUtilsSearchPaths.splice(j, 1);
        }
    }

    // insert to top
    fileUtilsSearchPaths.unshift(searchPath)

    jsb.fileUtils.setSearchPaths(fileUtilsSearchPaths);

    var searchPaths = jsb.fileUtils.getSearchPaths();
    console.log("jsb.fileUtils.getSearchPaths()", searchPaths);
    for (var i = 0; i < searchPaths.length; i++) {
        console.log(i, searchPaths[i]);
    }
}

// 准备补丁目录
// 如果需要重置补丁库，在main.js中提前删除，避免老代码干扰新代码
// bug描述：
// 此前creator项目中，resetPatch逻辑不完整，没有调用restart，导致覆盖无补丁的新包后，会直接使用patchPath中的老代码进入游戏，导致各种异常bug
// 为了规避这种问题，在main.js中提前检查补丁库版本号，提前删除补丁库
function preparePatchPath() {
    if (!jsb) return;

    console.log("main.js preparePatchPath")

    // 1. 读取包体中的patch_info.json
    // 由于patch_info只会存在于包体中，项目中没有这个问题，这个文件不会受到searchPath影响
    var jsonText = jsb.fileUtils.getStringFromFile("src/patch_info.json");
    var patchInfo;
    if (jsonText) {
        patchInfo = JSON.parse(jsonText);
    }

    if (!patchInfo) {
        console.log("[warn] patch_info.json load fail, pass.");
        return;
    }

    // 2. 检测包版本和存档版本，判断是否需要重置补丁

    /** 安装包的bid */
    var packageBid = patchInfo.B_ID;
    /** 安装包的pid */
    var packagePid = patchInfo.P_ID;
    /** 安装包的cfg */
    var packageChannel = patchInfo.CHANNEL;
    /** 安装包的version */
    var packageVersion = patchInfo.VERSION;

    console.log("packageBid", packageBid)
    console.log("packagePid", packagePid)
    console.log("packageChannel", packageChannel)
    console.log("packageVersion", packageVersion)

    // 检查本地存档的版本
    var recordBid = parseInt(localStorage.getItem("PATCH_BID"));
    var recordPid = parseInt(localStorage.getItem("PATCH_PID"));
    var recordPackagePid = parseInt(localStorage.getItem("PATCH_PACKAGE_PID"));
    var recordChannel = localStorage.getItem("PATCH_CHANNEL");

    console.log("recordBid", recordBid)
    console.log("recordPid", recordPid)
    console.log("recordPackagePid", recordPackagePid)
    console.log("recordChannel", recordChannel)

    // 如果bid和channel不匹配，则重置补丁
    // 如果package中的pid比存档的pid高，则重置补丁
    var bNeedRemove = false;

    if (packageBid != recordBid) {
        console.log("[warn] bid not match! package, record: = ", packageBid, recordBid);
        bNeedRemove = true;

    } else if (packageChannel != recordChannel) {
        console.log("[warn] channel not match! package, record: = ", packageChannel, recordChannel);
        bNeedRemove = true;

    } else if (packagePid != recordPackagePid) {
        console.log("[warn] package pid not match! package, record: = ", packagePid, recordPackagePid);
        bNeedRemove = true;

    } else if (packagePid > (isNaN(recordPid) ? 0 : recordPid)) {
        console.log("[warn] package pid is higher! package, record: = ", packagePid, recordPid);
        bNeedRemove = true;
    }

    // 3. 删除补丁库
    if (bNeedRemove) {
        removePatchPath(packageBid, packagePid, packageChannel, packageVersion);
    }
}

// 删除补丁库（如果存在）
function removePatchPath(bid, pid, channel, version) {
    console.log("main.js removePatchPath");

    // 1. 清理补丁目录
    var patchPath = getPatchPath();
    console.log("patchPath", patchPath);
    console.log("jsb.fileUtils.isDirectoryExist(patchPath)", jsb.fileUtils.isDirectoryExist(patchPath));
    if (jsb.fileUtils.isDirectoryExist(patchPath)) {
        jsb.fileUtils.removeDirectory(patchPath);
    }

    // 2. 清理存档中的补丁信息
    localStorage.setItem("PATCH_BID", bid.toString());
    localStorage.setItem("PATCH_PID", pid.toString());
    localStorage.setItem("PATCH_PACKAGE_PID", pid.toString());
    localStorage.setItem("PATCH_CHANNEL", channel);
    localStorage.setItem("GAME_VERSION", version);

    console.log("after setItem")

    console.log("PATCH_BID", localStorage.getItem("PATCH_BID"));
    console.log("PATCH_PID", localStorage.getItem("PATCH_PID"));
    console.log("PATCH_PACKAGE_PID", localStorage.getItem("PATCH_PACKAGE_PID"));
    console.log("PATCH_CHANNEL", localStorage.getItem("PATCH_CHANNEL"));
    console.log("GAME_VERSION", localStorage.getItem("GAME_VERSION"));
}

if (jsb && jsb.fileUtils) {
    // 注入补丁库的searchPath
    injectSearchPath();

    try {
        // 检查补丁库版本号
        preparePatchPath()
    } catch (e) {
        console.log("preparePatchPath exception:", e.message);
        console.log(e.stack)
    }
}

require("main_origin.js");