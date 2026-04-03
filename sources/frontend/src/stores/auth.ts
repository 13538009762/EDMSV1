import { defineStore } from "pinia";
import { ref, computed } from "vue";
import api from "@/api/client";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("edms_token"));
  const user = ref<{ id: number; login_name: string; display_name: string; is_manager?: boolean } | null>(
    null,
  );

  const isAuthenticated = computed(() => !!token.value);

  function setToken(t: string | null) {
    token.value = t;
    if (t) localStorage.setItem("edms_token", t);
    else localStorage.removeItem("edms_token");
  }

  async function login(loginName: string) {
    const { data } = await api.post("/auth/login", { login_name: loginName });
    setToken(data.access_token);
    user.value = data.user;
    return data;
  }

  async function fetchMe() {
    if (!token.value) return;
    const { data } = await api.get("/auth/me");
    user.value = data;
  }

  function logout() {
    setToken(null);
    user.value = null;
  }

  return { token, user, isAuthenticated, login, fetchMe, logout, setToken };
});
