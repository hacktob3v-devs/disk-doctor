/*
 * İki sayfanın ortak yardımcıları:
 * - Müşteri sayfasından gelen mesajları satıcı masasına taşıyan yerel gelen kutusu
 * - Sesli okuma (TTS) ve mikrofonla yazdırma (STT)
 */
window.ED_SHARED = (function () {
  "use strict";

  const KEY = "ed_inbox_v1";

  function readInbox() {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); }
    catch { return []; }
  }

  function pushInbox(item) {
    const list = readInbox();
    list.unshift(item);
    try { localStorage.setItem(KEY, JSON.stringify(list.slice(0, 50))); } catch { /* depolama kapalı */ }
  }

  function clearInbox() {
    try { localStorage.removeItem(KEY); } catch { /* depolama kapalı */ }
  }

  function onInboxChange(cb) {
    window.addEventListener("storage", (e) => { if (e.key === KEY) cb(readInbox()); });
  }

  // Ekranda anlamlı ama kulakta gürültü olan parçaları ayıklar:
  // kural kodları, sipariş numaraları, imza, emoji, simgeler.
  function toSpeech(text) {
    return String(text)
      .replace(/https?:\/\/\S+/g, "")
      .replace(/[\p{Extended_Pictographic}️‍]/gu, "")
      .replace(/\[[^\]]*\]/g, "")
      .replace(/\bPOL_[A-Z]+_\d+\b/g, "")
      .replace(/\b[A-Z]{2}-\d{4,}\b\s*(numaralı\s*)?/g, "")
      .replace(/\s*(—|-)?\s*Usta Deri\.?\s*$/u, "")
      .replace(/%\s?(\d+)/g, "yüzde $1")
      .replace(/(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})/g, "$1 ile $2")
      .replace(/(\d+)\s*-\s*(\d+)/g, "$1 ila $2")
      .replace(/(\d)\.(\d{3})\b/g, "$1$2")
      .replace(/\s*(TL|₺)\b/g, " lira")
      .replace(/\s*&\s*/g, " ve ")
      .replace(/\s*[·•|\/]\s*/g, ", ")
      .replace(/[*_#`>~]/g, "")
      .replace(/\(\s*\)/g, "")
      .replace(/\s+([,.!?])/g, "$1")
      .replace(/,\s*,/g, ",")
      .replace(/\s{2,}/g, " ")
      .replace(/^[,\s]+|[,\s]+$/g, "");
  }

  function speak(text) {
    if (!("speechSynthesis" in window)) return false;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(toSpeech(text));
    u.lang = "tr-TR";
    u.rate = 1.05;
    speechSynthesis.speak(u);
    return true;
  }

  // Not: Chrome/Edge'in yerleşik konuşma tanıma servisi sesi buluta gönderir.
  // Tam çevrimdışı demo için yerel Whisper (whisper.cpp / faster-whisper) ile değiştirilecek.
  function createDictation({ onStart, onResult, onEnd, onError }) {
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Rec) return null;
    const rec = new Rec();
    rec.lang = "tr-TR";
    rec.continuous = false;
    rec.interimResults = true;
    let active = false;
    rec.onstart = () => { active = true; onStart && onStart(); };
    rec.onresult = (e) => {
      let text = "";
      for (const r of e.results) text += r[0].transcript;
      onResult && onResult(text, e.results[e.results.length - 1].isFinal);
    };
    rec.onerror = (e) => { onError && onError(e.error); };
    rec.onend = () => { active = false; onEnd && onEnd(); };
    return {
      toggle() { active ? rec.stop() : rec.start(); },
      get active() { return active; }
    };
  }

  const nowHHMM = () => new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });

  function getPref(key, fallback) {
    try { const v = localStorage.getItem("ed_pref_" + key); return v === null ? fallback : v === "1"; }
    catch { return fallback; }
  }
  function setPref(key, on) {
    try { localStorage.setItem("ed_pref_" + key, on ? "1" : "0"); } catch { /* depolama kapalı */ }
  }

  return { readInbox, pushInbox, clearInbox, onInboxChange, toSpeech, speak, createDictation, nowHHMM, getPref, setPref };
})();
