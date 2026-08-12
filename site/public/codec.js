/* ASCENT frozen wire codec (browser) - ports ref/ascent_codec.py
   Cont 0xA0-0xBF (5 bits), ASCENT-V short forms + F5 03 u24be long.
   ASCII hyphens only. No network I/O. */

(function (global) {
  "use strict";

  var OPCODE = {
    0x0001: "STOP",
    0x0002: "ROLE",
    0x0003: "TOOL",
    0x0004: "THINK",
    0x0005: "HANDOFF",
    0x0006: "CAP",
    0x0007: "SAFETY",
  };
  var MM_KIND = { 1: "REF", 2: "INLINE", 3: "CHUNK", 4: "END" };
  var HASH_ALG = { 0: "none", 1: "sha-256", 2: "sha-512", 3: "blake3-256" };
  var HASH_LEN = { 0: 0, 1: 32, 2: 64, 3: 32 };

  var HEADER_MAGIC = "ASCENT/1.0\n";
  var PLANE_P3 = 0x03;

  var LEAD_SKYSTATE = 0xc5;
  var PATHHINT_SCHEMA_V1 = 0x01;
  var PATHHINT_BODY_LEN = 26;
  var PATHHINT_BODY_LEN_CRC = 30;
  var PATHHINT_MAX_BODY = 256;
  var P2_SKIP_CAP = 16384;
  var FLAG_CAP_KBPS = 0x01;
  var FLAG_HAS_OBSTRUCTION = 0x02;
  var FLAG_HAS_ELEV = 0x04;
  var FLAG_RELATIVE_FREEZE = 0x08;
  var FLAG_CRC = 0x10;
  var FLAG_RESERVED_MASK = 0xe0;
  var ELEV_ABSENT = 0x7fff;
  var OBSTRUCTION_ABSENT = 0xff;

  // SPEC.md E.2 interop hex
  var HELLO_UNIVERSE_HEX =
    "415343454E542F312E300A48656C6C6F" +
    "2C20556E6976657273652E0A9AC10100" +
    "020000060567756964659B9D4D010005" +
    "0101E491921182DA9CB7B24E4B8A579D" +
    "5E78EDC23E40141D015FAA097C3ECC6D" +
    "65EB000000000000002A6369643A7368" +
    "613235363A6161626263636464656566" +
    "66303031313232333334343535363637" +
    "37383839";

  function AscentError(message) {
    this.name = "AscentError";
    this.message = message || "ASCENT codec error";
    if (typeof Error.captureStackTrace === "function") {
      Error.captureStackTrace(this, AscentError);
    } else {
      this.stack = new Error(this.message).stack;
    }
  }
  AscentError.prototype = Object.create(Error.prototype);
  AscentError.prototype.constructor = AscentError;

  // ---------------------------------------------------------------------------
  // Cont class (FROZEN) - primary continuation 0xA0-0xBF, 5 payload bits
  // ---------------------------------------------------------------------------

  var Cont = {
    MIN: 0xa0,
    MAX: 0xbf,
    MASK: 0x1f,
    contByte: function (n5) {
      return 0xa0 | (n5 & 0x1f);
    },
    contVal: function (b) {
      if (!(b >= 0xa0 && b <= 0xbf)) {
        throw new AscentError("not a Cont byte: 0x" + b.toString(16));
      }
      return b & 0x1f;
    },
    isCont: function (b) {
      return b >= 0xa0 && b <= 0xbf;
    },
  };

  function contByte(n5) {
    return Cont.contByte(n5);
  }
  function contVal(b) {
    return Cont.contVal(b);
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  function hexOf(u8) {
    var out = "";
    for (var i = 0; i < u8.length; i++) {
      out += (u8[i] & 0xff).toString(16).padStart(2, "0");
    }
    return out;
  }

  function fromHex(hex) {
    var clean = String(hex).replace(/\s+/g, "").replace(/^0x/i, "");
    if (clean.length % 2) throw new AscentError("odd hex length");
    if (!/^[0-9a-fA-F]*$/.test(clean)) throw new AscentError("invalid hex");
    var out = new Uint8Array(clean.length / 2);
    for (var i = 0; i < out.length; i++) {
      out[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
    }
    return out;
  }

  function formatHexLines(u8, perLine) {
    var n = perLine || 16;
    var h = hexOf(u8).toUpperCase();
    var lines = [];
    for (var i = 0; i < h.length; i += n * 2) {
      lines.push(h.slice(i, i + n * 2));
    }
    return lines.join("\n");
  }

  function u16be(u8, i) {
    if (i + 2 > u8.length) throw new AscentError("truncated u16");
    return [(u8[i] << 8) | u8[i + 1], i + 2];
  }

  function u32be(u8, i) {
    if (i + 4 > u8.length) throw new AscentError("truncated u32");
    return [
      ((u8[i] << 24) | (u8[i + 1] << 16) | (u8[i + 2] << 8) | u8[i + 3]) >>> 0,
      i + 4,
    ];
  }

  function u64be(u8, i) {
    if (i + 8 > u8.length) throw new AscentError("truncated u64");
    var hi =
      ((u8[i] << 24) | (u8[i + 1] << 16) | (u8[i + 2] << 8) | u8[i + 3]) >>> 0;
    var lo =
      ((u8[i + 4] << 24) |
        (u8[i + 5] << 16) |
        (u8[i + 6] << 8) |
        u8[i + 7]) >>>
      0;
    // Safe for lab sizes (MM body hard cap applied by caller)
    if (hi > 0x1fffff) throw new AscentError("u64 too large for browser codec");
    var val = hi * 0x100000000 + lo;
    return [val, i + 8];
  }

  function pushU16(out, n) {
    out.push((n >> 8) & 0xff, n & 0xff);
  }

  function pushU32(out, n) {
    n = n >>> 0;
    out.push((n >>> 24) & 0xff, (n >>> 16) & 0xff, (n >>> 8) & 0xff, n & 0xff);
  }

  function pushI16(out, n) {
    if (n < 0) n = (0x10000 + n) & 0xffff;
    out.push((n >> 8) & 0xff, n & 0xff);
  }

  function i16be(u8, i) {
    if (i + 2 > u8.length) throw new AscentError("truncated i16");
    var v = (u8[i] << 8) | u8[i + 1];
    if (v & 0x8000) v = v - 0x10000;
    return [v, i + 2];
  }

  var CRC32_TABLE = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) {
      var c = n;
      for (var k = 0; k < 8; k++) {
        c = c & 1 ? (0xedb88320 ^ (c >>> 1)) : c >>> 1;
      }
      t[n] = c >>> 0;
    }
    return t;
  })();

  function crc32Ieee(u8) {
    var c = 0xffffffff;
    for (var i = 0; i < u8.length; i++) {
      c = CRC32_TABLE[(c ^ u8[i]) & 0xff] ^ (c >>> 8);
    }
    return (c ^ 0xffffffff) >>> 0;
  }

  function pushU64(out, n) {
    // big-endian u64; n is Number, lab sizes fit
    var hi = Math.floor(n / 0x100000000);
    var lo = n >>> 0;
    out.push(
      (hi >>> 24) & 0xff,
      (hi >>> 16) & 0xff,
      (hi >>> 8) & 0xff,
      hi & 0xff,
      (lo >>> 24) & 0xff,
      (lo >>> 16) & 0xff,
      (lo >>> 8) & 0xff,
      lo & 0xff
    );
  }

  function utf8Encode(str) {
    if (typeof TextEncoder !== "undefined") {
      return new TextEncoder().encode(str);
    }
    // Minimal fallback for pure BMP+ascii lab cases
    var out = [];
    for (var i = 0; i < str.length; i++) {
      var cp = str.charCodeAt(i);
      if (cp < 0x80) out.push(cp);
      else if (cp < 0x800) {
        out.push(0xc0 | (cp >> 6), 0x80 | (cp & 0x3f));
      } else if (cp >= 0xd800 && cp <= 0xdbff && i + 1 < str.length) {
        var lo = str.charCodeAt(i + 1);
        if (lo >= 0xdc00 && lo <= 0xdfff) {
          var full = 0x10000 + ((cp - 0xd800) << 10) + (lo - 0xdc00);
          out.push(
            0xf0 | (full >> 18),
            0x80 | ((full >> 12) & 0x3f),
            0x80 | ((full >> 6) & 0x3f),
            0x80 | (full & 0x3f)
          );
          i++;
          continue;
        }
        throw new AscentError("lone surrogate in utf8Encode");
      } else {
        out.push(
          0xe0 | (cp >> 12),
          0x80 | ((cp >> 6) & 0x3f),
          0x80 | (cp & 0x3f)
        );
      }
    }
    return new Uint8Array(out);
  }

  function utf8Decode(u8) {
    if (typeof TextDecoder !== "undefined") {
      return new TextDecoder("utf-8", { fatal: false }).decode(u8);
    }
    var s = "";
    for (var i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]);
    try {
      return decodeURIComponent(escape(s));
    } catch (e) {
      return s;
    }
  }

  function codePointsOf(text) {
    // Iterate Unicode scalars (handles JS surrogate pairs)
    var cps = [];
    for (var i = 0; i < text.length; ) {
      var cp = text.codePointAt(i);
      cps.push(cp);
      i += cp > 0xffff ? 2 : 1;
    }
    return cps;
  }

  // ---------------------------------------------------------------------------
  // ASCENT-V scalar packing (FROZEN lab map)
  // ---------------------------------------------------------------------------

  function rejectSurrogate(cp) {
    if (cp >= 0xd800 && cp <= 0xdfff) {
      throw new AscentError(
        "UTF-16 surrogates are illegal on ASCENT wire: U+" +
          cp.toString(16).toUpperCase().padStart(4, "0")
      );
    }
    if (cp < 0 || cp > 0x10ffff) {
      throw new AscentError("codepoint out of range: 0x" + cp.toString(16));
    }
  }

  function encodeScalar(cp) {
    rejectSurrogate(cp);
    if (cp < 0x80) return [cp];

    // 2-byte: U+0080..U+027F
    if (cp <= 0x027f) {
      var v2 = cp - 0x80;
      return [0xd0 | ((v2 >> 5) & 0x0f), contByte(v2 & 0x1f)];
    }

    // 3-byte: U+0280..U+427F
    if (cp <= 0x427f) {
      var v3 = cp - 0x280;
      return [
        0xe0 | ((v3 >> 10) & 0x0f),
        contByte((v3 >> 5) & 0x1f),
        contByte(v3 & 0x1f),
      ];
    }

    // 4-byte: U+4280.. when v fits in 18 bits with top 0..4 (max cp U+2C07F)
    var v4 = cp - 0x4280;
    if (v4 >= 0 && v4 < (5 << 15)) {
      var top = v4 >> 15; // 0..4
      return [
        0xf0 | top,
        contByte((v4 >> 10) & 0x1f),
        contByte((v4 >> 5) & 0x1f),
        contByte(v4 & 0x1f),
      ];
    }

    // LONG form: F5 03 + cp as u24be (P3 default plane)
    if (cp > 0xffffff) {
      throw new AscentError(
        "scalar exceeds u24: U+" + cp.toString(16).toUpperCase()
      );
    }
    return [0xf5, PLANE_P3, (cp >> 16) & 0xff, (cp >> 8) & 0xff, cp & 0xff];
  }

  function decodeAscentVAt(data, i) {
    var n = data.length;
    if (i >= n) return null;
    var b0 = data[i];

    // 2-byte D0-DF + Cont
    if (b0 >= 0xd0 && b0 <= 0xdf) {
      if (i + 1 >= n) throw new AscentError("truncated ASCENT-V 2-byte at " + i);
      var c1 = data[i + 1];
      if (!Cont.isCont(c1)) {
        throw new AscentError("bad ASCENT-V 2-byte cont at " + i);
      }
      var v2 = ((b0 & 0x0f) << 5) | contVal(c1);
      return { cp: 0x80 + v2, end: i + 2 };
    }

    // 3-byte E0-EF + 2 Cont
    if (b0 >= 0xe0 && b0 <= 0xef) {
      if (i + 2 >= n) throw new AscentError("truncated ASCENT-V 3-byte at " + i);
      var c3a = data[i + 1];
      var c3b = data[i + 2];
      if (!(Cont.isCont(c3a) && Cont.isCont(c3b))) {
        throw new AscentError("bad ASCENT-V 3-byte cont at " + i);
      }
      var v3 = ((b0 & 0x0f) << 10) | (contVal(c3a) << 5) | contVal(c3b);
      return { cp: 0x280 + v3, end: i + 3 };
    }

    // 4-byte F0-F4 + 3 Cont
    if (b0 >= 0xf0 && b0 <= 0xf4) {
      if (i + 3 >= n) throw new AscentError("truncated ASCENT-V 4-byte at " + i);
      var c4a = data[i + 1];
      var c4b = data[i + 2];
      var c4c = data[i + 3];
      if (!(Cont.isCont(c4a) && Cont.isCont(c4b) && Cont.isCont(c4c))) {
        throw new AscentError("bad ASCENT-V 4-byte cont at " + i);
      }
      var v4 =
        ((b0 & 0x07) << 15) |
        (contVal(c4a) << 10) |
        (contVal(c4b) << 5) |
        contVal(c4c);
      return { cp: 0x4280 + v4, end: i + 4 };
    }

    // LONG form F5 03 + u24be(cp)
    if (b0 === 0xf5) {
      if (i + 1 >= n) throw new AscentError("truncated F5 plane at " + i);
      var plane = data[i + 1];
      if (plane !== PLANE_P3) {
        // Not the lab long-scalar form; not a V lead for text merge
        return null;
      }
      if (i + 4 >= n) throw new AscentError("truncated F5 03 u24 at " + i);
      var cp =
        (data[i + 2] << 16) | (data[i + 3] << 8) | data[i + 4];
      if (cp >= 0xd800 && cp <= 0xdfff) {
        throw new AscentError(
          "surrogate on wire U+" + cp.toString(16).toUpperCase()
        );
      }
      if (cp > 0x10ffff) {
        throw new AscentError(
          "scalar out of range U+" + cp.toString(16).toUpperCase()
        );
      }
      return { cp: cp, end: i + 5 };
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // Encode text (header / role / non-ascii modes)
  // ---------------------------------------------------------------------------

  var OPCODE_BY_NAME = {
    STOP: 0x0001,
    ROLE: 0x0002,
    TOOL: 0x0003,
    THINK: 0x0004,
    HANDOFF: 0x0005,
    CAP: 0x0006,
    SAFETY: 0x0007,
  };

  function asciiBytes(str, label) {
    var out = [];
    var s = str == null ? "" : String(str);
    for (var i = 0; i < s.length; i++) {
      var cp = s.charCodeAt(i);
      if (cp > 0x7f) {
        throw new AscentError((label || "field") + " must be ASCII");
      }
      out.push(cp);
    }
    return out;
  }

  /**
   * Encode a P5 agent frame: 9A C1 ver opcode:u16be flags len:u16be args 9B
   * opts: { opcode|opcodeName, ver, flags, args (Uint8Array|number[]), name (ROLE/TOOL/HANDOFF) }
   */
  function encodeAgentFrame(opts) {
    var o = opts || {};
    var opcode = o.opcode;
    if (opcode == null && o.opcodeName) {
      opcode = OPCODE_BY_NAME[String(o.opcodeName).toUpperCase()];
    }
    if (opcode == null) throw new AscentError("agent opcode required");
    var ver = o.ver != null ? o.ver & 0xff : 0x01;
    var flags = o.flags != null ? o.flags & 0xff : 0x00;
    var args = [];
    if (o.args) {
      var src = o.args;
      for (var ai = 0; ai < src.length; ai++) args.push(src[ai] & 0xff);
    } else if (o.name != null && (opcode === 0x0002 || opcode === 0x0003 || opcode === 0x0005)) {
      var nameBytes = asciiBytes(o.name, "agent name");
      if (nameBytes.length > 64) throw new AscentError("agent name too long (max 64)");
      args.push(nameBytes.length);
      for (var nj = 0; nj < nameBytes.length; nj++) args.push(nameBytes[nj]);
    } else if (o.payload != null) {
      // Opaque THINK / SAFETY / CAP body as raw bytes or UTF-8 text
      var pay =
        typeof o.payload === "string" ? utf8Encode(o.payload) : o.payload;
      for (var pi = 0; pi < pay.length; pi++) args.push(pay[pi] & 0xff);
    }
    if (args.length > 8192) throw new AscentError("agent args exceed max 8192");
    var out = [0x9a, 0xc1, ver];
    pushU16(out, opcode);
    out.push(flags);
    pushU16(out, args.length);
    for (var k = 0; k < args.length; k++) out.push(args[k]);
    out.push(0x9b);
    return out;
  }

  function encodeRoleFrame(role) {
    return encodeAgentFrame({ opcode: 0x0002, name: role });
  }

  /**
   * Multimodal unit: 9D 4D kind codec:u16be flags hash-alg [hash] len:u64be [body]
   * opts: { mmKind|kindName, codec, flags, hashAlg, hash (Uint8Array), body|text|ref }
   */
  function encodeMm(opts) {
    var o = opts || {};
    var wireKind = o.mmKind;
    if (wireKind == null && o.kindName) {
      var kn = String(o.kindName).toUpperCase();
      wireKind = kn === "REF" ? 1 : kn === "INLINE" ? 2 : kn === "CHUNK" ? 3 : kn === "END" ? 4 : null;
    }
    if (wireKind == null) wireKind = 2;
    var codec = o.codec != null ? o.codec : 0x0001;
    var flags = o.flags != null ? o.flags & 0xff : 0;
    var hashAlg = o.hashAlg != null ? o.hashAlg & 0xff : 0;
    var hlen = HASH_LEN[hashAlg];
    if (hlen === undefined) throw new AscentError("unknown hash-alg " + hashAlg);
    var digest = [];
    if (o.hash) {
      for (var hi = 0; hi < o.hash.length; hi++) digest.push(o.hash[hi] & 0xff);
    }
    if (digest.length !== hlen) {
      if (hashAlg === 0) digest = [];
      else if (digest.length === 0) {
        for (var z = 0; z < hlen; z++) digest.push(0);
      } else {
        throw new AscentError("hash length mismatch for alg " + hashAlg);
      }
    }
    var body;
    if (o.body) body = o.body;
    else if (o.ref != null) body = utf8Encode(String(o.ref));
    else if (o.text != null) body = utf8Encode(String(o.text));
    else body = new Uint8Array(0);
    var out = [0x9d, 0x4d, wireKind & 0xff];
    pushU16(out, codec);
    out.push(flags);
    out.push(hashAlg);
    for (var d = 0; d < digest.length; d++) out.push(digest[d]);
    pushU64(out, body.length);
    for (var bi = 0; bi < body.length; bi++) out.push(body[bi] & 0xff);
    return out;
  }

  function encodeMmInlineUtf8(body, codec) {
    return encodeMm({
      mmKind: 2,
      codec: codec == null ? 0x0001 : codec,
      hashAlg: 0,
      body: body,
    });
  }

  function encodeMmRef(ref, opts) {
    var o = opts || {};
    return encodeMm({
      mmKind: 1,
      codec: o.codec != null ? o.codec : 0x0005,
      flags: o.flags || 0,
      hashAlg: o.hashAlg != null ? o.hashAlg : 1,
      hash: o.hash,
      ref: ref,
    });
  }

  /**
   * Crypto envelope sketch: 9C 4B alg:u16be kid-len kid nonce-len nonce ct-len:u32be ct
   * Lab only - not production crypto.
   */
  function encodeCrypto(opts) {
    var o = opts || {};
    var alg = o.alg != null ? o.alg : 0x010b; // AEGIR-DEMO
    var kid = o.kid != null ? (typeof o.kid === "string" ? utf8Encode(o.kid) : o.kid) : utf8Encode("demo-kid");
    var nonce =
      o.nonce != null
        ? typeof o.nonce === "string"
          ? utf8Encode(o.nonce)
          : o.nonce
        : new Uint8Array(12);
    var ct =
      o.ct != null
        ? typeof o.ct === "string"
          ? utf8Encode(o.ct)
          : o.ct
        : new Uint8Array(0);
    if (kid.length > 255) throw new AscentError("kid too long");
    if (nonce.length > 255) throw new AscentError("nonce too long");
    var out = [0x9c, 0x4b];
    pushU16(out, alg);
    out.push(kid.length);
    for (var i = 0; i < kid.length; i++) out.push(kid[i] & 0xff);
    out.push(nonce.length);
    for (var j = 0; j < nonce.length; j++) out.push(nonce[j] & 0xff);
    out.push(
      (ct.length >>> 24) & 0xff,
      (ct.length >>> 16) & 0xff,
      (ct.length >>> 8) & 0xff,
      ct.length & 0xff
    );
    for (var k = 0; k < ct.length; k++) out.push(ct[k] & 0xff);
    return out;
  }

  function concatBytes(parts) {
    var total = 0;
    for (var i = 0; i < parts.length; i++) total += parts[i].length;
    var out = new Uint8Array(total);
    var o = 0;
    for (var j = 0; j < parts.length; j++) {
      out.set(parts[j] instanceof Uint8Array ? parts[j] : new Uint8Array(parts[j]), o);
      o += parts[j].length;
    }
    return out;
  }

  /** Conformance helpers for the lab dashboard. */
  function analyzeStream(u8) {
    var pureP0 = true;
    var p0 = 0;
    var ext = 0;
    var planeHits = {
      P0: 0,
      P1: 0,
      P2: 0,
      P3: 0,
      P4: 0,
      P5: 0,
      P6: 0,
      P7: 0,
      P8: 0,
      P9: 0,
      P10: 0,
    };
    for (var i = 0; i < u8.length; i++) {
      var b = u8[i];
      if (b < 0x80) {
        p0++;
        planeHits.P0++;
      } else {
        pureP0 = false;
        ext++;
        if (b === 0x9a || b === 0x9b) planeHits.P5++;
        else if (b === 0x9d || b === 0x4d) planeHits.P6++;
        else if (b === 0x9c || b === 0x4b) planeHits.P7++;
        else if (b === 0xc0) planeHits.P8++;
        else if (b === 0xc1 || b === 0xc5) planeHits.P2++;
        else if (b >= 0x80 && b <= 0x9f) planeHits.P1++;
        else if (b >= 0xa0 && b <= 0xbf) planeHits.P3++;
        else if (b >= 0xd0 && b <= 0xf5) planeHits.P3++;
        else planeHits.P10++;
      }
    }
    // P9 sync scan
    for (var s = 0; s + 3 < u8.length; s++) {
      if (
        u8[s] === 0xd5 &&
        u8[s + 1] === 0xe5 &&
        u8[s + 2] === 0xc0 &&
        u8[s + 3] === 0xde
      ) {
        planeHits.P9++;
      }
    }
    var events = null;
    var decodeOk = true;
    var decodeError = null;
    try {
      events = decodeStream(u8);
    } catch (e) {
      decodeOk = false;
      decodeError = e.message || String(e);
    }
    return {
      total: u8.length,
      p0: p0,
      ext: ext,
      p0pct: u8.length ? (100 * p0) / u8.length : 100,
      pureAscent7: pureP0,
      parseLawOk: true, // P0 bytes are never remapped by definition
      decodeOk: decodeOk,
      decodeError: decodeError,
      planeHits: planeHits,
      events: events,
      unitKinds: events
        ? events.map(function (e) {
            return e.kind;
          })
        : [],
    };
  }

  /**
   * Encode plain text to ASCENT wire bytes (Uint8Array).
   * opts: { header?: bool, roleName?: string, nonAscii?: "v"|"bridge"|"reject" }
   */
  function encodeText(text, opts) {
    var o = opts || {};
    var nonAscii = o.nonAscii || "v";
    if (nonAscii !== "v" && nonAscii !== "bridge" && nonAscii !== "reject") {
      throw new AscentError("unknown nonAscii mode: " + nonAscii);
    }
    var out = [];
    if (o.header) {
      for (var h = 0; h < HEADER_MAGIC.length; h++) {
        out.push(HEADER_MAGIC.charCodeAt(h));
      }
    }

    var s = text == null ? "" : String(text);

    if (nonAscii === "reject") {
      for (var r = 0; r < s.length; ) {
        var rcp = s.codePointAt(r);
        if (rcp > 0x7f) {
          throw new AscentError(
            "ASCENT-7 rejects non-ASCII U+" +
              rcp.toString(16).toUpperCase().padStart(4, "0")
          );
        }
        out.push(rcp);
        r += 1;
      }
    } else if (nonAscii === "v") {
      var cps = codePointsOf(s);
      for (var vi = 0; vi < cps.length; vi++) {
        var unit = encodeScalar(cps[vi]);
        for (var uj = 0; uj < unit.length; uj++) out.push(unit[uj]);
      }
    } else {
      // bridge: ASCII runs P0; non-ascii runs -> MM INLINE utf-8
      var i = 0;
      while (i < s.length) {
        var cp = s.codePointAt(i);
        rejectSurrogate(cp);
        var step = cp > 0xffff ? 2 : 1;
        if (cp < 0x80) {
          out.push(cp);
          i += step;
          continue;
        }
        // gather non-ascii run (scalar by scalar)
        var runStart = i;
        while (i < s.length) {
          var c2 = s.codePointAt(i);
          rejectSurrogate(c2);
          if (c2 < 0x80) break;
          i += c2 > 0xffff ? 2 : 1;
        }
        var runStr = s.slice(runStart, i);
        var body = utf8Encode(runStr);
        var mm = encodeMmInlineUtf8(body, 0x0001);
        for (var mj = 0; mj < mm.length; mj++) out.push(mm[mj]);
      }
    }

    if (o.roleName) {
      var roleBytes = encodeRoleFrame(String(o.roleName));
      for (var rj = 0; rj < roleBytes.length; rj++) out.push(roleBytes[rj]);
    }

    return new Uint8Array(out);
  }

  // ---------------------------------------------------------------------------
  // Decode helpers (agent / mm / crypto / def)
  // ---------------------------------------------------------------------------

  function unescapeAgentArgs(raw) {
    var out = [];
    var i = 0;
    while (i < raw.length) {
      if (raw[i] === 0xc1 && i + 2 < raw.length && raw[i + 1] === 0x1b) {
        out.push(raw[i + 2]);
        i += 3;
        continue;
      }
      if (raw[i] === 0x9a || raw[i] === 0x9b) {
        throw new AscentError("bare fence byte inside agent args");
      }
      out.push(raw[i]);
      i++;
    }
    return new Uint8Array(out);
  }

  function parseRoleOrName(args) {
    if (!args.length) return { name: "" };
    var n = args[0];
    if (1 + n > args.length) throw new AscentError("name_len exceeds args");
    var nameBytes = args.slice(1, 1 + n);
    var name;
    try {
      name = utf8Decode(nameBytes);
    } catch (e) {
      name = hexOf(nameBytes);
    }
    return { name: name, nameBytes: hexOf(nameBytes) };
  }

  function decodeAgent(body, start) {
    var i = start + 1;
    if (i >= body.length || body[i] !== 0xc1) {
      throw new AscentError("AGENT_OPEN without C1 AGENT_OP");
    }
    i += 1;
    if (i + 1 + 2 + 1 + 2 > body.length) {
      throw new AscentError("truncated agent header");
    }
    var ver = body[i++];
    var opcode;
    var pair = u16be(body, i);
    opcode = pair[0];
    i = pair[1];
    var flags = body[i++];
    var alenPair = u16be(body, i);
    var alen = alenPair[0];
    i = alenPair[1];
    if (alen > 8192) throw new AscentError("agent args exceed max 8192");
    if (i + alen > body.length) throw new AscentError("truncated agent args");
    var argsWire = body.slice(i, i + alen);
    i += alen;
    if (i >= body.length || body[i] !== 0x9b) {
      throw new AscentError("AGENT missing CLOSE 0x9B");
    }
    i += 1;
    var args = unescapeAgentArgs(argsWire);
    var ev = {
      kind: "agent",
      ver: ver,
      opcode: opcode,
      opcodeName: OPCODE[opcode] || "UNKNOWN_0x" + opcode.toString(16),
      flags: flags,
      argsWireLen: alen,
      argsHex: hexOf(args),
      offset: start,
      end: i,
    };
    if (opcode === 0x0002 || opcode === 0x0003 || opcode === 0x0005) {
      var parsed = parseRoleOrName(args);
      ev.name = parsed.name;
      if (parsed.nameBytes) ev.nameBytes = parsed.nameBytes;
    }
    return [ev, i];
  }

  function decodeMm(body, start) {
    // Decode multimodal frame. Event kind stays "multimodal"; wire kind -> mmKind.
    var i = start + 1;
    if (i >= body.length || body[i] !== 0x4d) {
      throw new AscentError("MM_MARK without 0x4D 'M'");
    }
    i += 1;
    if (i >= body.length) throw new AscentError("truncated MM kind");
    var wireKind = body[i++];
    var codecPair = u16be(body, i);
    var codec = codecPair[0];
    i = codecPair[1];
    if (i >= body.length) throw new AscentError("truncated MM flags");
    var flags = body[i++];
    if (i >= body.length) throw new AscentError("truncated MM hash-alg");
    var hashAlg = body[i++];
    var hlen = HASH_LEN[hashAlg];
    if (hlen === undefined) {
      throw new AscentError("unknown hash-alg " + hashAlg);
    }
    if (i + hlen > body.length) throw new AscentError("truncated MM hash");
    var digest = body.slice(i, i + hlen);
    i += hlen;
    var mlenPair = u64be(body, i);
    var mlen = mlenPair[0];
    i = mlenPair[1];
    if (mlen > 256 * 1024 * 1024) {
      throw new AscentError("MM body over hard cap");
    }
    if (i + mlen > body.length) throw new AscentError("truncated MM body");
    var payload = body.slice(i, i + mlen);
    i += mlen;
    // Never put wire kind in field "kind" - that is the event type string.
    var ev = {
      kind: "multimodal",
      mmKind: wireKind,
      kindName: MM_KIND[wireKind] || "UNKNOWN_" + wireKind,
      codec: codec,
      flags: flags,
      hashAlg: HASH_ALG[hashAlg] || String(hashAlg),
      hashHex: hexOf(digest),
      len: mlen,
      offset: start,
      end: i,
    };
    if (wireKind === 1) {
      // REF
      try {
        ev.ref = utf8Decode(payload);
      } catch (e) {
        ev.refHex = hexOf(payload);
      }
    } else if (wireKind === 2) {
      // INLINE
      if (codec === 0x0001) {
        try {
          ev.text = utf8Decode(payload);
        } catch (e2) {
          ev.bodyHex =
            mlen <= 64
              ? hexOf(payload)
              : hexOf(payload.slice(0, 32)) + "...";
        }
      } else {
        ev.bodyHex =
          mlen <= 64 ? hexOf(payload) : hexOf(payload.slice(0, 32)) + "...";
      }
    } else {
      ev.bodyHex =
        mlen <= 64 ? hexOf(payload) : hexOf(payload.slice(0, 32)) + "...";
    }
    return [ev, i];
  }

  function decodeCrypto(body, start) {
    var i = start + 1;
    if (i >= body.length || body[i] !== 0x4b) {
      throw new AscentError("CRYPTO_MARK without 0x4B 'K'");
    }
    i += 1;
    var algPair = u16be(body, i);
    var alg = algPair[0];
    i = algPair[1];
    if (i >= body.length) throw new AscentError("truncated crypto kid-len");
    var kidLen = body[i++];
    if (i + kidLen > body.length) throw new AscentError("truncated kid");
    var kid = body.slice(i, i + kidLen);
    i += kidLen;
    if (i >= body.length) throw new AscentError("truncated nonce-len");
    var nonceLen = body[i++];
    if (i + nonceLen > body.length) throw new AscentError("truncated nonce");
    var nonce = body.slice(i, i + nonceLen);
    i += nonceLen;
    var ctPair = u32be(body, i);
    var ctLen = ctPair[0];
    i = ctPair[1];
    if (i + ctLen > body.length) throw new AscentError("truncated ciphertext");
    i += ctLen;
    return [
      {
        kind: "crypto",
        alg: alg,
        kidHex: hexOf(kid),
        nonceHex: hexOf(nonce),
        ctLen: ctLen,
        offset: start,
        end: i,
      },
      i,
    ];
  }

  function decodeDef(body, start) {
    var i = start + 1;
    if (i >= body.length) throw new AscentError("truncated DEF schema");
    var schema = body[i++];
    var dPair = u32be(body, i);
    var dlen = dPair[0];
    i = dPair[1];
    if (dlen > 16 * 1024 * 1024) throw new AscentError("DEF over hard cap");
    if (i + dlen > body.length) throw new AscentError("truncated DEF body");
    i += dlen;
    return [
      {
        kind: "def",
        schema: schema,
        len: dlen,
        offset: start,
        end: i,
      },
      i,
    ];
  }

  function pathhintSkipEvent(start, end, schema, reason, flags, bodyLen) {
    return {
      kind: "pathhint",
      schema: schema,
      applied: false,
      skipped: true,
      reason: reason,
      flags: flags || 0,
      len: bodyLen || 0,
      offset: start,
      end: end,
    };
  }

  function parsePathhintV1Body(body, start, end, schema) {
    if (!body.length) {
      return pathhintSkipEvent(start, end, schema, "truncated_body", 0, 0);
    }
    var flags = body[0];
    if (flags & FLAG_RESERVED_MASK) {
      return pathhintSkipEvent(
        start,
        end,
        schema,
        "unknown_flags",
        flags,
        body.length
      );
    }
    var want = flags & FLAG_CRC ? PATHHINT_BODY_LEN_CRC : PATHHINT_BODY_LEN;
    if (body.length !== want) {
      return pathhintSkipEvent(
        start,
        end,
        schema,
        "bad_body_len",
        flags,
        body.length
      );
    }
    if (flags & FLAG_CRC) {
      var got =
        ((body[PATHHINT_BODY_LEN] << 24) |
          (body[PATHHINT_BODY_LEN + 1] << 16) |
          (body[PATHHINT_BODY_LEN + 2] << 8) |
          body[PATHHINT_BODY_LEN + 3]) >>>
        0;
      var expect = crc32Ieee(body.slice(0, PATHHINT_BODY_LEN));
      if (got !== expect) {
        return pathhintSkipEvent(start, end, schema, "crc_fail", flags, body.length);
      }
    }
    var pathPair = u64be(body, 1);
    var pathId = pathPair[0];
    var capPair = u32be(body, 9);
    var capRaw = capPair[0];
    var freezePair = u32be(body, 13);
    var freezeMs = freezePair[0];
    var confPair = u16be(body, 17);
    var confU16 = confPair[0];
    var ttlPair = u32be(body, 19);
    var ttlMs = ttlPair[0];
    var obstU8 = body[23];
    var elevPair = i16be(body, 24);
    var elevI16 = elevPair[0];
    if (confU16 > 10000) {
      return pathhintSkipEvent(
        start,
        end,
        schema,
        "confidence_range",
        flags,
        body.length
      );
    }
    var nextBps = flags & FLAG_CAP_KBPS ? capRaw * 1000 : capRaw;
    var nextKbps = flags & FLAG_CAP_KBPS ? capRaw : capRaw ? Math.floor((capRaw + 999) / 1000) : 0;
    var obst = flags & FLAG_HAS_OBSTRUCTION ? obstU8 / 255.0 : null;
    var elev =
      flags & FLAG_HAS_ELEV && elevI16 !== ELEV_ABSENT ? elevI16 / 10.0 : null;
    return {
      kind: "pathhint",
      schema: schema,
      applied: true,
      skipped: false,
      reason: "",
      flags: flags,
      pathId: pathId,
      path_id: pathId,
      nextCapacityBps: nextBps,
      next_capacity_bps: nextBps,
      nextCapacityKbps: nextKbps,
      next_capacity_kbps: nextKbps,
      freezeMs: freezeMs,
      freeze_ms: freezeMs,
      freezeUntilMs: freezeMs,
      freeze_until_ms: freezeMs,
      confidence: confU16 / 10000.0,
      ttlMs: ttlMs,
      ttl_ms: ttlMs,
      obstruction: obst,
      elevDeg: elev,
      elev_deg: elev,
      crc: !!(flags & FLAG_CRC),
      len: body.length,
      offset: start,
      end: end,
    };
  }

  function decodeSkystate(body, start) {
    var i = start + 1;
    if (i >= body.length) throw new AscentError("truncated SKYSTATE schema");
    var schema = body[i++];
    var lenPair = u16be(body, i);
    var blen = lenPair[0];
    i = lenPair[1];
    if (blen > P2_SKIP_CAP) throw new AscentError("SKYSTATE body over skip cap");
    if (i + blen > body.length) throw new AscentError("truncated SKYSTATE body");
    var payload = body.slice(i, i + blen);
    i += blen;
    if (schema !== PATHHINT_SCHEMA_V1) {
      return [pathhintSkipEvent(start, i, schema, "unknown_schema", 0, blen), i];
    }
    if (blen > PATHHINT_MAX_BODY) {
      return [pathhintSkipEvent(start, i, schema, "over_schema_cap", 0, blen), i];
    }
    return [parsePathhintV1Body(payload, start, i, schema), i];
  }

  function encodePathhint(opts) {
    opts = opts || {};
    var pathId = opts.pathId != null ? opts.pathId : opts.path_id != null ? opts.path_id : 0;
    var confidence =
      opts.confidence != null ? Number(opts.confidence) : 0;
    if (confidence < 0 || confidence > 1) {
      throw new AscentError("confidence must be in [0, 1]");
    }
    var freezeMs =
      opts.freezeMs != null
        ? opts.freezeMs
        : opts.freeze_ms != null
          ? opts.freeze_ms
          : opts.freezeUntilMs != null
            ? opts.freezeUntilMs
            : opts.freeze_until_ms != null
              ? opts.freeze_until_ms
              : 0;
    var ttlMs = opts.ttlMs != null ? opts.ttlMs : opts.ttl_ms != null ? opts.ttl_ms : 0;
    if (freezeMs < 0 || ttlMs < 0) {
      throw new AscentError("freeze_ms and ttl_ms must be >= 0");
    }
    var flags = FLAG_RELATIVE_FREEZE;
    var capRaw = 0;
    var bps = opts.nextCapacityBps != null ? opts.nextCapacityBps : opts.next_capacity_bps;
    var kbps = opts.nextCapacityKbps != null ? opts.nextCapacityKbps : opts.next_capacity_kbps;
    if (kbps != null && bps != null) {
      throw new AscentError("pass next_capacity_bps or next_capacity_kbps, not both");
    }
    if (kbps != null) {
      flags |= FLAG_CAP_KBPS;
      capRaw = kbps >>> 0;
    } else if (bps == null) {
      capRaw = 0;
    } else if (bps > 0xffffffff) {
      flags |= FLAG_CAP_KBPS;
      capRaw = Math.floor((bps + 999) / 1000) >>> 0;
    } else {
      capRaw = bps >>> 0;
    }
    var obst = opts.obstruction;
    var obstU8 = OBSTRUCTION_ABSENT;
    if (obst != null && obst !== "") {
      obst = Number(obst);
      if (obst < 0 || obst > 1) throw new AscentError("obstruction must be in [0, 1]");
      flags |= FLAG_HAS_OBSTRUCTION;
      obstU8 = Math.round(obst * 255);
      if (obstU8 > 255) obstU8 = 255;
    }
    var elev = opts.elevDeg != null ? opts.elevDeg : opts.elev_deg;
    var elevI16 = ELEV_ABSENT;
    if (elev != null && elev !== "") {
      elev = Number(elev);
      if (elev < -90 || elev > 90) throw new AscentError("elev_deg must be in [-90, 90]");
      flags |= FLAG_HAS_ELEV;
      elevI16 = Math.round(elev * 10);
    }
    var wantCrc = !!(opts.crc || opts.useCrc);
    if (wantCrc) flags |= FLAG_CRC;
    var confU16 = Math.round(confidence * 10000);
    var body = [];
    body.push(flags & 0xff);
    pushU64(body, pathId);
    pushU32(body, capRaw);
    pushU32(body, freezeMs >>> 0);
    pushU16(body, confU16);
    pushU32(body, ttlMs >>> 0);
    body.push(obstU8);
    pushI16(body, elevI16);
    if (body.length !== PATHHINT_BODY_LEN) {
      throw new AscentError("PATHHINT v1 body length bug");
    }
    if (wantCrc) {
      var crc = crc32Ieee(new Uint8Array(body));
      pushU32(body, crc);
    }
    var out = [LEAD_SKYSTATE, PATHHINT_SCHEMA_V1];
    pushU16(out, body.length);
    return new Uint8Array(out.concat(body));
  }

  function canonicalPathhintBytes(crc) {
    return encodePathhint({
      pathId: 0x42,
      nextCapacityBps: 50000000,
      freezeMs: 15000,
      confidence: 0.8,
      ttlMs: 30000,
      obstruction: 0.2,
      elevDeg: 42.0,
      crc: !!crc,
    });
  }

  function recommendIntegrity(profile) {
    var p = String(profile || "")
      .trim()
      .toUpperCase()
      .replace(/_/g, "-");
    if (
      p === "ASCENT-D" ||
      p === "D" ||
      p === "DEEP" ||
      p === "DEEP-SPACE" ||
      p === "SPOOL"
    ) {
      return {
        profile: "ASCENT-D",
        mode: "p9",
        doubleFec: false,
        usePathhintCrc: false,
        wrapP9: true,
        note:
          "ASCENT-D: outer RS(255,223) erase-on-fail. Skip extra PATHHINT CRC. Spool/deep-space, not interactive Starlink IP.",
      };
    }
    if (
      p === "ASCENT-E-LEO" ||
      p === "E-LEO" ||
      p === "LEO" ||
      p === "LEO-IP" ||
      p === "STARLINK" ||
      p === "SKY" ||
      p === "SKYPULSE"
    ) {
      return {
        profile: "ASCENT-E-LEO",
        mode: "crc",
        doubleFec: false,
        usePathhintCrc: true,
        wrapP9: false,
        note:
          "ASCENT-E-LEO: Starlink/LEO IP already has PHY+TLS. Prefer light PATHHINT CRC or none. Do not wrap interactive turns in P9 RS. PATHHINT is a goodput hint, not an RF Mbps upgrade.",
      };
    }
    return {
      profile: "ASCENT-E",
      mode: "none",
      doubleFec: false,
      usePathhintCrc: false,
      wrapP9: false,
      note: "ASCENT-E default: plain PATHHINT unit; optional CRC. P9 only if integrity requested.",
    };
  }

  /**
   * Full decode to list of event objects.
   * P0 + ASCENT-V scalars merge into continuous text events
   * (kind="text", text=..., ascii=..., offset, end).
   * agent / multimodal (mmKind) / def / crypto / pathhint / pad as separate events.
   * Never overwrite event kind with numeric wire fields.
   */
  function decodeStream(data) {
    var events = [];
    var i = 0;
    var textChars = [];
    var textStart = 0;

    function flushText(end) {
      if (!textChars.length) return;
      var s = textChars.join("");
      var hasHigh = false;
      for (var t = 0; t < s.length; t++) {
        if (s.charCodeAt(t) > 0x7f) {
          hasHigh = true;
          break;
        }
      }
      events.push({
        kind: "text",
        text: s,
        ascii: s,
        len: hasHigh ? utf8Encode(s).length : s.length,
        offset: textStart,
        end: end,
      });
      textChars = [];
    }

    function pushChar(ch, at) {
      if (!textChars.length) textStart = at;
      textChars.push(ch);
    }

    while (i < data.length) {
      var b = data[i];
      if (b < 0x80) {
        // P0: String.fromCharCode for 0x00-0x7F (TextDecoder("ascii") unsupported)
        pushChar(String.fromCharCode(b), i);
        i += 1;
        continue;
      }

      // ASCENT-V (including F5 03 long scalar)
      var v = null;
      try {
        v = decodeAscentVAt(data, i);
      } catch (err) {
        if ((b >= 0xd0 && b <= 0xf4) || b === 0xf5) throw err;
        v = null;
      }
      if (v !== null) {
        pushChar(String.fromCodePoint(v.cp), i);
        i = v.end;
        continue;
      }

      flushText(i);

      if (b === 0x9a) {
        var agentPair = decodeAgent(data, i);
        events.push(agentPair[0]);
        i = agentPair[1];
        continue;
      }
      if (b === 0x9d) {
        var mmPair = decodeMm(data, i);
        events.push(mmPair[0]);
        i = mmPair[1];
        continue;
      }
      if (b === 0x9c) {
        var crPair = decodeCrypto(data, i);
        events.push(crPair[0]);
        i = crPair[1];
        continue;
      }
      if (b === 0xc0) {
        var defPair = decodeDef(data, i);
        events.push(defPair[0]);
        i = defPair[1];
        continue;
      }
      if (b === LEAD_SKYSTATE) {
        var skyPair = decodeSkystate(data, i);
        events.push(skyPair[0]);
        i = skyPair[1];
        continue;
      }
      if (b === 0x9f) {
        events.push({ kind: "pad", count: 1, offset: i, end: i + 1 });
        i += 1;
        continue;
      }
      // Cont alone is illegal as lead
      if (Cont.isCont(b)) {
        throw new AscentError(
          "orphan Cont lead 0x" + b.toString(16) + " at offset " + i
        );
      }
      throw new AscentError(
        "unsupported lead byte 0x" + b.toString(16) + " at offset " + i
      );
    }

    flushText(i);
    return events;
  }

  var AEGIR_ALG = {
    0x0100: "AEGIR-SUITE-1",
    0x0101: "AEGIR-DCH-KEM-768",
    0x0102: "AEGIR-DCH-KEM-1024",
    0x0103: "AEGIR-AEAD-AES256-GCMSIV",
    0x0104: "AEGIR-AEAD-CHACHA20POLY",
    0x0105: "AEGIR-HBOP-SHA512",
    0x0106: "AEGIR-SIG-HYBRID-65",
    0x0107: "AEGIR-SIG-SLH-128f",
    0x0108: "AEGIR-DSR-STATE",
    0x0109: "AEGIR-MPR-V1",
    0x010a: "AEGIR-IMS-SEAL",
    0x010b: "AEGIR-DEMO-X25519-GCM",
  };

  /**
   * Lightweight AEGIR sketch: XOR demo seal for UI only (not wire crypto).
   * Real hybrid PQ lives in ref/aegir_sketch.py. This shows envelope shape.
   */
  function aegirDemoSeal(plaintext, passphrase) {
    var pt =
      typeof plaintext === "string" ? utf8Encode(plaintext) : plaintext;
    var keySrc = utf8Encode("AEGIR-DEMO|" + (passphrase || "lab"));
    var key = [];
    for (var i = 0; i < 32; i++) {
      key.push(keySrc[i % keySrc.length] ^ (0x5a + i));
    }
    var nonce = new Uint8Array(12);
    for (var n = 0; n < 12; n++) nonce[n] = (n * 17 + 0x42) & 0xff;
    var ct = new Uint8Array(pt.length);
    for (var j = 0; j < pt.length; j++) {
      ct[j] = pt[j] ^ key[j % 32] ^ nonce[j % 12];
    }
    var frame = encodeCrypto({
      alg: 0x010b,
      kid: "demo-kid-1",
      nonce: nonce,
      ct: ct,
    });
    return {
      alg: 0x010b,
      algName: AEGIR_ALG[0x010b],
      kid: "demo-kid-1",
      nonceHex: hexOf(nonce),
      ctHex: hexOf(ct),
      frame: new Uint8Array(frame),
      note: "Lab XOR sketch only. Production AEGIR uses hybrid KEM+AEAD (see design/AEGIR.md).",
    };
  }

  function aegirDemoOpen(frameU8, passphrase) {
    var events = decodeStream(frameU8);
    var cr = null;
    for (var i = 0; i < events.length; i++) {
      if (events[i].kind === "crypto") {
        cr = events[i];
        break;
      }
    }
    if (!cr) throw new AscentError("no crypto unit in stream");
    // Re-derive for sketch: re-parse ct from raw frame is heavy; lab returns metadata
    return {
      alg: cr.alg,
      algName: AEGIR_ALG[cr.alg] || ("0x" + cr.alg.toString(16)),
      kidHex: cr.kidHex,
      nonceHex: cr.nonceHex,
      ctLen: cr.ctLen,
      note: "Opened envelope metadata. Lab XOR open requires matching seal path in UI.",
    };
  }

  var AscentCodec = {
    Cont: Cont,
    contByte: contByte,
    contVal: contVal,
    encodeScalar: encodeScalar,
    decodeAscentVAt: decodeAscentVAt,
    encodeText: encodeText,
    encodeAgentFrame: encodeAgentFrame,
    encodeRoleFrame: encodeRoleFrame,
    encodeMm: encodeMm,
    encodeMmInlineUtf8: encodeMmInlineUtf8,
    encodeMmRef: encodeMmRef,
    encodeCrypto: encodeCrypto,
    encodePathhint: encodePathhint,
    decodeSkystate: decodeSkystate,
    canonicalPathhintBytes: canonicalPathhintBytes,
    recommendIntegrity: recommendIntegrity,
    crc32Ieee: crc32Ieee,
    LEAD_SKYSTATE: LEAD_SKYSTATE,
    PATHHINT_SCHEMA_V1: PATHHINT_SCHEMA_V1,
    decodeStream: decodeStream,
    analyzeStream: analyzeStream,
    concatBytes: concatBytes,
    fromHex: fromHex,
    hexOf: hexOf,
    formatHexLines: formatHexLines,
    utf8Encode: utf8Encode,
    utf8Decode: utf8Decode,
    OPCODE: OPCODE,
    OPCODE_BY_NAME: OPCODE_BY_NAME,
    MM_KIND: MM_KIND,
    HASH_ALG: HASH_ALG,
    AEGIR_ALG: AEGIR_ALG,
    aegirDemoSeal: aegirDemoSeal,
    aegirDemoOpen: aegirDemoOpen,
    HELLO_UNIVERSE_HEX: HELLO_UNIVERSE_HEX,
    HEADER_MAGIC: HEADER_MAGIC,
    AscentError: AscentError,
    version: "2.1.0-skypulse",
  };

  global.AscentCodec = AscentCodec;
})(typeof window !== "undefined" ? window : globalThis);
