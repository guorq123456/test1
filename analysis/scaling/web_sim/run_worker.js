// Runs web/worker.js (as built) in Node against a local host, the way a browser worker would: the page's
// messages are sent to onmessage and the answers printed with their timings.
const path = require("path"), fs = require("fs"), vm = require("vm");
const [dist, port, ...calls] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}/`;
globalThis.self = globalThis;
self.location = new URL("worker.js", base);
globalThis.importScripts = (p) => {            // Pyodide in Node loads itself from a local folder
  const real = require(path.join(dist, p)).loadPyodide;
  globalThis.loadPyodide = (opts) => real({...opts, indexURL: path.join(dist, "pyodide") + "/"});
};
const pending = new Map();
let readyResolve; const ready = new Promise((r) => (readyResolve = r));
globalThis.postMessage = (msg) => {
  if (msg.type === "progress") console.log("progress:", msg.text);
  else if (msg.type === "ready") { console.log("ready"); readyResolve(); }
  else if (msg.type === "fatal") { console.log("FATAL", msg.text); process.exit(2); }
  else if (pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
};
const nodeFetch = globalThis.fetch;       // a worker resolves relative URLs against its own location
globalThis.fetch = (input, init) => nodeFetch(typeof input === "string" && !/^[a-z]+:/.test(input) ? new URL(input, base).href : input, init);
globalThis.onmessage = null;           // a worker global the script assigns
vm.runInThisContext(fs.readFileSync(path.join(dist, "worker.js"), "utf8"));
let next = 1;
function call(method, args) {
  return new Promise((resolve) => { const id = next++; pending.set(id, resolve); onmessage({data: {id, method, args}}); });
}
(async () => {
  const t0 = Date.now(); await ready; console.log("boot_s", (Date.now() - t0) / 1000);
  // scenario: [{deck, spec, seed, ai_steps}] -- "you" picks a legal action by a fixed generator, the AI decides
  const scenario = JSON.parse(calls[0]);
  for (const sc of scenario) {
    let x = sc.seed >>> 0;
    const rand = (n) => { x = (Math.imul(x, 1664525) + 1013904223) >>> 0; return x % n; };
    let v = JSON.parse((await call("start", [sc.deck, sc.deck, sc.spec, sc.seed])).result);
    const times = [];
    while (!v.over && times.length < sc.ai_steps) {
      let r;
      if (v.active === 1) {
        const t = Date.now(); r = await call("ai_step", []); times.push(Date.now() - t);
      } else if (v.phase === "mulligan") r = await call("mulligan", [[]]);
      else r = await call("act", [rand(v.actions.length)]);
      if (r.error) { console.log("ERROR", r.error); process.exit(3); }
      v = JSON.parse(r.result);
    }
    const mean = times.reduce((a, b) => a + b, 0) / times.length;
    console.log(JSON.stringify({name: sc.name, steps: times.length, mean_ms: Math.round(mean * 10) / 10,
                                first_ms: times[0], turn: v.turn, over: v.over}));
  }
  process.exit(0);
})();
