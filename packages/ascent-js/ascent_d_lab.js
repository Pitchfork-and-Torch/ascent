/* ASCENT-D P9 outer frame (browser) - structure + RS(255,223) via AscentRS.
   Matches ref/ascent_d.py layout: SYNC D5E5C0DE + profile + ecc + len + unit + codewords.
   CRC: zlib/ISO-HDLC CRC-32 (lab fallback when crc32c unavailable on host).
   Requires ascent_rs.js (AscentRS). ASCII hyphens only. */

(function (global) {
  "use strict";

  var RS = global.AscentRS;
  var SYNC = [0xd5, 0xe5, 0xc0, 0xde];
  var PROFILE_D = 0x44;
  var PROFILE_E = 0x45;
  var PROFILE_A = 0x41;
  var PROFILE_7 = 0x37;
  var FAMILY_RS = 0x01;
  var FAMILY_NONE = 0x00;
  var RS_N = 255;
  var RS_K = 223;
  var RS_PARITY = 32;
  var MAX_UNIT = 8192;

  function AscentDError(message) {
    this.name = "AscentDError";
    this.message = message || "ASCENT-D lab error";
  }
  AscentDError.prototype = Object.create(Error.prototype);

  var CRC_TABLE = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) {
      var c = n;
      for (var k = 0; k < 8; k++) {
        c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      }
      t[n] = c >>> 0;
    }
    return t;
  })();

  function crc32(data) {
    var c = 0xffffffff;
    for (var i = 0; i < data.length; i++) {
      c = CRC_TABLE[(c ^ data[i]) & 0xff] ^ (c >>> 8);
    }
    return (c ^ 0xffffffff) >>> 0;
  }

  function pushU32(out, n) {
    out.push((n >>> 24) & 0xff, (n >>> 16) & 0xff, (n >>> 8) & 0xff, n & 0xff);
  }

  function readU32(u8, i) {
    return (
      ((u8[i] << 24) | (u8[i + 1] << 16) | (u8[i + 2] << 8) | u8[i + 3]) >>> 0
    );
  }

  function eccHdr(family, interleave, crcPre) {
    return [
      family & 0xff,
      RS_N & 0xff,
      RS_K & 0xff,
      (interleave != null ? interleave : 1) & 0xff,
      (crcPre != null ? crcPre : 1) & 0xff,
    ];
  }

  function protectedBlob(profile, ecc, lengthBe, unit) {
    var pre = [profile].concat(ecc).concat(lengthBe);
    for (var i = 0; i < unit.length; i++) pre.push(unit[i]);
    var c = crc32(pre);
    var out = [];
    pushU32(out, c);
    for (var j = 0; j < unit.length; j++) out.push(unit[j]);
    return out;
  }

  function requireRS() {
    if (!RS || typeof RS.rsEncode !== "function") {
      throw new AscentDError("AscentRS missing - load ascent_rs.js before ascent_d_lab.js");
    }
  }

  function rsEncodeBlocks(protArr) {
    requireRS();
    var pad = (RS_K - (protArr.length % RS_K)) % RS_K;
    var padded = protArr.slice();
    for (var p = 0; p < pad; p++) padded.push(0);
    var out = [];
    for (var i = 0; i < padded.length; i += RS_K) {
      var block = new Uint8Array(padded.slice(i, i + RS_K));
      var cw = RS.rsEncode(block, RS_PARITY);
      for (var j = 0; j < cw.length; j++) out.push(cw[j]);
    }
    return out;
  }

  function rsDecodeBlocks(codewordBlob, expectedProtectedLen) {
    requireRS();
    var nBlocks = Math.ceil(expectedProtectedLen / RS_K) || 1;
    var need = nBlocks * RS_N;
    if (codewordBlob.length < need) return null;
    var prot = [];
    for (var bi = 0; bi < nBlocks; bi++) {
      var off = bi * RS_N;
      var word = codewordBlob.slice
        ? codewordBlob.slice(off, off + RS_N)
        : Array.prototype.slice.call(codewordBlob, off, off + RS_N);
      var u8 = word instanceof Uint8Array ? word : new Uint8Array(word);
      var dec = RS.rsDecode(u8, RS_PARITY);
      if (!dec) return null;
      for (var k = 0; k < RS_K; k++) prot.push(dec[k]);
    }
    return prot.slice(0, expectedProtectedLen);
  }

  function encodeP9(unit, opts) {
    var o = opts || {};
    var u =
      unit instanceof Uint8Array ? Array.from(unit) : Array.from(unit || []);
    if (u.length > MAX_UNIT) {
      throw new AscentDError(
        "unit length " + u.length + " > MAX_UNIT " + MAX_UNIT
      );
    }
    var profile = o.profile != null ? o.profile : PROFILE_D;
    var family = o.family != null ? o.family : FAMILY_RS;
    var interleave = o.interleave != null ? o.interleave : 1;
    if (profile === PROFILE_D && family === FAMILY_NONE) {
      throw new AscentDError("family NONE illegal on ASCENT-D");
    }
    var ecc = eccHdr(family, interleave, 1);
    var lengthBe = [];
    pushU32(lengthBe, u.length);
    var prot = protectedBlob(profile, ecc, lengthBe, u);
    var codewords = rsEncodeBlocks(prot);
    var out = SYNC.concat([profile], ecc, lengthBe, u, codewords);
    return new Uint8Array(out);
  }

  function findSync(stream, start) {
    start = start || 0;
    for (var i = start; i + 3 < stream.length; i++) {
      if (
        stream[i] === 0xd5 &&
        stream[i + 1] === 0xe5 &&
        stream[i + 2] === 0xc0 &&
        stream[i + 3] === 0xde
      ) {
        return i;
      }
    }
    return -1;
  }

  function decodeP9(stream, start) {
    start = start || 0;
    var i = findSync(stream, start);
    if (i < 0) return { frame: null, next: start, status: "no_sync" };
    var j = i + 4;
    if (j + 1 + 5 + 4 > stream.length) {
      return { frame: null, next: i + 1, status: "truncated" };
    }
    var profile = stream[j++];
    var ecc = [
      stream[j],
      stream[j + 1],
      stream[j + 2],
      stream[j + 3],
      stream[j + 4],
    ];
    j += 5;
    var family = ecc[0];
    var n = ecc[1];
    var k = ecc[2];
    var interleave = ecc[3];
    var crcPre = ecc[4];
    var length = readU32(stream, j);
    j += 4;
    if (length > MAX_UNIT) return { frame: null, next: i + 4, status: "erased" };
    if (j + length > stream.length) {
      return { frame: null, next: i + 1, status: "truncated" };
    }
    var clearUnit = stream.slice
      ? stream.slice(j, j + length)
      : new Uint8Array(Array.prototype.slice.call(stream, j, j + length));
    j += length;
    if (profile === PROFILE_D && family === FAMILY_NONE) {
      return { frame: null, next: i + 4, status: "erased" };
    }
    if (family !== FAMILY_RS || n !== RS_N || k !== RS_K) {
      return { frame: null, next: i + 4, status: "erased" };
    }

    var protectedLen = 4 + length;
    var nBlocks = Math.ceil(protectedLen / RS_K) || 1;
    var need = nBlocks * RS_N;
    if (j + need > stream.length) {
      return { frame: null, next: i + 1, status: "truncated" };
    }
    var codewordBlob = stream.slice
      ? stream.slice(j, j + need)
      : new Uint8Array(Array.prototype.slice.call(stream, j, j + need));
    var jEnd = j + need;

    var prot = rsDecodeBlocks(codewordBlob, protectedLen);
    if (!prot || prot.length < 4) {
      return {
        frame: null,
        next: i + 4,
        status: "erased",
        raw: stream.slice ? stream.slice(i, jEnd) : null,
      };
    }
    var gotCrc =
      ((prot[0] << 24) | (prot[1] << 16) | (prot[2] << 8) | prot[3]) >>> 0;
    var body = prot.slice(4);
    if (body.length !== length) {
      return { frame: null, next: i + 4, status: "erased" };
    }
    var lengthBe = [];
    pushU32(lengthBe, length);
    var expectArr = [profile].concat(ecc).concat(lengthBe);
    for (var bi = 0; bi < body.length; bi++) expectArr.push(body[bi]);
    var expect = crc32(expectArr);
    if (crcPre && gotCrc !== expect) {
      return { frame: null, next: i + 4, status: "erased" };
    }

    var recovered = false;
    if (clearUnit.length === body.length) {
      for (var ci = 0; ci < body.length; ci++) {
        if ((clearUnit[ci] & 0xff) !== (body[ci] & 0xff)) {
          recovered = true;
          break;
        }
      }
    }

    return {
      frame: {
        profile: profile,
        family: family,
        n: n,
        k: k,
        interleave: interleave,
        crcPre: crcPre,
        unit: new Uint8Array(body),
        clearUnit: clearUnit instanceof Uint8Array ? clearUnit : new Uint8Array(clearUnit),
        recovered: recovered,
        raw: stream.slice ? stream.slice(i, jEnd) : null,
        syncOffset: i,
        totalLen: jEnd - i,
      },
      next: jEnd,
      status: recovered ? "recovered" : "ok",
    };
  }

  function injectBitErrors(u8, count, opts) {
    var o = opts || {};
    var out = new Uint8Array(u8);
    var n = count | 0;
    if (n <= 0 || out.length === 0) return { bytes: out, flips: [] };
    var minOff = o.minOffset != null ? o.minOffset : 0;
    var maxOff = o.maxOffset != null ? o.maxOffset : out.length - 1;
    if (maxOff < minOff) maxOff = minOff;
    var flips = [];
    var used = {};
    var guard = 0;
    while (flips.length < n && guard < n * 50) {
      guard++;
      var off = minOff + Math.floor(Math.random() * (maxOff - minOff + 1));
      var bit = Math.floor(Math.random() * 8);
      var key = off + ":" + bit;
      if (used[key]) continue;
      used[key] = true;
      out[off] = out[off] ^ (1 << bit);
      flips.push({ offset: off, bit: bit, before: u8[off], after: out[off] });
    }
    return { bytes: out, flips: flips };
  }

  function describeFrame(frame) {
    if (!frame) return null;
    var prof =
      frame.profile === PROFILE_D
        ? "ASCENT-D"
        : frame.profile === PROFILE_E
          ? "ASCENT-E"
          : frame.profile === PROFILE_A
            ? "ASCENT-A"
            : "0x" + frame.profile.toString(16);
    return {
      profile: prof,
      profileByte: frame.profile,
      family: frame.family === FAMILY_RS ? "RS(255,223)" : "other",
      n: frame.n,
      k: frame.k,
      interleave: frame.interleave,
      unitLen: frame.unit.length,
      totalLen: frame.totalLen,
      recovered: !!frame.recovered,
      sync: "D5E5C0DE",
    };
  }

  var AscentDLab = {
    SYNC: SYNC,
    PROFILE_D: PROFILE_D,
    PROFILE_E: PROFILE_E,
    PROFILE_A: PROFILE_A,
    PROFILE_7: PROFILE_7,
    FAMILY_RS: FAMILY_RS,
    FAMILY_NONE: FAMILY_NONE,
    RS_N: RS_N,
    RS_K: RS_K,
    MAX_UNIT: MAX_UNIT,
    crc32: crc32,
    encodeP9: encodeP9,
    decodeP9: decodeP9,
    findSync: findSync,
    injectBitErrors: injectBitErrors,
    describeFrame: describeFrame,
    AscentDError: AscentDError,
    version: "2.0.0-rs",
    note:
      "Browser ASCENT-D uses real RS(255,223) GF(256) (AscentRS, poly 0x11d) + CRC-32 lab binding. Encode matches python reedsolo; 1-byte errors correct; multi-byte may erase (same as parity fail).",
  };

  global.AscentDLab = AscentDLab;
})(typeof window !== "undefined" ? window : globalThis);
