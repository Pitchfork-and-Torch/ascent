/* Pure JS Reed-Solomon GF(256) matching python reedsolo (poly 0x11d).
   RS(255,223) nsym=32 systematic. Encode is bit-identical to RSCodec(32).
   Decode: syndrome BM + Chien + Forney; 1-error fast path verified.
   ASCII hyphens only. */

(function (global) {
  "use strict";

  var PRIM = 0x11d;
  var GF_EXP = new Uint8Array(512);
  var GF_LOG = new Int16Array(256);

  (function init() {
    var x = 1;
    for (var i = 0; i < 255; i++) {
      GF_EXP[i] = x;
      GF_LOG[x] = i;
      x <<= 1;
      if (x & 0x100) x ^= PRIM;
    }
    for (var j = 255; j < 512; j++) GF_EXP[j] = GF_EXP[j - 255];
    GF_LOG[0] = -1;
  })();

  function gfMul(x, y) {
    if (x === 0 || y === 0) return 0;
    return GF_EXP[GF_LOG[x] + GF_LOG[y]];
  }
  function gfDiv(x, y) {
    if (y === 0) throw new Error("div0");
    if (x === 0) return 0;
    return GF_EXP[(GF_LOG[x] + 255 - GF_LOG[y]) % 255];
  }
  function gfPow(x, p) {
    if (p === 0) return 1;
    if (x === 0) return 0;
    return GF_EXP[(GF_LOG[x] * (p % 255 + 255 * 10)) % 255];
  }
  function gfInv(x) {
    if (x === 0) throw new Error("inv0");
    return GF_EXP[255 - GF_LOG[x]];
  }

  function polyMul(p, q) {
    var r = new Uint8Array(p.length + q.length - 1);
    for (var j = 0; j < q.length; j++) {
      for (var i = 0; i < p.length; i++) {
        r[i + j] ^= gfMul(p[i], q[j]);
      }
    }
    return r;
  }

  function polyEval(p, x) {
    var y = p[0];
    for (var i = 1; i < p.length; i++) y = gfMul(y, x) ^ p[i];
    return y;
  }

  function rsGeneratorPoly(nsym) {
    var g = new Uint8Array([1]);
    for (var i = 0; i < nsym; i++) {
      g = polyMul(g, new Uint8Array([1, gfPow(2, i)]));
    }
    return g;
  }

  var GEN = {};
  function gen(nsym) {
    if (!GEN[nsym]) GEN[nsym] = rsGeneratorPoly(nsym);
    return GEN[nsym];
  }

  function rsEncode(msg, nsym) {
    nsym = nsym == null ? 32 : nsym;
    var g = gen(nsym);
    var out = new Uint8Array(msg.length + nsym);
    out.set(msg, 0);
    for (var i = 0; i < msg.length; i++) {
      var coef = out[i];
      if (coef !== 0) {
        for (var j = 1; j < g.length; j++) {
          out[i + j] ^= gfMul(g[j], coef);
        }
      }
    }
    var res = new Uint8Array(msg.length + nsym);
    res.set(msg, 0);
    res.set(out.subarray(msg.length), msg.length);
    return res;
  }

  function calcSyndromes(msg, nsym) {
    var synd = new Uint8Array(nsym);
    var any = false;
    for (var i = 0; i < nsym; i++) {
      synd[i] = polyEval(msg, gfPow(2, i));
      if (synd[i]) any = true;
    }
    return { synd: synd, any: any };
  }

  function isCodeword(cw, nsym) {
    var k = cw.length - nsym;
    var re = rsEncode(cw.subarray(0, k), nsym);
    for (var i = 0; i < cw.length; i++) {
      if (re[i] !== cw[i]) return false;
    }
    return true;
  }

  /** Berlekamp-Massey (low-first Lambda). */
  function berlekampMassey(synd) {
    var C = [1];
    var B = [1];
    var L = 0;
    var m = 1;
    var b = 1;
    for (var n = 0; n < synd.length; n++) {
      var delta = synd[n];
      for (var j = 1; j <= L; j++) {
        delta ^= gfMul(C[j], synd[n - j]);
      }
      if (delta === 0) {
        m += 1;
      } else {
        var T = C.slice();
        var coef = gfDiv(delta, b);
        var addLen = m + B.length;
        while (C.length < addLen) C.push(0);
        for (var i = 0; i < B.length; i++) {
          C[i + m] ^= gfMul(B[i], coef);
        }
        if (2 * L <= n) {
          B = T;
          L = n + 1 - L;
          b = delta;
          m = 1;
        } else {
          m += 1;
        }
      }
    }
    while (C.length > L + 1) C.pop();
    return { lambda: C, L: L };
  }

  function chienSearch(lambda, n) {
    var pos = [];
    for (var i = 0; i < n; i++) {
      // eval lambda(alpha^i) low-first
      var x = gfPow(2, i);
      var y = 0;
      var xp = 1;
      for (var j = 0; j < lambda.length; j++) {
        y ^= gfMul(lambda[j], xp);
        xp = gfMul(xp, x);
      }
      if (y === 0) pos.push(n - 1 - i);
    }
    return pos;
  }

  function forney(lambda, synd, errPos, n) {
    var nsym = synd.length;
    var omega = new Array(nsym).fill(0);
    for (var i = 0; i < nsym; i++) {
      var s = 0;
      for (var j = 0; j <= i; j++) {
        var lj = j < lambda.length ? lambda[j] : 0;
        var si = i - j < synd.length ? synd[i - j] : 0;
        s ^= gfMul(lj, si);
      }
      omega[i] = s;
    }
    var out = {};
    for (var e = 0; e < errPos.length; e++) {
      var p = errPos[e];
      var X = gfPow(2, n - 1 - p);
      var Xi = gfInv(X);
      var num = 0;
      var xp = 1;
      for (var o = 0; o < omega.length; o++) {
        num ^= gfMul(omega[o], xp);
        xp = gfMul(xp, Xi);
      }
      var den = 0;
      for (var d = 1; d < lambda.length; d += 2) {
        den ^= gfMul(lambda[d], gfPow(Xi, d - 1));
      }
      if (den === 0) return null;
      out[p] = gfDiv(num, den);
    }
    return out;
  }

  function correctOneError(cw, synd) {
    // Fast path: X = S1/S0, pos = n-1-log(X), Y = S0
    if (synd[0] === 0) return false;
    var X = gfDiv(synd[1], synd[0]);
    var logX = GF_LOG[X];
    if (logX < 0) return false;
    var pos = cw.length - 1 - logX;
    if (pos < 0 || pos >= cw.length) return false;
    var Y = synd[0];
    // verify S2 consistency for single error: S2/S1 == X
    if (synd[1] !== 0) {
      var X2 = gfDiv(synd[2], synd[1]);
      if (X2 !== X) return false;
    }
    cw[pos] ^= Y;
    return true;
  }

  function rsDecode(msg, nsym) {
    nsym = nsym == null ? 32 : nsym;
    var cw = new Uint8Array(msg);
    var k = cw.length - nsym;
    var sc = calcSyndromes(cw, nsym);
    if (!sc.any) return cw.subarray(0, k);

    // 1-error fast path
    var trial = new Uint8Array(cw);
    if (correctOneError(trial, sc.synd) && isCodeword(trial, nsym)) {
      return trial.subarray(0, k);
    }

    // General BM path
    var bm = berlekampMassey(sc.synd);
    var errPos = chienSearch(bm.lambda, cw.length);
    if (errPos.length === 0 || errPos.length > nsym) return null;
    var corr = forney(bm.lambda, sc.synd, errPos, cw.length);
    if (!corr) return null;
    trial = new Uint8Array(cw);
    for (var p in corr) {
      if (Object.prototype.hasOwnProperty.call(corr, p)) {
        trial[p | 0] ^= corr[p];
      }
    }
    if (!isCodeword(trial, nsym)) return null;
    return trial.subarray(0, k);
  }

  var AscentRS = {
    n: 255,
    k: 223,
    nsym: 32,
    rsEncode: rsEncode,
    rsDecode: rsDecode,
    isCodeword: isCodeword,
    version: "2.0.0-rs",
    selfTest: function () {
      var msg = new Uint8Array(223);
      for (var i = 0; i < 223; i++) msg[i] = (i * 17 + 3) & 0xff;
      var enc = rsEncode(msg, 32);
      if (enc.length !== 255) return "len";
      var dec = rsDecode(enc, 32);
      if (!dec) return "clean-fail";
      for (i = 0; i < 223; i++) if (dec[i] !== msg[i]) return "clean-mismatch";
      var noisy = new Uint8Array(enc);
      noisy[50] ^= 0x5a;
      dec = rsDecode(noisy, 32);
      if (!dec) return "e1-fail";
      for (i = 0; i < 223; i++) if (dec[i] !== msg[i]) return "e1-mismatch";
      noisy = new Uint8Array(enc);
      noisy[10] ^= 0x5a;
      noisy[100] ^= 0x5a;
      dec = rsDecode(noisy, 32);
      if (!dec) return "e2-fail";
      for (i = 0; i < 223; i++) if (dec[i] !== msg[i]) return "e2-mismatch";
      return true;
    },
  };

  global.AscentRS = AscentRS;
})(typeof window !== "undefined" ? window : globalThis);
