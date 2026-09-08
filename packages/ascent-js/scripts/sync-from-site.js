#!/usr/bin/env node
"use strict";
var fs = require("fs");
var path = require("path");
var root = path.resolve(__dirname, "../../..");
var pub = path.join(root, "site", "public");
var dest = path.resolve(__dirname, "..");
["ascent_codec.js", "ascent_rs.js", "ascent_d_lab.js"].forEach(function (f) {
  fs.copyFileSync(path.join(pub, f), path.join(dest, f));
  console.log("synced", f);
});
