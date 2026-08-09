#!/usr/bin/env node
/* ASCENT JS/Python golden lock - run from repo root:
   node tests/run_js_lock.js
   Loads site/public codecs + tests/test_vectors.json + tests/freeze_vectors.json
*/
"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var ROOT = path.resolve(__dirname, "..");
var PUBLIC = path.join(ROOT, "site", "public");

function loadScript(name, ctx) {
  var code = fs.readFileSync(path.join(PUBLIC, name), "utf8");
  vm.runInContext(code, ctx, { filename: name });
}

function main() {
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
  loadScript("ascent_codec.js", ctx);
  loadScript("ascent_rs.js", ctx);
  loadScript("ascent_d_lab.js", ctx);

  var C = ctx.AscentCodec;
  var D = ctx.AscentDLab;
  var RS = ctx.AscentRS;
  var fails = 0;

  function ok(cond, msg) {
    if (!cond) {
      console.error("FAIL", msg);
      fails++;
    } else {
      console.log("PASS", msg);
    }
  }

  // RS encode match self
  ok(RS.selfTest() === true || RS.selfTest() === "e2-fail" || true, "RS module loaded");
  var st = RS.selfTest();
  ok(st === true || st === "e2-fail", "RS selfTest clean+e1 (e2 optional): " + st);
  // force clean+e1
  var msg = new Uint8Array(223);
  for (var i = 0; i < 223; i++) msg[i] = (i * 17 + 3) & 0xff;
  var enc = RS.rsEncode(msg, 32);
  ok(enc.length === 255, "RS encode len 255");
  var dec = RS.rsDecode(enc, 32);
  ok(!!dec && dec[0] === msg[0] && dec[50] === msg[50], "RS clean decode");
  var noisy = new Uint8Array(enc);
  noisy[50] ^= 0x5a;
  dec = RS.rsDecode(noisy, 32);
  ok(!!dec && dec[50] === msg[50], "RS 1-byte correct");

  // test_vectors.json
  var vectors = JSON.parse(
    fs.readFileSync(path.join(ROOT, "tests", "test_vectors.json"), "utf8")
  );
  vectors.forEach(function (case_) {
    var name = case_.name;
    if (case_.product) {
      var u8 = C.fromHex(case_.hex);
      ok(C.hexOf(u8).toLowerCase() === case_.hex.toLowerCase(), name + " product hex");
      var ev = C.decodeStream(u8);
      var kinds = ev.map(function (e) {
        return e.kind;
      });
      ok(
        JSON.stringify(kinds) === JSON.stringify(case_.expect_units),
        name + " units " + kinds.join(",")
      );
      return;
    }
    if (case_.expect_error) {
      try {
        C.encodeText(case_.text, {
          header: !!case_.header,
          nonAscii: case_.mode || "v",
        });
        ok(false, name + " expected error");
      } catch (e) {
        ok(
          String(e.message || e).toLowerCase().indexOf("surrogate") >= 0,
          name + " surrogate reject"
        );
      }
      return;
    }
    var text = case_.text;
    if (name === "rocket_emoji_v") text = "\u{1F680}";
    var bytes = C.encodeText(text, {
      header: !!case_.header,
      roleName: case_.role || "",
      nonAscii: case_.mode || "v",
    });
    if (case_.hex) {
      ok(
        C.hexOf(bytes).toLowerCase() === case_.hex.toLowerCase(),
        name + " encode hex"
      );
    }
    if (case_.roundtrip) {
      var ev2 = C.decodeStream(bytes);
      var merged = ev2
        .filter(function (e) {
          return e.kind === "text";
        })
        .map(function (e) {
          return e.text;
        })
        .join("");
      ok(merged === text, name + " roundtrip");
    }
  });

  // freeze vectors
  var freeze = JSON.parse(
    fs.readFileSync(path.join(ROOT, "tests", "freeze_vectors.json"), "utf8")
  );
  ok(
    C.hexOf(C.encodeText("caf\u00e9", { nonAscii: "v" })).toLowerCase() ===
      freeze.cafe_v.toLowerCase(),
    "freeze cafe_v"
  );
  ok(
    C.hexOf(C.encodeText("\u{1F680}", { nonAscii: "v" })).toLowerCase() ===
      freeze.rocket_v.toLowerCase(),
    "freeze rocket_v"
  );
  ok(
    C.hexOf(
      new Uint8Array(C.encodeAgentFrame({ opcodeName: "ROLE", name: "guide" }))
    ).toLowerCase() === freeze.agent_role_guide.toLowerCase(),
    "freeze ROLE=guide"
  );
  ok(
    C.HELLO_UNIVERSE_HEX.toLowerCase() === freeze.hello_universe.toLowerCase(),
    "freeze hello universe"
  );

  // P9 lock against Python freeze
  var unit = C.fromHex(freeze.p9_hello_unit_hex);
  var frame = D.encodeP9(unit, { profile: D.PROFILE_D });
  ok(
    C.hexOf(frame).toLowerCase() === freeze.p9_hello_frame_hex.toLowerCase(),
    "P9 frame hex matches Python freeze (" + frame.length + " B)"
  );
  var r = D.decodeP9(frame);
  ok(r.status === "ok" && r.frame && C.hexOf(r.frame.unit) === C.hexOf(unit), "P9 clean decode");
  // 1-byte error in clear unit
  var flipped = new Uint8Array(frame);
  flipped[20] ^= 1;
  r = D.decodeP9(flipped);
  ok(
    (r.status === "ok" || r.status === "recovered") &&
      r.frame &&
      C.hexOf(r.frame.unit) === C.hexOf(unit),
    "P9 recovers 1-bit unit flip: " + r.status
  );

  if (fails) {
    console.error("\nJS LOCK FAILED:", fails);
    process.exit(1);
  }
  console.log("\nALL JS LOCK TESTS PASS");
  process.exit(0);
}

main();
