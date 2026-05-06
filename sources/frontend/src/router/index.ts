import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: () => import("@/views/LoginView.vue") },
    { path: "/admin", name: "admin", component: () => import("@/views/AdminView.vue") },
    {
      path: "/",
      component: () => import("@/layouts/MainLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        { path: "", name: "library", component: () => import("@/views/LibraryView.vue") },
        { path: "import", name: "import", component: () => import("@/views/ImportView.vue"), meta: { requiresManager: true } },
        { path: "inbox", name: "inbox", component: () => import("@/views/InboxView.vue") },
        { path: "dashboard", name: "dashboard", component: () => import("@/views/DashboardView.vue") },
        { path: "templates", name: "templates", component: () => import("@/views/TemplateView.vue") },
        { path: "template-admin", name: "template-admin", component: () => import("@/views/TemplateAdminView.vue"), meta: { requiresManager: true } },
        {
          path: "doc/:id",
          name: "editor",
          component: () => import("@/views/EditorView.vue"),
        },
        {
          path: "doc/:id/diff",
          name: "diff",
          component: () => import("@/views/DiffView.vue"),
        },
        { path: "personal", name: "personal", component: () => import("@/views/PersonalView.vue") },
        { path: "users", name: "users", component: () => import("@/views/UserManagementView.vue"), meta: { requiresManager: true } },
        { path: "audit-log", name: "audit-log", component: () => import("@/views/AuditLogView.vue"), meta: { requiresAdmin: true } },
        { path: "ai-history", name: "ai-history", component: () => import("@/views/AiHistoryView.vue"), meta: { requiresAdmin: true } },
        { path: "notifications", name: "notifications", component: () => import("@/views/NotificationsView.vue") },
        { path: "ai", name: "ai", component: () => import("@/views/AiView.vue") },
      ],
    },
  ],
});

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.token) {
    next({ name: "login", query: { redirect: to.fullPath } });
    return;
  }
  if (to.name === "login" && auth.token) {
    next({ name: "library" });
    return;
  }
  // 检查是否需要 manager 权限
  if (to.meta.requiresManager && !auth.user?.is_manager && auth.user?.login_name !== 'admin') {
    next({ name: "library" });
    return;
  }
  // 检查是否需要 system admin 权限
  if (to.meta.requiresAdmin && auth.user?.login_name !== 'admin') {
    next({ name: "library" });
    return;
  }
  next();
});

export default router;
