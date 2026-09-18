/* CommonJS entry - loads ASCENT browser codecs for Node. */
"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var dir = __dirname;
var ctx = {
  console: console,
  Uint8Array: Uint8Array,
  Int16Array: Int16Array,
  Array: Array,
  Error: Error,
  Math: Math,
  JSON: JSON,
  parseInt: parseInt,
  TextEncoder: typeof TextEncoder !== "undefined" ? TextEncoder : undefined,
  TextDecoder: typeof TextDecoder !== "undefined" ? TextDecoder : undefined,
};
ctx.global = ctx;
ctx.window = ctx;
ctx.globalThis = ctx;
vm.createContext(ctx);

["ascent_codec.js", "ascent_rs.js", "ascent_d_lab.js"].forEach(function (f) {
  var code = fs.readFileSync(path.join(dir, f), "utf8");
  vm.runInContext(code, ctx, { filename: f });
});

module.exports = {
  AscentCodec: ctx.AscentCodec,
  AscentRS: ctx.AscentRS,
  AscentDLab: ctx.AscentDLab,
  version: "2.1.0",
};
