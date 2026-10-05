// Runs the simulator in the browser: Pyodide (Python on WebAssembly) plus the
// svsim package, both published next to the page. Python sources arrive as
// JSON text (hosts like claude.ai serve no archives): the standard library is
// packed here into the uncompressed zip Pyodide mounts, and svsim is written
// into Pyodide's file system. The page sends {id, method, args}; the worker
// calls Session.<method>(*args) and answers {id, result} as JSON text.
"use strict";
let call = null;

const CRC = new Uint32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(bytes) {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = CRC[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

// An uncompressed ("stored") zip of {path: text}.
function storedZip(files) {
  const enc = new TextEncoder(), parts = [], central = [];
  let offset = 0;
  for (const [path, text] of Object.entries(files)) {
    const name = enc.encode(path), data = enc.encode(text), crc = crc32(data);
    const local = new DataView(new ArrayBuffer(30));
    local.setUint32(0, 0x04034b50, true); local.setUint16(4, 20, true); local.setUint16(6, 0x0800, true);
    local.setUint32(14, crc, true); local.setUint32(18, data.length, true); local.setUint32(22, data.length, true);
    local.setUint16(26, name.length, true);
    parts.push(new Uint8Array(local.buffer), name, data);
    const entry = new DataView(new ArrayBuffer(46));
    entry.setUint32(0, 0x02014b50, true); entry.setUint16(4, 20, true); entry.setUint16(6, 20, true);
    entry.setUint16(8, 0x0800, true); entry.setUint32(16, crc, true); entry.setUint32(20, data.length, true);
    entry.setUint32(24, data.length, true); entry.setUint16(28, name.length, true); entry.setUint32(42, offset, true);
    central.push(new Uint8Array(entry.buffer), name);
    offset += 30 + name.length + data.length;
  }
  const size = central.reduce((n, p) => n + p.length, 0), count = Object.keys(files).length;
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, count, true); end.setUint16(10, count, true);
  end.setUint32(12, size, true); end.setUint32(16, offset, true);
  return new Blob([...parts, ...central, new Uint8Array(end.buffer)], {type: "application/zip"});
}

async function json(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

async function boot() {
  postMessage({type: "progress", text: "正在加载 Python 运行时（第一次约 20 MB，之后会快很多）……"});
  importScripts("pyodide/pyodide.js");
  const stdlib = await json("pyodide/python_stdlib.json");
  const stdLibURL = URL.createObjectURL(storedZip(stdlib));
  const py = await loadPyodide({indexURL: new URL("pyodide/", self.location).href, stdLibURL});
  postMessage({type: "progress", text: "正在加载模拟器和卡池……"});
  const files = await json("svsim.json");
  for (const [path, text] of Object.entries(files)) {
    const full = "/home/pyodide/app/" + path;
    py.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
    py.FS.writeFile(full, text);
  }
  py.runPython(`
import sys, json
sys.path.insert(0, "/home/pyodide/app")
from svsim.ui.session import Session
session = Session()
def call(method, args_json):
    return json.dumps(getattr(session, method)(*json.loads(args_json)), ensure_ascii=False)
`);
  call = py.globals.get("call");
  postMessage({type: "ready"});
}

const ready = boot().catch((e) => postMessage({type: "fatal", text: String(e && e.message || e)}));

onmessage = async (ev) => {
  const {id, method, args} = ev.data;
  await ready;
  if (!call) { postMessage({id, error: "模拟器没有加载成功"}); return; }
  try {
    postMessage({id, result: call(method, JSON.stringify(args || []))});
  } catch (e) {
    postMessage({id, error: String(e && e.message || e).split("\n").slice(-3).join(" ")});
  }
};
