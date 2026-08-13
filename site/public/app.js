/* ASCENT Nexus - Wire Lab 3.0 Crystal Wire
   Client-side lab UI. ASCII hyphens only. Faithful to draft SPEC packing. */

(function () {
  "use strict";

  var C = window.AscentCodec;
  var D = window.AscentDLab;
  if (!C) {
    console.error("AscentCodec missing");
    return;
  }

  var state = {
    u8: new Uint8Array(0),
    events: [],
    analysis: null,
    profile: "E",
    live: true,
    suppressText: false,
    suppressHex: false,
    selectedPlane: null,
    tourStep: 0,
    codegenLang: "python",
    dsim: { tx: null, rx: null, flips: [] },
  };

  var PLANES = [
    {
      id: "P0",
      name: "Identity",
      role: "Classic ASCII 0x00-0x7F",
      detail:
        "Sacred range. Byte less than 0x80 is classic 7-bit ASCII, width 1, forever. Greppers and shebangs still work. Pure ASCENT-7 needs no header.",
      example: "ascii",
    },
    {
      id: "P1",
      name: "C1 fences",
      role: "0x80-0x9F stream control",
      detail:
        "Fence and mark bytes for higher planes: 0x9A/0x9B agent, 0x9C crypto, 0x9D multimodal. Fixed control, never confused with P0 text.",
      example: "agent",
    },
    {
      id: "P2",
      name: "Escape nucleus",
      role: "Length-prefixed ops / DEF",
      detail:
        "C0 DEF documents, C1 AGENT_OP, and C5 SKYSTATE/PATHHINT (SkyPulse) are length-declared so unknowns can be skipped safely. PATHHINT is usable session bandwidth foresight, not an RF Mbps upgrade.",
      example: "hello",
    },
    {
      id: "P3",
      name: "Scripts",
      role: "Living + historical",
      detail:
        "ASCENT-V variable-width scalars with frozen Cont 0xA0-0xBF (5-bit). No overlongs of 0x00-0x7F. No UTF-16 surrogates on the wire.",
      example: "vscalar",
    },
    {
      id: "P4",
      name: "Emoji",
      role: "No surrogate pairs",
      detail:
        "Emoji and symbol scalars use the same ASCENT-V forms (or LONG F5 03). Surrogate pairs are illegal on the wire.",
      example: "emoji",
    },
    {
      id: "P5",
      name: "Agent",
      role: "9A / C1 / 9B frames",
      detail:
        "Fenced agent control: STOP, ROLE, TOOL, THINK, HANDOFF, CAP, SAFETY. THINK stays opaque on shared logs. SAFETY marks untrusted tool results as data.",
      example: "agent",
    },
    {
      id: "P6",
      name: "Multimodal",
      role: "REF · INLINE · CHUNK",
      detail:
        "Content-addressed REF, INLINE payloads, and CHUNK streams. Event kind is always multimodal; wire kind lives in mm_kind.",
      example: "mm",
    },
    {
      id: "P7",
      name: "Quantum-safe",
      role: "Alg registry, no silent downgrade",
      detail:
        "Crypto envelopes (9C 4B ...) carry algorithm IDs from a registry. AEGIR is the hybrid PQ companion suite. No silent alg downgrade.",
      example: "aegir",
    },
    {
      id: "P8",
      name: "Self-map",
      role: "DEF + version history",
      detail:
        "Self-describing definition documents let archives and private planes declare structure without redefining P0-P2.",
      example: "hello",
    },
    {
      id: "P9",
      name: "Deep space",
      role: "Sync D5E5C0DE + ECC",
      detail:
        "Outer frame for high BER links. Default production ECC RS(255,223). Parity fail erases the unit - no mojibake best-effort.",
      example: "deep",
    },
    {
      id: "P10+",
      name: "Private",
      role: "Cannot touch P0-P2",
      detail:
        "Private planes may extend for an organization or mission but must never remap sacred ASCII or the core control grammar.",
      example: "ascii",
    },
  ];

  var GALLERY = [
    { id: "hello", label: "Hello, Universe", build: buildHello },
    { id: "ascii", label: "Pure ASCII", build: buildAscii },
    { id: "agent", label: "Agent chat", build: buildAgentChat },
    { id: "agentloop", label: "Agent loop demo", build: buildAgentLoop },
    { id: "mm", label: "Multimodal REF", build: buildMm },
    { id: "vscalar", label: "ASCENT-V cafe", build: buildVScalar },
    { id: "emoji", label: "Emoji scalar", build: buildEmoji },
    { id: "aegir", label: "AEGIR envelope", build: buildAegir },
    { id: "deep", label: "Deep-space packet", build: buildDeep },
    { id: "skybrary", label: "Skybrary pack seal", build: buildSkybrarySeal },
    { id: "skypulse", label: "SkyPulse PATHHINT", build: buildSkyPulse },
    { id: "mixed", label: "Captain log", build: buildMixed },
  ];

  var TOUR = [
    {
      title: "1 · Sacred parse law",
      body:
        "Any byte less than <strong>0x80</strong> is classic ASCII forever. Load pure ASCII and watch the sacred meter stay green. Greppers still smile.",
      sample: "ascii",
    },
    {
      title: "2 · Hello, Universe",
      body:
        "The civilization kit: greppable <code>ASCENT/1.0</code> header, prose, a ROLE=guide agent frame, and a multimodal REF. Click the byte map.",
      sample: "hello",
    },
    {
      title: "3 · Agent frames",
      body:
        "Control tokens travel with the prose inside <code>0x9A ... 0x9B</code>. Try the Agent composer: ROLE, TOOL, THINK, SAFETY.",
      sample: "agent",
    },
    {
      title: "4 · Multimodal",
      body:
        "Media is a first-class unit: REF points at content by hash, INLINE carries small payloads. Insert a REF from the Multimodal playground.",
      sample: "mm",
    },
    {
      title: "5 · Deep space",
      body:
        "Wrap the stream in an ASCENT-D outer frame, inject bit flips, and watch erase-on-fail vs recovery. No mojibake when parity fails.",
      sample: "deep",
    },
    {
      title: "6 · Skybrary pack seal",
      body:
        "Integrity seal for an open Skybrary starter pack: JSON with <code>root_sha256</code>, wrapped in ASCENT-D. Decode, match the zip hash, refuse on mismatch. Live packs: skycache.jonbailey.xyz/library/",
      sample: "skybrary",
    },
    {
      title: "7 · SkyPulse PATHHINT",
      body:
        "LEO usable session bandwidth: a PATHHINT unit seeds predicted sender bottleneck (next_capacity) and freeze_until so apps/CCA waste fewer retransmits. Not an RF Mbps claim. Fail-closed erase on corrupt/stale hints. Toggle ASCENT-E-LEO vs D in the SkyPulse panel (sim).",
      sample: "skypulse",
    },
    {
      title: "8 · Captain log / mission deck",
      body:
        "A mixed stream: prose log, ROLE=pilot, SAFETY on untrusted telemetry, a deck-camera REF, and INLINE altitude. The mission HUD reads the units so humans see intent without decoding hex.",
      sample: "mixed",
    },
  ];

  var SPEC_SECTIONS = [
    {
      id: "parse",
      label: "Parse law",
      html:
        "<h3>A. Parse law (normative spirit)</h3><p>If <code>byte &lt; 0x80</code>, the unit is classic 7-bit ASCII, width 1, bit-identical forever. No overlong encodings of <code>0x00-0x7F</code>. No UTF-16 surrogates on the wire.</p><pre>if byte &lt; 0x80: classic ASCII forever\nelse: extension grammar</pre>",
      sample: "ascii",
    },
    {
      id: "agent",
      label: "Agent frames",
      html:
        "<h3>P5 Agent frame</h3><p>Fenced, length-declared control for LLM tool loops.</p><pre>0x9A AGENT_OPEN\n0xC1 ver opcode:u16be flags len:u16be args\n0x9B AGENT_CLOSE\n\nSTOP=1 ROLE=2 TOOL=3 THINK=4\nHANDOFF=5 CAP=6 SAFETY=7</pre>",
      sample: "agent",
    },
    {
      id: "mm",
      label: "Multimodal",
      html:
        "<h3>P6 Multimodal</h3><p>REF / INLINE / CHUNK. Event type string is always <code>kind=\"multimodal\"</code>; wire kind is <code>mm_kind</code>.</p><pre>9D 4D kind codec:u16be flags hash-alg hash len:u64be body</pre>",
      sample: "mm",
    },
    {
      id: "v",
      label: "ASCENT-V",
      html:
        "<h3>Frozen ASCENT-V packing (1.1+)</h3><p>Cont class <code>0xA0-0xBF</code> (5 payload bits). Shortest of 2/3/4-byte, else LONG <code>F5 03</code> + u24be.</p><pre>e acute U+00E9 -&gt; D3 A9\nrocket U+1F680 -&gt; F3 AD A0 A0</pre>",
      sample: "vscalar",
    },
    {
      id: "d",
      label: "ASCENT-D",
      html:
        "<h3>P9 Deep-space outer frame</h3><p>Default production ECC: RS(255,223). Parity fail = erase unit.</p><pre>sync   D5 E5 C0 DE\nprofile · ecc params · len · unit · parity</pre>",
      sample: "deep",
    },
    {
      id: "skypulse",
      label: "SkyPulse",
      html:
        "<h3>SkyPulse PATHHINT (P2 0xC5)</h3><p>Additive SKYSTATE unit. Schema 0x01 required fields: path_id, next_capacity (predicted sender bottleneck bits/s, not RF PHY), freeze_until, confidence, ttl. elev/obstruction optional. Fail-closed erase. ASCENT-E-LEO: light CRC or short RS, never full P9 on interactive Starlink IP. Does <strong>not</strong> raise RF Mbps. Wire Lab panel is <strong>sim</strong>.</p><pre>0xC5 schema:u8 len:u16be body\nflags path_id:u64be cap:u32be freeze:u32be\nconf:u16be ttl:u32be obst:u8 elev:i16be [crc32]</pre>",
      sample: "skypulse",
    },
    {
      id: "profiles",
      label: "Profiles",
      html:
        "<h3>Profiles</h3><p><strong>ASCENT-7</strong> pure identity · <strong>ASCENT-E</strong> Earth interchange · <strong>ASCENT-E-LEO</strong> usage of E (PATHHINT, light integrity) · <strong>ASCENT-D</strong> deep-space ECC · <strong>ASCENT-A</strong> archive / DEF-heavy.</p>",
      sample: "hello",
    },
  ];

  // ---------- builders ----------

  function buildHello() {
    return C.fromHex(C.HELLO_UNIVERSE_HEX);
  }

  function buildAscii() {
    return C.encodeText("#!/usr/bin/env bash\necho Hello, Universe.\n", {
      header: false,
      nonAscii: "reject",
    });
  }

  function buildAgentChat() {
    var parts = [];
    var hdr = C.encodeText("User: plot a course to Proxima.\n", {
      header: true,
      nonAscii: "v",
    });
    parts.push(hdr);
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({ opcodeName: "ROLE", name: "navigator" })
      )
    );
    parts.push(
      C.encodeText("Agent: burn complete. Coasting.\n", { nonAscii: "v" })
    );
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({
          opcodeName: "THINK",
          payload: "delta-v within margin",
        })
      )
    );
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({ opcodeName: "TOOL", name: "ephemeris.query" })
      )
    );
    return C.concatBytes(parts);
  }

  /** Full agent-loop demo matching examples/agent-loop-demo.ascent.bin spirit. */
  function buildAgentLoop() {
    var parts = [];
    parts.push(
      C.encodeText("User: plot a course to Proxima.\n", {
        header: true,
        nonAscii: "v",
      })
    );
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({ opcodeName: "ROLE", name: "navigator" })
      )
    );
    parts.push(C.encodeText("Agent: burn complete.\n", { nonAscii: "v" }));
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({
          opcodeName: "THINK",
          payload: "delta-v within margin",
        })
      )
    );
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({ opcodeName: "TOOL", name: "ephemeris.query" })
      )
    );
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({
          opcodeName: "SAFETY",
          payload: "untrusted:telemetry-blob",
        })
      )
    );
    parts.push(
      new Uint8Array(C.encodeAgentFrame({ opcodeName: "STOP" }))
    );
    return C.concatBytes(parts);
  }

  function buildMm() {
    var parts = [];
    parts.push(C.encodeText("ASCENT/1.0\nAttach sensor still.\n", { nonAscii: "v" }));
    var hash = new Uint8Array(32);
    for (var i = 0; i < 32; i++) hash[i] = (i * 17 + 0x3c) & 0xff;
    parts.push(
      new Uint8Array(
        C.encodeMmRef("cid:sha256:aabbccddeeff00112233445566778899", {
          hashAlg: 1,
          hash: hash,
          codec: 0x0005,
        })
      )
    );
    return C.concatBytes(parts);
  }

  function buildVScalar() {
    // cafe + e acute
    return C.encodeText("caf\u00e9", { header: false, nonAscii: "v" });
  }

  function buildEmoji() {
    return C.encodeText("Hello \u{1F680}", { header: false, nonAscii: "v" });
  }

  function buildAegir() {
    var seal = C.aegirDemoSeal("Hello, Universe.\n", "lab");
    var head = C.encodeText("AEGIR sketch envelope\n", {
      header: true,
      nonAscii: "v",
    });
    return C.concatBytes([head, seal.frame]);
  }

  function buildDeep() {
    var unit = C.encodeText("Hello, Universe.\n", {
      header: true,
      nonAscii: "v",
      roleName: "probe",
    });
    if (!D) return unit;
    return D.encodeP9(unit, { profile: D.PROFILE_D });
  }

  function buildSkyPulse() {
    if (C.canonicalPathhintBytes) return C.canonicalPathhintBytes(false);
    return C.encodePathhint({
      pathId: 66,
      nextCapacityBps: 50000000,
      freezeMs: 15000,
      confidence: 0.8,
      ttlMs: 30000,
      obstruction: 0.2,
      elevDeg: 42,
      crc: false,
    });
  }

  /** Skybrary Starter Trio literacy pack seal (schema skybrary-seal/1). */
  function buildSkybrarySeal() {
    var seal = {
      schema: "skybrary-seal/1",
      pack_id: "literacy-starter",
      title: "literacy starter",
      root_sha256:
        "e84d14921dd60d160a9104cc61dcc2c10db6e0d51bee0938f2b2435e876e445b",
      pack_bytes: 255235,
      issued_utc: "2026-08-09T01:13:23Z",
      issuer: "Pitchfork-and-Torch/Skybrary",
      profile: "ASCENT-D",
      download:
        "https://skycache.jonbailey.xyz/downloads/skycache-pack-literacy-starter.zip",
      note: "Integrity seal for Skybrary starter pack. Open/PD only.",
    };
    var compact = JSON.stringify(seal);
    var unit = C.encodeText("SKYBRARY-SEAL/1\n" + compact + "\n", {
      header: true,
      nonAscii: "reject",
    });
    if (!D || !D.encodeP9) return unit;
    return D.encodeP9(unit, { profile: D.PROFILE_D || 0x44 });
  }

  function buildMixed() {
    var parts = [];
    parts.push(
      C.encodeText("Captain log: approach vector locked.\n", {
        header: true,
        nonAscii: "v",
      })
    );
    parts.push(
      new Uint8Array(C.encodeAgentFrame({ opcodeName: "ROLE", name: "pilot" }))
    );
    parts.push(
      new Uint8Array(
        C.encodeAgentFrame({
          opcodeName: "SAFETY",
          payload: "untrusted:external-telemetry",
        })
      )
    );
    var hash = new Uint8Array(32);
    for (var i = 0; i < 32; i++) hash[i] = i;
    parts.push(
      new Uint8Array(
        C.encodeMm({
          kindName: "REF",
          codec: 5,
          hashAlg: 1,
          hash: hash,
          ref: "cid:sha256:deck-camera-03",
        })
      )
    );
    parts.push(
      new Uint8Array(
        C.encodeMm({
          kindName: "INLINE",
          codec: 1,
          text: "alt=120km status=nominal",
        })
      )
    );
    return C.concatBytes(parts);
  }

  // ---------- helpers ----------

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function toHexDump(u8, bytesPerLine) {
    var n = bytesPerLine || 16;
    var lines = [];
    for (var i = 0; i < u8.length; i += n) {
      var slice = u8.slice(i, i + n);
      var hex = Array.from(slice)
        .map(function (b) {
          return b.toString(16).padStart(2, "0").toUpperCase();
        })
        .join(" ");
      var ascii = Array.from(slice)
        .map(function (b) {
          return b >= 0x20 && b < 0x7f ? String.fromCharCode(b) : ".";
        })
        .join("");
      lines.push(
        i.toString(16).padStart(4, "0").toUpperCase() +
          ":  " +
          hex.padEnd(n * 3 - 1, " ") +
          "  |" +
          ascii +
          "|"
      );
    }
    return lines.join("\n");
  }

  function classifyByte(b) {
    if (b < 0x80) return "p0";
    if (b === 0xd5 || b === 0xe5 || b === 0xc0 || b === 0xde) return "p9";
    if (b === 0x9a || b === 0x9b) return "agent";
    if (b === 0x9d || b === 0x4d) return "mm";
    if (b === 0x9c || b === 0x4b) return "crypto";
    if (b === 0xc1 || b === 0xc5) return "p2";
    if (b >= 0xa0 && b <= 0xbf) return "cont";
    if (b >= 0x80 && b <= 0x9f) return "p1";
    return "ext";
  }

  function textFromEvents(events) {
    if (!events) return "";
    var parts = [];
    for (var i = 0; i < events.length; i++) {
      var e = events[i];
      if (e.kind === "text") parts.push(e.text || e.ascii || "");
    }
    return parts.join("");
  }

  function debounce(fn, ms) {
    var t = null;
    return function () {
      var args = arguments;
      var self = this;
      clearTimeout(t);
      t = setTimeout(function () {
        fn.apply(self, args);
      }, ms);
    };
  }

  function hexToUtf8(hex) {
    if (!hex) return "";
    try {
      var u8 = C.fromHex(String(hex).replace(/\s+/g, ""));
      return new TextDecoder("utf-8").decode(u8);
    } catch (e) {
      return "";
    }
  }

  function toast(msg, kind) {
    var stack = document.getElementById("toast-stack");
    if (!stack) return;
    var el = document.createElement("div");
    el.className = "toast " + (kind || "ok");
    el.textContent = msg;
    stack.appendChild(el);
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 3200);
  }

  function unitSummary(e) {
    if (!e) return { k: "unit", v: "" };
    if (e.kind === "text") {
      var t = e.ascii != null ? e.ascii : e.text != null ? e.text : "";
      return { k: "TEXT", v: String(t).replace(/\s+/g, " ").slice(0, 42) };
    }
    if (e.kind === "agent") {
      return {
        k: "AGENT " + (e.opcodeName || ""),
        v: e.name || hexToUtf8(e.argsHex) || "",
      };
    }
    if (e.kind === "multimodal") {
      return {
        k: "MM " + (e.kindName || e.mmKind || ""),
        v: e.ref || e.text || "",
      };
    }
    if (e.kind === "pathhint") return { k: "PATHHINT", v: String(e.nextCapacityBps || e.next_capacity_bps || "") };
    if (e.kind === "crypto") return { k: "CRYPTO", v: "alg 0x" + (e.alg != null ? e.alg.toString(16) : "?") };
    return { k: String(e.kind || "unit").toUpperCase(), v: "" };
  }

  function renderMissionHud() {
    var hud = document.getElementById("mission-hud");
    var grid = document.getElementById("mission-grid");
    var titleEl = document.getElementById("mission-title");
    if (!hud || !grid) return;
    var events = state.events || [];
    var title = "";
    var role = "";
    var safety = "";
    var cam = "";
    var alt = "";
    for (var i = 0; i < events.length; i++) {
      var e = events[i];
      if (e.kind === "text") {
        var tx = e.ascii != null ? e.ascii : e.text != null ? e.text : "";
        if (/captain log|approach vector/i.test(tx)) {
          title = String(tx).replace(/^ASCENT\/1\.0\s*/i, "").replace(/\s+/g, " ").trim();
        }
      } else if (e.kind === "agent") {
        if (e.opcodeName === "ROLE") role = e.name || hexToUtf8(e.argsHex);
        if (e.opcodeName === "SAFETY") safety = e.name || hexToUtf8(e.argsHex);
      } else if (e.kind === "multimodal") {
        if (e.ref && /deck-camera|cid:/i.test(e.ref)) cam = e.ref;
        if (e.text && /alt=|status=/i.test(e.text)) alt = e.text;
      }
    }
    var on = !!(title || (role && (cam || safety)));
    hud.hidden = !on;
    hud.classList.toggle("is-on", on);
    if (!on) {
      grid.innerHTML = "";
      return;
    }
    if (titleEl) titleEl.textContent = title || "Mission stream";
    function cell(k, v, cls) {
      return (
        '<div class="mission-cell ' +
        (cls || "") +
        '"><div class="mk">' +
        escapeHtml(k) +
        '</div><div class="mv">' +
        escapeHtml(v || "n/a") +
        "</div></div>"
      );
    }
    grid.innerHTML =
      cell("ROLE", role || "none", role ? "ok" : "") +
      cell("SAFETY", safety || "none", /untrusted/i.test(safety) ? "warn" : "") +
      cell("CAMERA", cam || "none", cam ? "cam" : "") +
      cell("ALT / STATUS", alt || "none", alt ? "ok" : "");
  }

  function renderTimeline() {
    var mount = document.getElementById("stream-timeline");
    if (!mount) return;
    var events = state.events || [];
    mount.innerHTML = "";
    if (!events.length) return;
    events.forEach(function (e, idx) {
      var s = unitSummary(e);
      var b = document.createElement("button");
      b.type = "button";
      b.className = "tl-seg kind-" + (e.kind || "unknown");
      b.innerHTML =
        '<span class="tl-k">' +
        escapeHtml(s.k) +
        '</span><span class="tl-v">' +
        escapeHtml(s.v) +
        "</span>";
      b.addEventListener("click", function () {
        document.querySelectorAll(".tl-seg.active").forEach(function (n) {
          n.classList.remove("active");
        });
        b.classList.add("active");
        var cards = document.querySelectorAll("#event-stream .event-card");
        if (cards[idx]) {
          cards[idx].scrollIntoView({ behavior: "smooth", block: "nearest" });
          cards[idx].classList.add("lab-flash");
        }
      });
      mount.appendChild(b);
    });
  }

  // ---------- core setStream ----------

  function setStream(u8, opts) {
    opts = opts || {};
    state.u8 = u8 instanceof Uint8Array ? u8 : new Uint8Array(u8 || []);
    var analysis;
    try {
      analysis = C.analyzeStream(state.u8);
    } catch (e) {
      analysis = {
        total: state.u8.length,
        p0: 0,
        ext: state.u8.length,
        p0pct: 0,
        pureAscent7: false,
        parseLawOk: true,
        decodeOk: false,
        decodeError: e.message,
        planeHits: {},
        events: [],
        unitKinds: [],
      };
    }
    state.analysis = analysis;
    state.events = analysis.events || [];

    if (!opts.skipHex) {
      state.suppressHex = true;
      var hi = document.getElementById("hex-input");
      if (hi) hi.value = C.formatHexLines(state.u8, 16);
      state.suppressHex = false;
    }
    if (!opts.skipText) {
      state.suppressText = true;
      var ti = document.getElementById("text-input");
      if (ti && state.events) {
        // Only rewrite text from pure-ish text streams; keep user prose when mixed
        if (opts.forceText || !ti.value || opts.fromHex) {
          ti.value = textFromEvents(state.events);
        }
      }
      state.suppressText = false;
    }

    renderAll(opts);
    if (opts.persist !== false) persistHash();
  }

  function renderAll(opts) {
    opts = opts || {};
    renderDashboard();
    renderByteGrid();
    renderHexDump();
    renderEvents();
    renderMissionHud();
    renderTimeline();
    renderSacredFromStream();
    renderConformance();
    renderPlaneUsage();
    renderAnatomy();
    renderCodegen();
    updateStats();
    if (opts.flash) flashResults();
  }

  function updateStats() {
    var st = state.analysis;
    var statsEl = document.getElementById("wire-stats");
    var dec = document.getElementById("decode-status");
    if (!st) return;
    if (statsEl) {
      statsEl.innerHTML =
        "<span><strong>" +
        st.total +
        "</strong> bytes</span>" +
        '<span class="ok"><strong>' +
        st.p0 +
        "</strong> sacred P0 (" +
        st.p0pct.toFixed(0) +
        "%)</span>" +
        "<span><strong>" +
        st.ext +
        "</strong> extension</span>" +
        "<span><strong>" +
        (st.events ? st.events.length : 0) +
        "</strong> units</span>";
    }
    if (dec) {
      if (!st.decodeOk) {
        dec.textContent = "Decode error: " + (st.decodeError || "unknown");
        dec.className = "decode-status err";
      } else {
        var kinds = (st.unitKinds || []).join(", ") || "empty";
        dec.textContent =
          "Decoded " +
          st.total +
          " bytes · " +
          (st.events ? st.events.length : 0) +
          " unit(s): " +
          kinds;
        dec.className = "decode-status ok";
      }
    }
  }

  function renderDashboard() {
    var el = document.getElementById("lab-dashboard");
    if (!el || !state.analysis) return;
    var a = state.analysis;
    var kinds = {};
    (a.events || []).forEach(function (e) {
      kinds[e.kind] = (kinds[e.kind] || 0) + 1;
    });
    el.innerHTML =
      card(a.total, "bytes", "hot") +
      card(a.p0pct.toFixed(0) + "%", "sacred P0", a.pureAscent7 ? "hot" : "amber") +
      card(kinds.text || 0, "text units") +
      card(kinds.agent || 0, "agent") +
      card(kinds.multimodal || 0, "multimodal") +
      card(kinds.crypto || 0, "crypto") +
      card(kinds.pathhint || 0, "pathhint") +
      card(state.profile, "profile");
  }

  function card(v, label, cls) {
    return (
      '<div class="dash-card ' +
      (cls || "") +
      '"><div class="dv">' +
      escapeHtml(String(v)) +
      '</div><div class="dl">' +
      escapeHtml(label) +
      "</div></div>"
    );
  }

  function renderPlaneUsage() {
    var el = document.getElementById("plane-usage");
    if (!el || !state.analysis) return;
    var hits = state.analysis.planeHits || {};
    var ids = ["P0", "P1", "P2", "P3", "P5", "P6", "P7", "P8", "P9", "P10"];
    el.innerHTML = ids
      .map(function (id) {
        var n = hits[id] || 0;
        return (
          '<span class="plane-pill ' +
          (n ? "on" : "") +
          '">' +
          id +
          (n ? " · " + n : "") +
          "</span>"
        );
      })
      .join("");

    // Highlight architecture plane cards
    document.querySelectorAll(".plane").forEach(function (node) {
      var pid = node.getAttribute("data-plane");
      var key = pid === "P10+" ? "P10" : pid;
      node.classList.toggle("in-stream", !!(hits[key] || hits[pid]));
    });
  }

  function renderAnatomy() {
    var a = state.analysis;
    if (!a) return;
    var kinds = a.unitKinds || [];
    var hasAgent = kinds.indexOf("agent") >= 0;
    var hasMm = kinds.indexOf("multimodal") >= 0;
    var hasCrypto = kinds.indexOf("crypto") >= 0;
    var hasText = kinds.indexOf("text") >= 0;
    var hasP9 = (a.planeHits && a.planeHits.P9) > 0;
    setSeg("fixed", hasAgent || hasMm || hasCrypto);
    setSeg("len", hasAgent || hasMm || hasCrypto);
    setSeg("var", hasText || (a.ext > 0 && !hasP9));
    setSeg("outer", hasP9);
  }

  function setSeg(name, on) {
    var el = document.querySelector('.anatomy-seg[data-seg="' + name + '"]');
    if (el) el.classList.toggle("on", !!on);
  }

  function renderSacredFromStream() {
    var bar = document.getElementById("sacred-bar");
    var meter = document.getElementById("sacred-meter");
    var a = state.analysis;
    if (!a || !bar || !meter) return;
    var pct = a.total ? a.p0pct : 100;
    bar.style.width = Math.max(4, pct) + "%";
    bar.classList.toggle("warn", !a.pureAscent7 && a.total > 0);
    if (!a.total) {
      meter.textContent = "[sim] Empty stream. Sacred range awaits.";
      meter.className = "sacred-readout";
    } else if (a.pureAscent7) {
      meter.textContent =
        "[sim] ASCENT-7 identity: 100% sacred P0. Every byte is classic ASCII. Greppers smile.";
      meter.className = "sacred-readout ok";
    } else {
      meter.textContent =
        "[sim] Sacred P0 holds " +
        pct.toFixed(0) +
        "% of bytes. Extension planes present - P0 meaning unchanged.";
      meter.className = "sacred-readout warn";
    }
  }

  function renderConformance() {
    var el = document.getElementById("conf-list");
    if (!el || !state.analysis) return;
    var a = state.analysis;
    var items = [];
    items.push(row(true, "Parse law: bytes &lt; 0x80 remain classic ASCII (never remapped)"));
    items.push(
      row(
        a.pureAscent7,
        a.pureAscent7
          ? "Pure ASCENT-7: entire stream is sacred P0"
          : "Not pure ASCENT-7 (extension bytes present - expected for agent/MM)"
      )
    );
    items.push(
      row(
        a.decodeOk,
        a.decodeOk
          ? "Stream decodes under lab codec"
          : "Decode failed: " + escapeHtml(a.decodeError || "")
      )
    );
    if (state.profile === "7") {
      items.push(
        row(a.pureAscent7, "Profile ASCENT-7: non-ASCII disallowed")
      );
    }
    if (state.profile === "D") {
      var hasP9 = a.planeHits && a.planeHits.P9 > 0;
      items.push(
        row(hasP9, hasP9 ? "Profile ASCENT-D: outer sync present" : "Profile ASCENT-D: no P9 outer frame yet (use simulator)")
      );
    }
    var hasAgent = (a.unitKinds || []).indexOf("agent") >= 0;
    items.push(
      row(null, hasAgent ? "Contains agent frame(s)" : "No agent frames", hasAgent ? "pass" : "warn")
    );
    el.innerHTML = items.join("");
  }

  function row(pass, html, forceClass) {
    var cls =
      forceClass ||
      (pass === true ? "pass" : pass === false ? "fail" : "warn");
    return '<li class="' + cls + '">' + html + "</li>";
  }

  function renderByteGrid() {
    var mount = document.getElementById("byte-grid");
    if (!mount) return;
    mount.innerHTML = "";
    var u8 = state.u8;
    var events = state.events || [];
    var ranges = [];
    for (var ei = 0; ei < events.length; ei++) {
      var e = events[ei];
      if (e.offset != null && e.end != null) {
        ranges.push({ start: e.offset, end: e.end, kind: e.kind, ev: e });
      }
    }
    function eventAt(i) {
      for (var r = 0; r < ranges.length; r++) {
        if (i >= ranges[r].start && i < ranges[r].end) return ranges[r];
      }
      return null;
    }
    var limit = Math.min(u8.length, 2048);
    for (var i = 0; i < limit; i++) {
      var b = u8[i];
      var el = document.createElement("button");
      el.type = "button";
      el.className = "byte-cell " + classifyByte(b);
      var er = eventAt(i);
      if (er) el.classList.add("ev-" + er.kind);
      el.textContent = b.toString(16).padStart(2, "0").toUpperCase();
      el.title = "offset " + i + " = 0x" + b.toString(16).padStart(2, "0");
      (function (byte, off, cell, range) {
        cell.addEventListener("click", function () {
          document.querySelectorAll(".byte-cell.active").forEach(function (n) {
            n.classList.remove("active");
          });
          cell.classList.add("active");
          var panel = document.getElementById("byte-inspect");
          if (!panel) return;
          var ch =
            byte >= 0x20 && byte < 0x7f
              ? JSON.stringify(String.fromCharCode(byte))
              : byte === 0x0a
                ? "LF"
                : byte === 0x0d
                  ? "CR"
                  : "non-print";
          var extra = "";
          if (range && range.ev) {
            extra =
              " · unit <code>" +
              escapeHtml(range.ev.kind) +
              (range.ev.opcodeName ? "/" + escapeHtml(range.ev.opcodeName) : "") +
              (range.ev.kindName ? "/" + escapeHtml(range.ev.kindName) : "") +
              "</code> [" +
              range.start +
              ".." +
              range.end +
              ")";
          }
          panel.innerHTML =
            "<strong>0x" +
            byte.toString(16).padStart(2, "0").toUpperCase() +
            "</strong> @ " +
            off +
            " · class <code>" +
            classifyByte(byte) +
            "</code> · " +
            ch +
            (byte < 0x80
              ? ' · <span class="ok">SACRED P0</span>'
              : " · extension") +
            extra;
        });
      })(b, i, el, er);
      mount.appendChild(el);
    }
    if (u8.length > limit) {
      var more = document.createElement("div");
      more.className = "form-hint";
      more.textContent = "Showing first " + limit + " of " + u8.length + " bytes.";
      mount.appendChild(more);
    }
  }

  function renderHexDump() {
    var el = document.getElementById("hex-dump");
    if (el) el.textContent = state.u8.length ? toHexDump(state.u8) : "";
  }

  function renderEvents() {
    var mount = document.getElementById("event-stream");
    if (!mount) return;
    mount.innerHTML = "";
    var events = state.events || [];
    if (!events.length) {
      mount.innerHTML = '<p class="form-hint">No units decoded.</p>';
      return;
    }
    for (var i = 0; i < events.length; i++) {
      var e = events[i];
      var card = document.createElement("div");
      var type = typeof e.kind === "string" ? e.kind : "unknown";
      card.className = "event-card kind-" + type;
      if (type === "text") {
        var t = e.ascii != null ? e.ascii : e.text != null ? e.text : "";
        card.innerHTML =
          '<div class="ev-label">TEXT · P0/V</div><pre>' +
          escapeHtml(t) +
          "</pre>";
      } else if (type === "agent") {
        var agentBody = e.name || hexToUtf8(e.argsHex) || "";
        var untrusted = /untrusted/i.test(agentBody);
        card.innerHTML =
          '<div class="ev-label">AGENT · ' +
          escapeHtml(e.opcodeName || "") +
          (untrusted ? '<span class="ev-badge warn">untrusted</span>' : "") +
          "</div><p>payload: <code>" +
          escapeHtml(agentBody) +
          "</code> · flags " +
          e.flags +
          " · ver " +
          e.ver +
          " · args " +
          (e.argsWireLen || 0) +
          " B</p>";
      } else if (type === "multimodal") {
        var bodyBits = "";
        if (e.ref) bodyBits = "ref: <code>" + escapeHtml(e.ref) + "</code>";
        else if (e.text) bodyBits = "text: <code>" + escapeHtml(e.text) + "</code>";
        else if (e.bodyHex) bodyBits = "body: <code>" + escapeHtml(e.bodyHex) + "</code>";
        card.innerHTML =
          '<div class="ev-label">MULTIMODAL · ' +
          escapeHtml(e.kindName || "") +
          "</div><p>codec " +
          e.codec +
          " · " +
          escapeHtml(e.hashAlg || "") +
          '</p><p class="mono-sm">' +
          escapeHtml(e.hashHex || "") +
          "</p><p>" +
          bodyBits +
          "</p>";
      } else if (type === "pathhint") {
        var applied = e.applied ? "APPLIED" : "SKIP " + (e.reason || "");
        var cap = e.nextCapacityBps != null ? e.nextCapacityBps : e.next_capacity_bps;
        var freeze = e.freezeMs != null ? e.freezeMs : e.freeze_ms;
        var obst = e.obstruction == null ? "na" : Number(e.obstruction).toFixed(2);
        var el = e.elevDeg != null ? e.elevDeg : e.elev_deg;
        card.innerHTML =
          '<div class="ev-label">PATHHINT · ' +
          escapeHtml(applied) +
          "</div><p>path_id <code>" +
          escapeHtml(String(e.pathId != null ? e.pathId : e.path_id)) +
          "</code> · bottleneck_hint " +
          escapeHtml(String(cap)) +
          " bps · freeze_until " +
          escapeHtml(String(freeze)) +
          " ms · conf " +
          escapeHtml(String(e.confidence)) +
          "</p><p>obst " +
          escapeHtml(String(obst)) +
          " · el " +
          escapeHtml(String(el == null ? "na" : el)) +
          " deg · ttl " +
          escapeHtml(String(e.ttlMs != null ? e.ttlMs : e.ttl_ms)) +
          " ms</p><p class=\"form-hint\">Goodput/CCA hint (sim). Predicted sender bottleneck, not a Starlink RF Mbps claim.</p>";
      } else if (type === "crypto") {
        card.innerHTML =
          '<div class="ev-label">CRYPTO · alg 0x' +
          (e.alg != null ? e.alg.toString(16) : "?") +
          "</div><p>kid <code>" +
          escapeHtml(e.kidHex || "") +
          "</code> · nonce <code>" +
          escapeHtml(e.nonceHex || "") +
          "</code> · ct " +
          e.ctLen +
          " B</p>";
      } else {
        card.innerHTML =
          '<div class="ev-label">' +
          escapeHtml(String(type).toUpperCase()) +
          "</div><pre>" +
          escapeHtml(JSON.stringify(e, null, 2)) +
          "</pre>";
      }
      mount.appendChild(card);
    }
  }

  function flashResults() {
    ["lab-results", "lab-units", "lab"].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.classList.remove("lab-flash");
      void el.offsetWidth;
      el.classList.add("lab-flash");
    });
  }

  // ---------- encode / decode from editors ----------

  function readEncodeOpts() {
    var nonEl = document.getElementById("opt-nonascii");
    var nonAscii = nonEl && nonEl.value ? nonEl.value : "v";
    if (state.profile === "7") nonAscii = "reject";
    return {
      header: !!(document.getElementById("opt-header") || {}).checked,
      roleName: (document.getElementById("opt-role") || {}).checked
        ? ((document.getElementById("opt-role-name") || {}).value || "guide").trim()
        : "",
      nonAscii: nonAscii,
    };
  }

  function encodeFromText(andFlash) {
    var textEl = document.getElementById("text-input");
    var text = textEl ? textEl.value : "";
    var status = document.getElementById("encode-status");
    try {
      if (state.profile === "7") {
        for (var i = 0; i < text.length; ) {
          var cp = text.codePointAt(i);
          if (cp > 0x7f) throw new Error("ASCENT-7 rejects non-ASCII");
          i += cp > 0xffff ? 2 : 1;
        }
      }
      var opts = readEncodeOpts();
      var encOpts = { header: opts.header, nonAscii: opts.nonAscii };
      if (opts.roleName) encOpts.roleName = opts.roleName;
      var bytes = C.encodeText(text, encOpts);
      setStream(bytes, { skipText: true, flash: andFlash, persist: true });
      if (status) {
        status.textContent =
          "Encoded " +
          bytes.length +
          " B · mode=" +
          opts.nonAscii +
          " · profile " +
          state.profile +
          ". Pure ASCII stays bit-identical P0.";
        status.className = "decode-status ok";
      }
    } catch (e) {
      if (status) {
        status.textContent = "Encode error: " + e.message;
        status.className = "decode-status err";
      }
    }
  }

  function decodeFromHex(opts) {
    opts = opts || {};
    var raw = (document.getElementById("hex-input") || {}).value || "";
    var status = document.getElementById("decode-status");
    try {
      if (!String(raw).replace(/\s+/g, "")) {
        if (status) {
          status.textContent = "Hex input is empty.";
          status.className = "decode-status err";
        }
        return;
      }
      var u8 = C.fromHex(raw);
      setStream(u8, {
        skipHex: true,
        fromHex: true,
        forceText: opts.forceText !== false,
        flash: opts.flash,
        persist: true,
      });
    } catch (e) {
      if (status) {
        status.textContent = "Decode error: " + e.message;
        status.className = "decode-status err";
      }
    }
  }

  // ---------- composers ----------

  function insertBytes(arr, mode) {
    var piece = arr instanceof Uint8Array ? arr : new Uint8Array(arr);
    var next;
    if (mode === "replace") next = piece;
    else next = C.concatBytes([state.u8, piece]);
    setStream(next, { forceText: true, flash: true });
  }

  function wireAgentComposer() {
    var insert = document.getElementById("btn-agent-insert");
    var replace = document.getElementById("btn-agent-replace");
    function build() {
      var op = (document.getElementById("agent-opcode") || {}).value || "ROLE";
      var name = (document.getElementById("agent-name") || {}).value || "";
      var flags = parseInt((document.getElementById("agent-flags") || {}).value, 10) || 0;
      var opts = { opcodeName: op, flags: flags };
      if (op === "ROLE" || op === "TOOL" || op === "HANDOFF") opts.name = name || "agent";
      else if (op === "STOP") opts.args = [];
      else opts.payload = name;
      return new Uint8Array(C.encodeAgentFrame(opts));
    }
    if (insert)
      insert.addEventListener("click", function () {
        insertBytes(build(), "append");
      });
    if (replace)
      replace.addEventListener("click", function () {
        insertBytes(build(), "replace");
      });
  }

  function wireMmComposer() {
    var insert = document.getElementById("btn-mm-insert");
    var replace = document.getElementById("btn-mm-replace");
    function build() {
      var kind = (document.getElementById("mm-kind") || {}).value || "INLINE";
      var body = (document.getElementById("mm-body") || {}).value || "";
      var codec = parseInt((document.getElementById("mm-codec") || {}).value, 10);
      if (isNaN(codec)) codec = 1;
      if (kind === "REF") {
        var hash = new Uint8Array(32);
        for (var i = 0; i < 32; i++) hash[i] = (body.charCodeAt(i % Math.max(body.length, 1)) || i) & 0xff;
        return new Uint8Array(
          C.encodeMmRef(body, { codec: codec, hashAlg: 1, hash: hash })
        );
      }
      if (kind === "CHUNK") {
        return new Uint8Array(
          C.encodeMm({ kindName: "CHUNK", codec: codec, text: body })
        );
      }
      return new Uint8Array(
        C.encodeMm({ kindName: "INLINE", codec: codec, text: body })
      );
    }
    if (insert)
      insert.addEventListener("click", function () {
        insertBytes(build(), "append");
      });
    if (replace)
      replace.addEventListener("click", function () {
        insertBytes(build(), "replace");
      });
  }

  function wireAegir() {
    var reg = document.getElementById("aegir-registry");
    if (reg && C.AEGIR_ALG) {
      var names = Object.keys(C.AEGIR_ALG)
        .map(function (k) {
          return "0x" + Number(k).toString(16) + " " + C.AEGIR_ALG[k];
        })
        .join(" · ");
      reg.textContent = "Registry: " + names;
    }
    var btn = document.getElementById("btn-aegir-seal");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var pt = (document.getElementById("aegir-pt") || {}).value || "";
      var pass = (document.getElementById("aegir-pass") || {}).value || "lab";
      var seal = C.aegirDemoSeal(pt, pass);
      insertBytes(seal.frame, "append");
      var st = document.getElementById("aegir-status");
      if (st) {
        st.textContent =
          "Sealed with " +
          seal.algName +
          " · frame " +
          seal.frame.length +
          " B. " +
          seal.note;
        st.className = "status-line ok";
      }
    });
  }

  // ---------- ASCENT-D sim ----------

  function wireDsim() {
    if (!D) return;
    var wrapBtn = document.getElementById("btn-dsim-wrap");
    var noiseBtn = document.getElementById("btn-dsim-noise");
    var decBtn = document.getElementById("btn-dsim-decode");

    function showTx(u8) {
      state.dsim.tx = u8;
      var dump = document.getElementById("dsim-tx-dump");
      if (dump) dump.textContent = toHexDump(u8);
      var box = document.getElementById("dsim-tx");
      if (box) box.className = "dsim-box ok";
    }

    function showRx(result, noisy) {
      state.dsim.rx = result;
      var dump = document.getElementById("dsim-rx-dump");
      var box = document.getElementById("dsim-rx");
      var st = document.getElementById("dsim-status");
      if (!dump || !box) return;
      if (result.status === "ok" || result.status === "recovered") {
        var desc = D.describeFrame(result.frame);
        dump.textContent =
          "status: " +
          result.status.toUpperCase() +
          "\n" +
          "profile: " +
          desc.profile +
          "\n" +
          "unit: " +
          desc.unitLen +
          " B · frame: " +
          desc.totalLen +
          " B\n" +
          "family: " +
          desc.family +
          " (params n=" +
          desc.n +
          " k=" +
          desc.k +
          ")\n" +
          "unit preview: " +
          C.hexOf(result.frame.unit).slice(0, 48) +
          (result.frame.unit.length > 24 ? "..." : "");
        box.className =
          "dsim-box " + (result.status === "recovered" ? "recovered" : "ok");
        if (st) {
          st.textContent =
            result.status === "recovered"
              ? "RECOVERED: clear unit differed; parity restored authoritative unit. No mojibake."
              : "OK: outer frame verified. Unit intact.";
          st.className =
            "status-line " + (result.status === "recovered" ? "warn" : "ok");
        }
        if (result.frame && result.frame.unit) {
          // Optionally load recovered unit into main lab
        }
      } else {
        dump.textContent =
          "status: " +
          String(result.status).toUpperCase() +
          "\n" +
          "ERASE-ON-FAIL\n" +
          "Unit discarded. No best-effort mojibake.\n" +
          (noisy ? "Noise defeated recovery." : "");
        box.className = "dsim-box erased";
        if (st) {
          st.textContent =
            "ERASED: parity/CRC failed. Stream unit wiped - deep-space honesty.";
          st.className = "status-line err";
        }
      }
    }

    if (wrapBtn) {
      wrapBtn.addEventListener("click", function () {
        try {
          var unit = state.u8;
          if (!unit.length) unit = C.encodeText("Hello, Universe.\n", { header: true });
          // If already has P9 sync, re-wrap inner text only
          var frame = D.encodeP9(unit, { profile: D.PROFILE_D });
          showTx(frame);
          state.dsim.flips = [];
          document.getElementById("dsim-flip-count").textContent = "0 flips";
          document.getElementById("noise-fill").style.width = "0%";
          var dec = D.decodeP9(frame);
          showRx(dec, false);
          setStream(frame, { forceText: true, flash: true });
          var st = document.getElementById("dsim-status");
          if (st) {
            st.textContent =
              "Wrapped " +
              unit.length +
              " B unit into " +
              frame.length +
              " B P9 frame. " +
              D.note;
            st.className = "status-line ok";
          }
        } catch (e) {
          var s = document.getElementById("dsim-status");
          if (s) {
            s.textContent = "Wrap error: " + e.message;
            s.className = "status-line err";
          }
        }
      });
    }

    if (noiseBtn) {
      noiseBtn.addEventListener("click", function () {
        try {
          var base = state.dsim.tx || state.u8;
          if (!base || !base.length) {
            throw new Error("Wrap a stream first");
          }
          var n = parseInt((document.getElementById("dsim-errors") || {}).value, 10) || 0;
          var target = (document.getElementById("dsim-target") || {}).value || "unit";
          var minOff = 0;
          var maxOff = base.length - 1;
          // Rough regions: header ~14 bytes, then unit, then parity
          if (target === "unit" && base.length > 20) {
            minOff = 14;
            var len = (base[10] << 24) | (base[11] << 16) | (base[12] << 8) | base[13];
            maxOff = Math.min(base.length - 1, 14 + Math.max(len - 1, 0));
          } else if (target === "parity" && base.length > 40) {
            minOff = Math.floor(base.length * 0.55);
            maxOff = base.length - 1;
          }
          var inj = D.injectBitErrors(base, n, { minOffset: minOff, maxOffset: maxOff });
          state.dsim.flips = inj.flips;
          document.getElementById("dsim-flip-count").textContent =
            inj.flips.length + " flips";
          var fill = document.getElementById("noise-fill");
          if (fill) fill.style.width = Math.min(100, inj.flips.length * 8) + "%";
          showTx(base);
          var dec = D.decodeP9(inj.bytes);
          showRx(dec, true);
          // Keep noisy frame in lab for inspection
          setStream(inj.bytes, { forceText: false, flash: true });
        } catch (e) {
          var s = document.getElementById("dsim-status");
          if (s) {
            s.textContent = "Noise error: " + e.message;
            s.className = "status-line err";
          }
        }
      });
    }

    if (decBtn) {
      decBtn.addEventListener("click", function () {
        var dec = D.decodeP9(state.u8);
        showRx(dec, false);
        if (dec.frame && dec.frame.unit && (dec.status === "ok" || dec.status === "recovered")) {
          setStream(dec.frame.unit, { forceText: true, flash: true });
        }
      });
    }
  }

  // ---------- architecture ----------

  function wireArchitecture() {
    var grid = document.getElementById("plane-grid");
    if (!grid) return;
    grid.innerHTML = "";
    PLANES.forEach(function (p) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "plane";
      btn.setAttribute("data-plane", p.id);
      btn.innerHTML =
        '<div class="pid">' +
        escapeHtml(p.id) +
        '</div><div class="pname">' +
        escapeHtml(p.name) +
        '</div><div class="prole">' +
        escapeHtml(p.role) +
        "</div>";
      btn.addEventListener("click", function () {
        state.selectedPlane = p;
        document.querySelectorAll(".plane").forEach(function (n) {
          n.classList.remove("active");
        });
        btn.classList.add("active");
        var det = document.getElementById("plane-detail");
        var title = document.getElementById("plane-detail-title");
        var body = document.getElementById("plane-detail-body");
        if (det) det.classList.add("open");
        if (title) title.textContent = p.id + " · " + p.name;
        if (body) body.textContent = p.detail;
      });
      grid.appendChild(btn);
    });
    var load = document.getElementById("plane-load-example");
    if (load) {
      load.addEventListener("click", function () {
        if (!state.selectedPlane) return;
        loadGallery(state.selectedPlane.example);
        document.getElementById("lab").scrollIntoView({ behavior: "smooth" });
      });
    }
  }

  // ---------- gallery / tour / spec ----------

  function loadGallery(id) {
    var g = null;
    for (var i = 0; i < GALLERY.length; i++) {
      if (GALLERY[i].id === id) {
        g = GALLERY[i];
        break;
      }
    }
    if (!g) return;
    try {
      var u8 = g.build();
      setStream(u8, { forceText: true, flash: true });
      document.querySelectorAll("#gallery-chips .chip").forEach(function (c) {
        c.classList.toggle("active", c.getAttribute("data-id") === id);
      });
    } catch (e) {
      console.error(e);
      alert("Sample error: " + e.message);
    }
  }

  function wireGallery() {
    var row = document.getElementById("gallery-chips");
    if (!row) return;
    GALLERY.forEach(function (g) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.setAttribute("data-id", g.id);
      b.textContent = g.label;
      b.addEventListener("click", function () {
        loadGallery(g.id);
      });
      row.appendChild(b);
    });
  }

  function renderTour() {
    var steps = document.getElementById("tour-steps");
    var body = document.getElementById("tour-body");
    if (!steps || !body) return;
    steps.innerHTML = "";
    TOUR.forEach(function (t, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className =
        "tour-step" +
        (i === state.tourStep ? " active" : "") +
        (i < state.tourStep ? " done" : "");
      b.textContent = t.title;
      b.addEventListener("click", function () {
        state.tourStep = i;
        renderTour();
      });
      steps.appendChild(b);
    });
    var cur = TOUR[state.tourStep];
    body.innerHTML = cur
      ? "<strong>" + cur.title + "</strong> - " + cur.body
      : "";
  }

  function wireTour() {
    renderTour();
    var next = document.getElementById("tour-next");
    var run = document.getElementById("tour-run");
    var reset = document.getElementById("tour-reset");
    var start = document.getElementById("btn-start-tour");
    if (next) {
      next.addEventListener("click", function () {
        state.tourStep = Math.min(TOUR.length - 1, state.tourStep + 1);
        renderTour();
        var cur = TOUR[state.tourStep];
        if (cur) loadGallery(cur.sample);
      });
    }
    if (run) {
      run.addEventListener("click", function () {
        var cur = TOUR[state.tourStep];
        if (cur) {
          loadGallery(cur.sample);
          document.getElementById("lab").scrollIntoView({ behavior: "smooth" });
        }
      });
    }
    if (reset) {
      reset.addEventListener("click", function () {
        state.tourStep = 0;
        renderTour();
        loadGallery(TOUR[0].sample);
      });
    }
    if (start) {
      start.addEventListener("click", function () {
        state.tourStep = 0;
        renderTour();
        loadGallery(TOUR[0].sample);
        document.getElementById("tour").scrollIntoView({ behavior: "smooth" });
      });
    }
  }

  function wireSpec() {
    var toc = document.getElementById("spec-toc");
    var panel = document.getElementById("spec-panel");
    var tryBtn = document.getElementById("spec-try");
    var active = 0;
    function show(i) {
      active = i;
      var s = SPEC_SECTIONS[i];
      if (panel) panel.innerHTML = s.html;
      if (toc) {
        toc.querySelectorAll(".chip").forEach(function (c, idx) {
          c.classList.toggle("active", idx === i);
        });
      }
    }
    if (toc) {
      SPEC_SECTIONS.forEach(function (s, i) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "chip" + (i === 0 ? " active" : "");
        b.textContent = s.label;
        b.addEventListener("click", function () {
          show(i);
        });
        toc.appendChild(b);
      });
    }
    show(0);
    if (tryBtn) {
      tryBtn.addEventListener("click", function () {
        loadGallery(SPEC_SECTIONS[active].sample);
        document.getElementById("lab").scrollIntoView({ behavior: "smooth" });
      });
    }
  }

  // ---------- codegen ----------

  function renderCodegen() {
    var out = document.getElementById("codegen-out");
    if (!out) return;
    var hex = C.hexOf(state.u8).toUpperCase();
    var shortHex = hex.length > 96 ? hex.slice(0, 96) + "..." : hex;
    var textPreview = textFromEvents(state.events).slice(0, 80);
    var lang = state.codegenLang;
    var code = "";
    if (lang === "python") {
      code =
        "# ASCENT lab snippet - matches current stream (" +
        state.u8.length +
        " B)\n" +
        "# pip: use repo ref/ascent_codec.py\n" +
        "from ascent_codec import encode_text, decode_stream\n" +
        "from pathlib import Path\n\n" +
        "text = " +
        JSON.stringify(textPreview || "Hello, Universe.\\n") +
        "\n" +
        "wire = encode_text(text, header=True, non_ascii='v')\n" +
        "print(wire.hex())\n" +
        "for ev in decode_stream(wire):\n" +
        "    print(ev['kind'], ev)\n\n" +
        "# Current lab hex (truncated):\n# " +
        shortHex +
        "\n";
    } else if (lang === "javascript") {
      code =
        "// Browser / Node lab (AscentCodec from ascent_codec.js)\n" +
        "const text = " +
        JSON.stringify(textPreview || "Hello, Universe.\\n") +
        ";\n" +
        "const wire = AscentCodec.encodeText(text, { header: true, nonAscii: 'v' });\n" +
        "console.log(AscentCodec.hexOf(wire));\n" +
        "console.log(AscentCodec.decodeStream(wire));\n\n" +
        "// Current stream hex (truncated):\n// " +
        shortHex +
        "\n";
    } else if (lang === "rust") {
      code =
        "// Sketch - keep P0 identity; real crate would mirror ref/ascent_codec.py\n" +
        "fn is_sacred(b: u8) -> bool { b < 0x80 }\n\n" +
        "fn encode_ascent7(s: &str) -> Result<Vec<u8>, &'static str> {\n" +
        "    let mut out = Vec::with_capacity(s.len());\n" +
        "    for b in s.bytes() {\n" +
        "        if !is_sacred(b) { return Err(\"non-ASCII\"); }\n" +
        "        out.push(b); // bit-identical\n" +
        "    }\n" +
        "    Ok(out)\n" +
        "}\n\n" +
        "// Lab stream length: " +
        state.u8.length +
        " bytes\n";
    } else {
      code =
        "// How to use ASCENT inside an LLM agent loop\n" +
        "1. Emit prose as ASCENT-7 when possible (pure ASCII).\n" +
        "2. Fence control with agent frames:\n" +
        "   ROLE / TOOL / THINK / HANDOFF / CAP / SAFETY / STOP\n" +
        "3. Keep THINK opaque on shared logs.\n" +
        "4. Wrap untrusted tool output in SAFETY (data, not silent control).\n" +
        "5. Attach media as MM REF (content-addressed) not raw megabytes.\n" +
        "6. On deep-space or hostile links, outer ASCENT-D: erase-on-fail.\n\n" +
        "Example ROLE=guide wire:\n" +
        "9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B\n";
    }
    out.textContent = code;
  }

  function wireCodegen() {
    document.querySelectorAll("#codegen-tabs .chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        state.codegenLang = chip.getAttribute("data-lang");
        document.querySelectorAll("#codegen-tabs .chip").forEach(function (c) {
          c.classList.remove("active");
        });
        chip.classList.add("active");
        renderCodegen();
      });
    });
    var copy = document.getElementById("btn-copy-code");
    if (copy) {
      copy.addEventListener("click", async function () {
        var out = document.getElementById("codegen-out");
        if (!out) return;
        await navigator.clipboard.writeText(out.textContent);
        toast("Snippet copied", "ok");
      });
    }
  }

  // ---------- export / share ----------

  function persistHash() {
    try {
      if (!state.u8.length || state.u8.length > 4000) return;
      var h = "#h=" + C.hexOf(state.u8);
      if (history.replaceState) {
        history.replaceState(null, "", h);
      }
    } catch (e) {
      /* ignore */
    }
  }

  function loadFromHash() {
    var m = /[#&]h=([0-9a-fA-F]+)/.exec(location.hash || "");
    if (m) {
      try {
        setStream(C.fromHex(m[1]), { forceText: true, persist: false });
        return true;
      } catch (e) {
        console.warn("hash load failed", e);
      }
    }
    return false;
  }

  function wireExport() {
    var copy = document.getElementById("btn-copy-hex");
    if (copy) {
      copy.addEventListener("click", async function () {
        await navigator.clipboard.writeText(C.hexOf(state.u8));
        toast("Hex copied", "ok");
      });
    }
    var dl = document.getElementById("btn-download");
    if (dl) {
      dl.addEventListener("click", function () {
        var blob = new Blob([state.u8], { type: "application/octet-stream" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "stream.ascent.bin";
        a.click();
        URL.revokeObjectURL(a.href);
      });
    }
    var share = document.getElementById("btn-share");
    if (share) {
      share.addEventListener("click", async function () {
        persistHash();
        var url = location.href.split("#")[0] + "#h=" + C.hexOf(state.u8);
        try {
          await navigator.clipboard.writeText(url);
          toast("Share URL copied", "ok");
        } catch (e) {
          prompt("Copy share URL:", url);
        }
      });
    }
    var jsonBtn = document.getElementById("btn-json");
    if (jsonBtn) {
      jsonBtn.addEventListener("click", async function () {
        var payload = JSON.stringify(state.events || [], null, 2);
        await navigator.clipboard.writeText(payload);
        toast("JSON units copied", "ok");
      });
    }
  }

  // ---------- profile / sacred input / meta ----------

  function wireProfile() {
    var sel = document.getElementById("profile-select");
    if (!sel) return;
    sel.addEventListener("change", function () {
      state.profile = sel.value;
      var non = document.getElementById("opt-nonascii");
      if (state.profile === "7" && non) non.value = "reject";
      if (state.profile === "E" || state.profile === "E-LEO") {
        if (non && non.value === "reject") non.value = "v";
      }
      if (state.profile === "E-LEO") {
        var skySel = document.getElementById("sky-profile");
        if (skySel) skySel.value = "ASCENT-E-LEO";
      }
      if (state.profile === "D") {
        var skySelD = document.getElementById("sky-profile");
        if (skySelD) skySelD.value = "ASCENT-D";
      }
      renderAll({ flash: false });
      var st = document.getElementById("encode-status");
      if (st) {
        st.textContent = "Profile set to ASCENT-" + state.profile + ".";
        st.className = "decode-status ok";
      }
    });
  }

  function wireSacredInput() {
    var input = document.getElementById("sacred-input");
    var meter = document.getElementById("sacred-input-meter");
    if (!input || !meter) return;
    var paint = function () {
      var pure = true;
      for (var i = 0; i < input.value.length; ) {
        var cp = input.value.codePointAt(i);
        if (cp > 127) {
          pure = false;
          break;
        }
        i += cp > 0xffff ? 2 : 1;
      }
      meter.textContent = pure
        ? "[sim] ASCENT-7: every character is classic ASCII."
        : "[sim] Contains codepoints above 127 - extension planes on the wire.";
      meter.className = "sacred-readout " + (pure ? "ok" : "warn");
    };
    input.addEventListener("input", paint);
    paint();
  }

  function wireMeta() {
    var m = document.getElementById("btn-encode-manifesto");
    var t = document.getElementById("btn-encode-page-title");
    var st = document.getElementById("meta-status");
    if (m) {
      m.addEventListener("click", function () {
        var text =
          "Keep every classic ASCII byte sacred.\n" +
          "Everything else ascends without burning the stairs.\n" +
          "ASCENT Nexus Wire Lab 3.0 Crystal Wire\n";
        var bytes = C.encodeText(text, {
          header: true,
          nonAscii: "v",
          roleName: "manifesto",
        });
        setStream(bytes, { forceText: true, flash: true });
        if (st) {
          st.textContent = "Manifesto encoded: " + bytes.length + " bytes.";
          st.className = "status-line ok";
        }
        document.getElementById("lab").scrollIntoView({ behavior: "smooth" });
      });
    }
    if (t) {
      t.addEventListener("click", function () {
        var bytes = C.encodeText("ASCENT Nexus - Wire Lab 3.0 Crystal Wire\n", {
          header: true,
          nonAscii: "reject",
        });
        setStream(bytes, { forceText: true, flash: true });
        if (st) {
          st.textContent = "Title encoded as pure ASCENT-7.";
          st.className = "status-line ok";
        }
      });
    }
  }

  // ---------- hero canvas ----------

  function initCanvas() {
    var c = document.getElementById("hero-canvas");
    if (!c) return;
    var ctx = c.getContext("2d");
    var w, h, dpr;
    var glyphs = [];
    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = c.clientWidth;
      h = c.clientHeight;
      c.width = Math.floor(w * dpr);
      c.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);
    for (var i = 0; i < 70; i++) {
      glyphs.push({
        x: Math.random() * 1000,
        y: Math.random() * 600,
        v: 0.15 + Math.random() * 0.7,
        b: Math.floor(Math.random() * 128),
        a: 0.12 + Math.random() * 0.4,
      });
    }
    var t = 0;
    function frame() {
      t += 0.01;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = "rgba(61,214,255,0.035)";
      for (var x = 0; x < w; x += 48) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      ctx.font = "11px ui-monospace, Cascadia Code, monospace";
      for (var gi = 0; gi < glyphs.length; gi++) {
        var g = glyphs[gi];
        g.y += g.v;
        if (g.y > h + 20) {
          g.y = -20;
          g.x = Math.random() * w;
          g.b = Math.floor(Math.random() * 128);
        }
        ctx.fillStyle = "rgba(0,229,192," + g.a + ")";
        ctx.fillText(
          g.b.toString(16).padStart(2, "0").toUpperCase(),
          g.x % w,
          g.y
        );
      }
      var gy = h * 0.62 + Math.sin(t) * 3;
      var grad = ctx.createLinearGradient(0, gy, w, gy);
      grad.addColorStop(0, "rgba(0,229,192,0)");
      grad.addColorStop(0.5, "rgba(61,214,255,0.28)");
      grad.addColorStop(1, "rgba(240,180,41,0)");
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(0, gy);
      ctx.lineTo(w, gy);
      ctx.stroke();
      requestAnimationFrame(frame);
    }
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      requestAnimationFrame(frame);
    }
  }

  function wireSkyPulse() {
    function readOpts() {
      var obstEl = document.getElementById("sky-obst");
      var elevEl = document.getElementById("sky-elev");
      var obstRaw = obstEl ? obstEl.value : "";
      var elevRaw = elevEl ? elevEl.value : "";
      return {
        pathId: parseInt((document.getElementById("sky-path-id") || {}).value, 10) || 0,
        nextCapacityBps: parseInt((document.getElementById("sky-cap") || {}).value, 10) || 0,
        freezeMs: parseInt((document.getElementById("sky-freeze") || {}).value, 10) || 0,
        confidence: parseFloat((document.getElementById("sky-conf") || {}).value) || 0,
        ttlMs: parseInt((document.getElementById("sky-ttl") || {}).value, 10) || 0,
        obstruction: obstRaw === "" ? null : parseFloat(obstRaw),
        elevDeg: elevRaw === "" ? null : parseFloat(elevRaw),
      };
    }
    function encodeCurrent() {
      var profile = (document.getElementById("sky-profile") || {}).value || "ASCENT-E-LEO";
      var pol = C.recommendIntegrity ? C.recommendIntegrity(profile) : { wrapP9: false, usePathhintCrc: false, note: "" };
      var opts = readOpts();
      opts.crc = !!pol.usePathhintCrc;
      var unit = C.encodePathhint(opts);
      if (pol.wrapP9 && D && D.encodeP9) {
        unit = D.encodeP9(unit, { profile: D.PROFILE_D });
      }
      return { unit: unit, pol: pol, profile: profile };
    }
    function showFields(unit, pol) {
      var pre = document.getElementById("sky-fields");
      var st = document.getElementById("sky-status");
      var inner = unit;
      var p9note = "";
      if (D && D.decodeP9 && unit.length >= 4 && unit[0] === 0xd5) {
        var dec = D.decodeP9(unit);
        if (dec && dec.status === "ok" && dec.frame) {
          inner = dec.frame.unit;
          p9note = "P9 wrap ok. Inner PATHHINT below.\n";
        }
      }
      var ev = C.decodeStream(inner);
      var hint = null;
      for (var i = 0; i < ev.length; i++) {
        if (ev[i].kind === "pathhint") hint = ev[i];
      }
      if (pre) {
        pre.textContent =
          p9note +
          (pol && pol.note ? pol.note + "\n\n" : "") +
          (hint ? JSON.stringify(hint, null, 2) : "no PATHHINT decoded") +
          "\n\nhex " +
          C.hexOf(unit).toUpperCase();
      }
      if (st) {
        st.textContent = hint && hint.applied
          ? "PATHHINT applied (sim). bottleneck_hint is predicted sender bottleneck, not RF Mbps. profile " + (pol && pol.profile)
          : "PATHHINT skipped (" + ((hint && hint.reason) || "none") + "). Fail-closed.";
        st.className = "status-line " + (hint && hint.applied ? "ok" : "warn");
      }
    }
    var enc = document.getElementById("btn-sky-encode");
    if (enc) {
      enc.addEventListener("click", function () {
        try {
          var r = encodeCurrent();
          setStream(r.unit, { forceText: true, flash: true });
          showFields(r.unit, r.pol);
        } catch (e) {
          var st = document.getElementById("sky-status");
          if (st) {
            st.textContent = "Encode error: " + e.message;
            st.className = "status-line err";
          }
        }
      });
    }
    var ins = document.getElementById("btn-sky-insert");
    if (ins) {
      ins.addEventListener("click", function () {
        try {
          var r = encodeCurrent();
          insertBytes(r.unit, "append");
          showFields(r.unit, r.pol);
        } catch (e) {
          alert("PATHHINT error: " + e.message);
        }
      });
    }
    var can = document.getElementById("btn-sky-canonical");
    if (can) {
      can.addEventListener("click", function () {
        loadGallery("skypulse");
        var unit = buildSkyPulse();
        var pol = C.recommendIntegrity("ASCENT-E-LEO");
        showFields(unit, pol);
      });
    }
    var sel = document.getElementById("sky-profile");
    if (sel) {
      sel.addEventListener("change", function () {
        var pol = C.recommendIntegrity(sel.value);
        var st = document.getElementById("sky-status");
        if (st) {
          st.textContent = pol.note;
          st.className = "status-line ok";
        }
      });
    }
  }

  // ---------- chrome: cmdk, density, focus, mobile ----------

  var CMDK_ITEMS = [];

  function buildCmdkCatalog() {
    var items = [];
    [
      ["Navigate", "Manifesto", "#manifesto", "g m"],
      ["Navigate", "Wire Lab", "#lab", "g l"],
      ["Navigate", "SkyPulse", "#skypulse", ""],
      ["Navigate", "Planes", "#architecture", ""],
      ["Navigate", "SPEC", "#spec", ""],
      ["Navigate", "Install", "#install", ""],
      ["Navigate", "FAQ", "#faq", ""],
    ].forEach(function (row) {
      items.push({ group: row[0], label: row[1], href: row[2], hint: row[3], kind: "nav" });
    });
    GALLERY.forEach(function (g) {
      items.push({ group: "Samples", label: "Load " + g.label, sample: g.id, kind: "sample" });
    });
    items.push({ group: "Actions", label: "Encode text", action: "encode", hint: "e", kind: "act" });
    items.push({ group: "Actions", label: "Decode hex", action: "decode", hint: "d", kind: "act" });
    items.push({ group: "Actions", label: "Share stream URL", action: "share", kind: "act" });
    items.push({ group: "Actions", label: "Toggle focus lab", action: "focus", kind: "act" });
    items.push({ group: "Actions", label: "Toggle compact density", action: "compact", kind: "act" });
    items.push({ group: "Actions", label: "Start 2-minute tour", action: "tour", kind: "act" });
    CMDK_ITEMS = items;
  }

  function cmdkOpen() {
    var wrap = document.getElementById("cmdk");
    var input = document.getElementById("cmdk-input");
    if (!wrap) return;
    wrap.hidden = false;
    wrap.setAttribute("data-open", "true");
    renderCmdk("");
    if (input) {
      input.value = "";
      input.focus();
    }
  }

  function cmdkClose() {
    var wrap = document.getElementById("cmdk");
    var input = document.getElementById("cmdk-input");
    var trigger = document.getElementById("btn-cmdk");
    if (!wrap) return;
    wrap.setAttribute("data-open", "false");
    wrap.hidden = true;
    if (input) input.value = "";
    if (trigger) trigger.focus();
  }

  function cmdkIsOpen() {
    var wrap = document.getElementById("cmdk");
    return !!(wrap && wrap.getAttribute("data-open") === "true");
  }

  function fuzzy(q, s) {
    q = String(q || "").toLowerCase();
    s = String(s || "").toLowerCase();
    if (!q) return true;
    if (s.indexOf(q) >= 0) return true;
    var j = 0;
    for (var i = 0; i < s.length && j < q.length; i++) {
      if (s.charCodeAt(i) === q.charCodeAt(j)) j++;
    }
    return j === q.length;
  }

  function renderCmdk(q) {
    var list = document.getElementById("cmdk-list");
    if (!list) return;
    var hits = CMDK_ITEMS.filter(function (it) {
      return fuzzy(q, it.group + " " + it.label);
    });
    if (!hits.length) {
      list.innerHTML = '<div class="cmdk-empty">No matches. Try lab, captain, or encode.</div>';
      return;
    }
    var html = "";
    var last = "";
    hits.forEach(function (it, i) {
      if (it.group !== last) {
        html += '<div class="cmdk-group">' + escapeHtml(it.group) + "</div>";
        last = it.group;
      }
      html +=
        '<button type="button" class="cmdk-item" role="option" data-idx="' +
        i +
        '" aria-selected="' +
        (i === 0 ? "true" : "false") +
        '"><span>' +
        escapeHtml(it.label) +
        "</span>" +
        (it.hint ? "<kbd>" + escapeHtml(it.hint) + "</kbd>" : "") +
        "</button>";
    });
    list.innerHTML = html;
    list._hits = hits;
    list.querySelectorAll(".cmdk-item").forEach(function (btn) {
      btn.addEventListener("click", function () {
        runCmdk(hits[parseInt(btn.getAttribute("data-idx"), 10)]);
      });
    });
  }

  function runCmdk(it) {
    if (!it) return;
    cmdkClose();
    if (it.kind === "nav" && it.href) {
      var el = document.querySelector(it.href);
      if (el) el.scrollIntoView({ behavior: "smooth" });
      return;
    }
    if (it.kind === "sample") {
      loadGallery(it.sample);
      var lab = document.getElementById("lab");
      if (lab) lab.scrollIntoView({ behavior: "smooth" });
      toast("Loaded " + it.label.replace(/^Load /, ""), "ok");
      return;
    }
    if (it.action === "encode") encodeFromText(true);
    if (it.action === "decode") decodeFromHex({ flash: true, forceText: true });
    if (it.action === "share") {
      var share = document.getElementById("btn-share");
      if (share) share.click();
    }
    if (it.action === "focus") {
      var f = document.getElementById("opt-focus");
      if (f) {
        f.checked = !f.checked;
        f.dispatchEvent(new Event("change"));
      }
    }
    if (it.action === "compact") {
      var c = document.getElementById("opt-compact");
      if (c) {
        c.checked = !c.checked;
        c.dispatchEvent(new Event("change"));
      }
    }
    if (it.action === "tour") {
      var t = document.getElementById("btn-start-tour");
      if (t) t.click();
    }
  }

  function wireChrome() {
    buildCmdkCatalog();
    var cmdkBtn = document.getElementById("btn-cmdk");
    var cmdkInput = document.getElementById("cmdk-input");
    var backdrop = document.getElementById("cmdk");
    if (cmdkBtn) cmdkBtn.addEventListener("click", cmdkOpen);
    if (backdrop) {
      backdrop.addEventListener("click", function (e) {
        if (e.target === backdrop) cmdkClose();
      });
    }
    if (cmdkInput) {
      cmdkInput.addEventListener("input", function () {
        renderCmdk(cmdkInput.value);
      });
      cmdkInput.addEventListener("keydown", function (e) {
        var list = document.getElementById("cmdk-list");
        var items = list ? list.querySelectorAll(".cmdk-item") : [];
        var sel = list ? list.querySelector('.cmdk-item[aria-selected="true"]') : null;
        var idx = 0;
        for (var i = 0; i < items.length; i++) {
          if (items[i] === sel) idx = i;
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          idx = Math.min(items.length - 1, idx + 1);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          idx = Math.max(0, idx - 1);
        } else if (e.key === "Enter") {
          e.preventDefault();
          if (sel) sel.click();
          return;
        } else {
          return;
        }
        items.forEach(function (n, i) {
          n.setAttribute("aria-selected", i === idx ? "true" : "false");
        });
        if (items[idx]) items[idx].scrollIntoView({ block: "nearest" });
      });
    }

    var navToggle = document.getElementById("nav-toggle");
    var navLinks = document.getElementById("nav-links");
    if (navToggle && navLinks) {
      navToggle.addEventListener("click", function () {
        var open = navLinks.classList.toggle("is-open");
        navToggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      navLinks.querySelectorAll("a").forEach(function (a) {
        a.addEventListener("click", function () {
          navLinks.classList.remove("is-open");
          navToggle.setAttribute("aria-expanded", "false");
        });
      });
    }

    var focus = document.getElementById("opt-focus");
    if (focus) {
      focus.addEventListener("change", function () {
        document.body.setAttribute("data-lab-focus", focus.checked ? "true" : "false");
        try {
          localStorage.setItem("ascent-lab-focus", focus.checked ? "1" : "0");
        } catch (e) {}
        toast(focus.checked ? "Focus lab on" : "Focus lab off", "ok");
      });
      try {
        if (localStorage.getItem("ascent-lab-focus") === "1") {
          focus.checked = true;
          document.body.setAttribute("data-lab-focus", "true");
        }
      } catch (e) {}
    }
    var compact = document.getElementById("opt-compact");
    if (compact) {
      compact.addEventListener("change", function () {
        document.body.setAttribute("data-density", compact.checked ? "compact" : "comfortable");
        try {
          localStorage.setItem("ascent-density", compact.checked ? "compact" : "comfortable");
        } catch (e) {}
      });
      try {
        if (localStorage.getItem("ascent-density") === "compact") {
          compact.checked = true;
          document.body.setAttribute("data-density", "compact");
        }
      } catch (e) {}
    }

    var captain = document.getElementById("btn-captain");
    if (captain) {
      captain.addEventListener("click", function () {
        loadGallery("mixed");
        var lab = document.getElementById("lab");
        if (lab) lab.scrollIntoView({ behavior: "smooth" });
      });
    }

    document.addEventListener("keydown", function (e) {
      var tag = (e.target && e.target.tagName) || "";
      var typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (e.target && e.target.isContentEditable);
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (cmdkIsOpen()) cmdkClose();
        else cmdkOpen();
        return;
      }
      if (e.key === "Escape") {
        if (cmdkIsOpen()) {
          e.preventDefault();
          cmdkClose();
        }
        return;
      }
      if (typing) return;
      if (e.key === "?") {
        cmdkOpen();
        return;
      }
      if (e.key.toLowerCase() === "e") encodeFromText(true);
      if (e.key.toLowerCase() === "d") decodeFromHex({ flash: true, forceText: true });
    });
  }

  // ---------- main wire ----------

  function wireUi() {
    wireGallery();
    wireTour();
    wireSpec();
    wireArchitecture();
    wireAgentComposer();
    wireMmComposer();
    wireAegir();
    wireSkyPulse();
    wireDsim();
    wireCodegen();
    wireExport();
    wireProfile();
    wireSacredInput();
    wireMeta();
    wireChrome();

    var live = document.getElementById("opt-live");
    if (live) {
      live.addEventListener("change", function () {
        state.live = !!live.checked;
      });
    }

    var textInput = document.getElementById("text-input");
    var hexInput = document.getElementById("hex-input");
    var liveEncode = debounce(function () {
      if (!state.live || state.suppressText) return;
      encodeFromText(false);
    }, 220);
    var liveDecode = debounce(function () {
      if (!state.live || state.suppressHex) return;
      decodeFromHex({ flash: false, forceText: true });
    }, 220);
    if (textInput) textInput.addEventListener("input", liveEncode);
    if (hexInput) hexInput.addEventListener("input", liveDecode);

    var btnEnc = document.getElementById("btn-encode");
    if (btnEnc) btnEnc.addEventListener("click", function () { encodeFromText(true); });
    var btnEncDec = document.getElementById("btn-encode-decode");
    if (btnEncDec) {
      btnEncDec.addEventListener("click", function () {
        encodeFromText(true);
        document.getElementById("lab-results").scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    }
    var btnDec = document.getElementById("btn-decode");
    if (btnDec) {
      btnDec.addEventListener("click", function () {
        decodeFromHex({ flash: true, forceText: true });
      });
    }
    var btnHello = document.getElementById("btn-hello");
    if (btnHello) {
      btnHello.addEventListener("click", function () {
        loadGallery("hello");
        document.getElementById("lab").scrollIntoView({ behavior: "smooth" });
      });
    }

    window.ASCENT = {
      version: "3.0.0-crystal-wire",
      getState: function () {
        return state;
      },
      setStream: setStream,
      loadGallery: loadGallery,
      decodeStream: C.decodeStream,
      encodeText: C.encodeText,
      fromHex: C.fromHex,
      hexOf: C.hexOf,
      HELLO_HEX: C.HELLO_UNIVERSE_HEX,
    };

    if (!loadFromHash()) {
      loadGallery("hello");
    }
  }

  function boot() {
    try {
      initCanvas();
      wireUi();
    } catch (e) {
      console.error("ASCENT Nexus boot failed:", e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
