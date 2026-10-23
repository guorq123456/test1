// Pyodide in Node, set up as the page's worker does (numpy unpacked from the build's numpy.json, svsim.json written
// into /home/pyodide/app), then a Python script run there with extra files copied in.
const path = require("path"), fs = require("fs");
const [dist, script, ...extra] = process.argv.slice(2);
(async () => {
  const py = await require(path.join(dist, "pyodide/pyodide.js")).loadPyodide({indexURL: path.join(dist, "pyodide") + "/"});
  const {base64} = JSON.parse(fs.readFileSync(path.join(dist, "pyodide/numpy.json"), "utf8"));
  py.unpackArchive(new Uint8Array(Buffer.from(base64, "base64")), "wheel");
  const files = JSON.parse(fs.readFileSync(path.join(dist, "svsim.json"), "utf8"));
  for (const name of files._more || []) Object.assign(files, JSON.parse(fs.readFileSync(path.join(dist, name), "utf8")));
  delete files._more;
  for (const [p, text] of Object.entries(files)) {
    const full = "/home/pyodide/app/" + p;
    py.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
    py.FS.writeFile(full, text);
  }
  for (const pair of extra) {                     // local=inside
    const [local, inside] = pair.split("=");
    py.FS.mkdirTree(inside.slice(0, inside.lastIndexOf("/")));
    py.FS.writeFile(inside, new Uint8Array(fs.readFileSync(local)));
  }
  py.FS.mkdirTree("/out");
  try { py.runPython(`import sys; sys.path.insert(0, "/home/pyodide/app")\n` + fs.readFileSync(script, "utf8")); } catch (e) { console.log("PYERR", String(e.message).slice(-2500)); process.exit(4); }
  console.log(py.FS.readFile("/out/result.json", {encoding: "utf8"}));
})();
