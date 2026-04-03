<template>
  <div class="wrap">
    <div class="top-bar">
      <img src="/favicon.png" class="top-icon" alt="System Icon" />
      <LocaleSwitcher />
    </div>
    <div class="login-container">
      <!-- 左侧轮播图 -->
      <div class="carousel-container">
        <el-carousel :interval="4000" height="100%">
          <el-carousel-item v-for="(item, index) in carouselImages" :key="index">
            <img :src="item.src" :alt="item.alt" class="carousel-image" />
          </el-carousel-item>
        </el-carousel>
      </div>
      
      <!-- 右侧登录卡片 -->
      <div class="login-card-container">
        <el-card class="card">
          <template #header>{{ t("login.title") }}</template>
          <el-form @submit.prevent="submit">
            <el-form-item :label="t('login.loginName')">
              <el-input v-model="loginName" autocomplete="username" />
            </el-form-item>
            <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">{{
              t("login.submit")
            }}</el-button>
            <div class="admin-link">
              <el-button type="primary" link @click="router.push({ name: 'admin' })">{{
                t("login.goAdmin")
              }}</el-button>
            </div>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/auth";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";

const loginName = ref("");
const loading = ref(false);
const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const { t } = useI18n();

// 轮播图数据，预留接口
const carouselImages = ref([
  {
    src: "/images/carousel/1.png", // 图片接口路径
    alt: "EDMS System"
  },
  {
    src: "/images/carousel/2.png", // 图片接口路径
    alt: "Document Management"
  },
  {
    src: "/images/carousel/3.png", // 图片接口路径
    alt: "Workflow Automation"
  }
]);

async function submit() {
  loading.value = true;
  try {
    await auth.login(loginName.value.trim());
    const r = (route.query.redirect as string) || "/";
    router.replace(r);
  } catch {
    ElMessage.error(t("login.invalid"));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.wrap {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  background: var(--el-fill-color-light);
  position: relative;
  overflow: hidden;
}
.top-bar {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
  display: flex;
  align-items: center;
}
.top-icon {
  width: clamp(40px, 10vw, 80px);
  height: auto;
  margin-right: 15px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
  transition: transform 0.3s ease;
}
.top-icon:hover {
  transform: scale(1.05);
}
.login-container {
  display: flex;
  flex: 1;
  width: 100%;
  height: 100%;
}
.carousel-container {
  width: 70%;
  height: 100%;
}

.carousel-container :deep(.el-carousel) {
  height: 100%;
}

.login-card-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 40px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
}
.card {
  width: 100%;
  max-width: 400px;
}
.carousel-image {
  width: 100%;
  height: 100%;
  object-fit: fill;
  display: block;
}
.admin-link {
  margin-top: 12px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }
  .carousel-container {
    height: 40%;
    min-width: 100%;
  }
  .login-card-container {
    width: 100%;
    height: 60%;
    padding: 0 20px;
  }
}
</style>
