import { createI18n } from "vue-i18n";
import en from "@/locales/en";
import zhCN from "@/locales/zh-CN";


const STORAGE_KEY = "edms_locale";

export type LocaleCode = "en" | "zh-CN";

export function getSavedLocale(): LocaleCode {
  const v = localStorage.getItem(STORAGE_KEY);
  if (v === "zh-CN" || v === "en") return v;
  
  // Detect system language
  const navLang = navigator.language.toLowerCase();
  if (navLang.startsWith("zh")) return "zh-CN";

  
  return "en";
}

export function saveLocale(code: LocaleCode) {
  localStorage.setItem(STORAGE_KEY, code);
}

export const i18n = createI18n({
  legacy: false,
  locale: getSavedLocale(),
  fallbackLocale: "en",
  messages: {
    en,
    "zh-CN": zhCN,
    zh: zhCN,
  },
});
