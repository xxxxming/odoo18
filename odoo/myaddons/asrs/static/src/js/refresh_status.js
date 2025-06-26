/** @odoo-module **/

import { jsonRpc } from "@web/core/network/rpc";

console.log("✅ 模块加载成功");

function getRecordIdFromURL() {
    const match = window.location.pathname.match(/\/(\d+)$/);
    return match ? parseInt(match[1]) : null;
}

function refreshPackNumber() {
    const recordId = getRecordIdFromURL();
    if (!recordId) {
        console.warn("❌ 未找到记录 ID");
        return;
    }

    jsonRpc("/asrs/pack_number", { record_id: recordId }).then(result => {
        console.log("✅ 包装数：", result.pack_number);
        const el = document.getElementById("pack_number_field");
        if (el) {
            el.innerText = result.pack_number || "0";
        } else {
            console.warn("❌ 未找到字段元素");
        }
    }).catch(err => {
        console.error("❌ RPC 错误：", err);
    });
}

setInterval(refreshPackNumber, 5000);
