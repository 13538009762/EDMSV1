<template>
  <div class="editor-page" v-loading="loading">
    <div class="header-bar">
      <div class="header-left">
        <el-input v-model="title" style="width: 240px" :disabled="!meta.can_edit" @blur="saveTitle" />
        <el-tag :type="statusTag" class="status-tag">{{ statusLabel }}</el-tag>
        <span class="hint">{{ saveHint }}</span>
      </div>
      
      <div class="header-right">
        <div class="collab-avatars" v-if="collabColors.length">
          <el-tooltip v-for="(c, i) in collabColors" :key="i" :content="c.name" placement="bottom">
            <div class="avatar-dot" :style="{ backgroundColor: c.color }">{{ c.name.charAt(0).toUpperCase() }}</div>
          </el-tooltip>
        </div>
        
        <el-dropdown trigger="click" style="margin-right: 8px;">
          <el-button>{{ t("editor.actions") }} <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="meta.can_edit" :loading="saving" @click="saveNow">{{ t("editor.save") }}</el-dropdown-item>
              <el-dropdown-item @click="downloadDocx">{{ t("editor.exportDocx") }}</el-dropdown-item>
              <el-dropdown-item @click="downloadPdf">{{ t("editor.exportPdf") }}</el-dropdown-item>
              <el-dropdown-item v-if="meta.can_edit && meta.status === 'draft'" @click="showApproval = true">{{ t("editor.startApproval") }}</el-dropdown-item>
              <el-dropdown-item v-if="meta.status === 'rejected' && isOwner" @click="newVersion">{{ t("editor.newVersion") }}</el-dropdown-item>
              <el-dropdown-item @click="searchVisible = !searchVisible">{{ t("editor.findReplace") }}</el-dropdown-item>
              <el-dropdown-item @click="fixPunc">{{ t("editor.punctuation") }}</el-dropdown-item>
              <el-dropdown-item @click="pageSettingsVisible = true">{{ t("editor.pageSetup") }}</el-dropdown-item>
              <el-dropdown-item v-if="meta.can_manage_permissions && meta.status === 'draft'" @click="showShare = true">{{ t("library.share") }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="editor-toolbar" v-if="editor && meta.can_edit">
      <el-select v-model="currentFontFamily" size="small" style="width: 120px" @change="setFontFamily">
        <el-option label="Default" value="Inter, sans-serif" />
        <el-option label="Arial" value="Arial" />
        <el-option label="Courier New" value="Courier New" />
        <el-option label="Georgia" value="Georgia" />
        <el-option label="Times New Roman" value="Times New Roman" />
      </el-select>
      <el-select v-model="currentFontSize" size="small" style="width: 80px" @change="setFontSize">
        <el-option v-for="size in ['12px', '14px', '16px', '18px', '24px', '36px']" :key="size" :label="size" :value="size" />
      </el-select>
      <div class="toolbar-divider"></div>
      
      <el-button-group class="toolbar-group">
        <el-tooltip :content="t('editor.toolbar.bold', 'Bold')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('bold') }" @click="editor.chain().focus().toggleBold().run()"><b style="font-family: serif">B</b></el-button>
        </el-tooltip>
        <el-tooltip :content="t('editor.toolbar.italic', 'Italic')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('italic') }" @click="editor.chain().focus().toggleItalic().run()"><i style="font-family: serif">I</i></el-button>
        </el-tooltip>
        <el-tooltip :content="t('editor.toolbar.underline', 'Underline')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('underline') }" @click="editor.chain().focus().toggleUnderline().run()"><u style="font-family: serif">U</u></el-button>
        </el-tooltip>
        <el-tooltip :content="t('editor.toolbar.strike', 'Strike')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('strike') }" @click="editor.chain().focus().toggleStrike().run()"><s style="font-family: serif">S</s></el-button>
        </el-tooltip>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button-group class="toolbar-group">
        <el-button size="small" :class="{ 'is-active': editor.isActive('heading', { level: 1 }) }" @click="editor.chain().focus().toggleHeading({ level: 1 }).run()">H1</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('heading', { level: 2 }) }" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()">H2</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('heading', { level: 3 }) }" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()">H3</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('paragraph') }" @click="editor.chain().focus().setParagraph().run()">P</el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button-group class="toolbar-group">
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'left' }) }" @click="editor.chain().focus().setTextAlign('left').run()">L</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'center' }) }" @click="editor.chain().focus().setTextAlign('center').run()">C</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'right' }) }" @click="editor.chain().focus().setTextAlign('right').run()">R</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'justify' }) }" @click="editor.chain().focus().setTextAlign('justify').run()">J</el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button-group class="toolbar-group">
        <el-button size="small" :class="{ 'is-active': editor.isActive('bulletList') }" @click="editor.chain().focus().toggleBulletList().run()">• {{ t("editor.toolbar.bulletList") }}</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('orderedList') }" @click="editor.chain().focus().toggleOrderedList().run()">1. {{ t("editor.toolbar.orderedList") }}</el-button>
      </el-button-group>
      
      <div class="toolbar-divider"></div>
      
      <el-button-group class="toolbar-group">
        <el-button size="small" @click="doOutdent">- {{ t("editor.toolbar.outdent") }}</el-button>
        <el-button size="small" @click="doIndent">+ {{ t("editor.toolbar.indent") }}</el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>
      <el-button size="small" @click="insertImage">{{ t("editor.toolbar.image") }}</el-button>
      <el-button size="small" @click="insertCustomTable">{{ t("editor.toolbar.table") }}</el-button>
      <el-button size="small" type="success" plain @click="importDocx">{{ t("editor.toolbar.importDocx") }}</el-button>
      <el-button size="small" @click="fixPunc">{{ t("editor.toolbar.fixPunc") }}</el-button>
      <el-button size="small" type="info" plain @click="searchVisible = !searchVisible">{{ t("editor.toolbar.findReplace") }}</el-button>
      
      <el-button-group class="toolbar-group" v-if="editor && editor.isActive('table')">
        <el-button size="small" @click="editor.chain().focus().addRowBefore().run()">{{ t("editor.toolbar.addRowBefore") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().addRowAfter().run()">{{ t("editor.toolbar.addRowAfter") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().deleteRow().run()">{{ t("editor.toolbar.deleteRow") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().addColumnBefore().run()">{{ t("editor.toolbar.addColumnBefore") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().addColumnAfter().run()">{{ t("editor.toolbar.addColumnAfter") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().deleteColumn().run()">{{ t("editor.toolbar.deleteColumn") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().deleteTable().run()">{{ t("editor.toolbar.deleteTable") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().toggleHeaderRow().run()">{{ t("editor.toolbar.headerRow") }}</el-button>
      </el-button-group>
      <el-button-group class="toolbar-group" v-if="editor && editor.isActive('image')" style="margin-left: 8px;">
        <el-button size="small" type="warning" plain @click="setImgWidth('100%')">
          {{ t("editor.toolbar.imgSize100") }}
        </el-button>
        <el-button size="small" type="warning" plain @click="setImgWidth('50%')">
          {{ t("editor.toolbar.imgSize50") }}
        </el-button>
        <el-button size="small" type="warning" plain @click="setImgWidth('25%')">
          {{ t("editor.toolbar.imgSize25") }}
        </el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>
      <div style="display: flex; align-items: center; gap: 4px; font-size: 12px; margin-right:8px;">
        <label>{{ t("editor.toolbar.textColor") }}</label>
        <input type="color" v-model="currentColor" @change="setTextColor" style="width: 24px; height: 24px; padding: 0; border: none; cursor: pointer" />
      </div>
      <div style="display: flex; align-items: center; gap: 4px; font-size: 12px">
        <label>{{ t("editor.toolbar.highlight") }}</label>
        <input type="color" v-model="currentHighlight" @change="setHighlight" style="width: 24px; height: 24px; padding: 0; border: none; cursor: pointer" />
      </div>

    </div>

    <!-- Search/Replace Bar -->
    <div v-if="searchVisible" class="search-bar">
      <el-input v-model="searchTerm" :placeholder="t('editor.searchPlaceholder')" size="small" style="width: 150px" @input="updateSearch" />
      <el-input v-model="replaceTerm" :placeholder="t('editor.replacePlaceholder')" size="small" style="width: 150px" />
      <el-button size="small" @click="doReplace">{{ t("editor.replace") }}</el-button>
      <el-button size="small" @click="doReplaceAll">{{ t("editor.replaceAll") }}</el-button>
      <el-button size="small" icon="Close" @click="searchVisible = false" />
    </div>

    <div class="body">
      <div class="main-wrapper" v-if="editor">
        <div class="main-paper" :class="page.paperFormat">
          <editor-content :editor="editor" class="tiptap" :style="{ paddingTop: page.marginTop + 'px', paddingBottom: page.marginBottom + 'px' }" />
        </div>
      </div>
      <div class="side">
        <el-tabs v-model="activeSideTab" stretch>
          <el-tab-pane :label="t('editor.commentsTab')" name="comments">
            <div class="comments-header">
              <el-button v-if="meta.can_comment" size="small" type="primary" style="width: 100%; margin-top: 8px; margin-bottom: 12px;" @click="addCommentOnSelection">
                {{ t("editor.commentSelection") }}
              </el-button>
            </div>
            
            <div class="comment-filters">
              <el-select v-model="filterAuthor" size="small" :placeholder="t('editor.commentsFilters.author')" clearable class="filter-item">
                <el-option v-for="a in authorOptions" :key="a" :label="a" :value="a" />
              </el-select>
              <el-select v-model="filterStatus" size="small" :placeholder="t('editor.commentsFilters.status')" class="filter-item">
                <el-option :label="t('editor.commentsFilters.all')" value="all" />
                <el-option :label="t('editor.commentsFilters.active')" value="active" />
                <el-option :label="t('editor.commentsFilters.resolved')" value="resolved" />
              </el-select>
              <el-date-picker v-model="filterDate" type="date" :placeholder="t('editor.commentsFilters.date')" size="small" class="filter-item" value-format="YYYY-MM-DD" style="width:100%" />
            </div>

            <div class="comments-list">
              <div v-for="m in threadedComments" :key="m.id" class="comment-group">
                <div class="comment" :class="{ 'resolved': m.status === 'resolved' }" @click="scrollToComment(m.id)">
                  <div class="meta">
                    <div style="font-weight: 500;">{{ m.author_login }}</div>
                    <div class="meta-right">
                      <span>{{ m.created_at ? m.created_at.split('T')[0] : '' }} · {{ m.status }}</span>
                      <el-button
                        v-if="m.status === 'active'"
                        link
                        type="primary"
                        @click.stop="resolveComment(m.id)"
                        size="small"
                      >
                        {{ t("editor.resolve") }}
                      </el-button>
                    </div>
                  </div>
                  <div class="comment-body">{{ m.body }}</div>
                  <el-input
                    v-model="replyMap[m.id]"
                    :placeholder="t('editor.replyPlaceholder')"
                    size="small"
                    @keyup.enter="replyTo(m.id)"
                    @click.stop
                  />
                </div>
                
                <div v-if="m.replies && m.replies.length" class="replies">
                  <div v-for="r in m.replies" :key="r.id" class="comment reply" :class="{ 'resolved': r.status === 'resolved' }">
                    <div class="meta">
                      <div style="font-weight: 500;">{{ r.author_login }}</div>
                      <div class="meta-right">
                        <span>{{ r.created_at ? r.created_at.split('T')[0] : '' }}</span>
                      </div>
                    </div>
                    <div class="comment-body">{{ r.body }}</div>
                  </div>
                </div>
              </div>
              <el-empty v-if="threadedComments.length === 0" :description="t('editor.commentsFilters.noComments')" :image-size="60" />
            </div>
            <el-button size="small" @click="loadComments" style="width:100%; margin-top: 12px;">{{ t("editor.refreshComments") }}</el-button>
          </el-tab-pane>

          <el-tab-pane :label="t('editor.versionsTab')" name="versions">
            <div class="version-list-container">
              <div class="version-header">
                <el-button size="small" type="primary" @click="$router.push(`/doc/${docId}/diff`)">{{ t("editor.viewDiff") }}</el-button>
                <el-button size="small" @click="loadVersions">{{ t("editor.refresh") }}</el-button>
              </div>
              <div class="version-items">
                <div v-for="v in versionList" :key="v.id" class="version-item">
                  <div class="v-meta">
                    <span class="v-no">V{{ v.version_no }}</span>
                    <span class="v-user">{{ v.created_by_name }}</span>
                  </div>
                  <div class="v-time">{{ new Date(v.created_at).toLocaleString() }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <DocumentShareDialog v-model="showShare" :document-id="docId" @saved="loadDoc" />

    <el-dialog v-model="pageSettingsVisible" :title="t('editor.pageSetupTitle')" width="400px">
      <el-form label-width="120px">
        <el-form-item :label="t('editor.orientation')">
          <el-radio-group v-model="page.orientation">
            <el-radio label="portrait">{{ t("editor.portrait") }}</el-radio>
            <el-radio label="landscape">{{ t("editor.landscape") }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('editor.paperSize')">
          <el-select v-model="page.paperFormat">
            <el-option label="A4" value="A4" />
            <el-option label="Letter" value="Letter" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('editor.marginTop')">
          <el-slider v-model="page.marginTop" :min="0" :max="100" />
        </el-form-item>
        <el-form-item :label="t('editor.marginBottom')">
          <el-slider v-model="page.marginBottom" :min="0" :max="100" />
        </el-form-item>
        <el-form-item :label="t('editor.showPageNumber')">
          <el-switch v-model="page.showPageNumber" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="savePageSettings">{{ t("editor.apply") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showApproval" :title="t('editor.approvalTitle')" width="420px">
      <el-radio-group v-model="approvalType">
        <el-radio label="parallel">{{ t("editor.parallel") }}</el-radio>
        <el-radio label="sequential">{{ t("editor.sequential") }}</el-radio>
      </el-radio-group>
      <el-select
        v-model="approverIds"
        multiple
        filterable
        :placeholder="t('editor.approversPlaceholder')"
        style="width: 100%; margin-top: 12px"
      >
        <el-option v-for="u in filteredUserOptions" :key="u.id" :label="`${u.login_name}`" :value="u.id" />

      </el-select>
      <template #footer>
        <el-button type="primary" @click="startApproval">{{ t("editor.start") }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import * as Y from "yjs";
import { Awareness } from "y-protocols/awareness";
import { useEditor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import Underline from "@tiptap/extension-underline";
import TextAlign from "@tiptap/extension-text-align";
import TextStyle from "@tiptap/extension-text-style";
import Color from "@tiptap/extension-color";
import Highlight from "@tiptap/extension-highlight";
import FontFamily from "@tiptap/extension-font-family";
import Image from "@tiptap/extension-image";
import Dropcursor from "@tiptap/extension-dropcursor";
import Gapcursor from "@tiptap/extension-gapcursor";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import { ArrowDown } from "@element-plus/icons-vue";

import { FontSize, LineHeight, Indent, CommentMark, TableExit, SearchAndReplace } from "@/utils/tiptapExtensions";
import api from "@/api/client";
import { useAuthStore } from "@/stores/auth";
import { attachDocCollab } from "@/composables/useDocSocket";
import { fixPunctuation } from "@/utils/punctuation";
import { ElMessage, ElMessageBox } from "element-plus";
import mammoth from "mammoth";
import DocumentShareDialog from "@/components/DocumentShareDialog.vue";

const CustomImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: null,
        parseHTML: element => element.getAttribute('width'),
        renderHTML: attributes => {
          if (!attributes.width) return {};
          return { width: attributes.width };
        }
      }
    };
  }
});
const route = useRoute();
const { t } = useI18n();
const auth = useAuthStore();
const docId = computed(() => Number(route.params.id));

const loading = ref(true);
const saving = ref(false);
const title = ref("");
const meta = ref<any>({
  status: "draft",
  can_edit: false,
  can_comment: false,
  can_manage_permissions: false,
  owner_id: 0,
});

const showShare = ref(false);
const comments = ref<Array<any>>([]);
const replyMap = ref<Record<number, string>>({});
const activeSideTab = ref("comments");
const versionList = ref<Array<any>>([]);

const searchVisible = ref(false);
const searchTerm = ref("");
const replaceTerm = ref("");
const pageSettingsVisible = ref(false);

const showApproval = ref(false);
const approvalType = ref("parallel");
const approverIds = ref<number[]>([]);
const userOptions = ref<Array<{ id: number; login_name: string }>>([]);

const page = ref({
  orientation: "portrait",
  marginTop: 40,
  marginBottom: 40,
  showPageNumber: true,
  paperFormat: "A4",
});

const saveHint = ref("");
const collabColors = ref<Array<{ name: string; color: string }>>([]);

const currentFontFamily = ref("Inter, sans-serif");
const currentFontSize = ref("16px");
const currentColor = ref("#000000");
const currentHighlight = ref("#ffffff");

const filterAuthor = ref("");
const filterStatus = ref("all");
const filterDate = ref<string | null>(null);

const authorOptions = computed(() => {
  const set = new Set(comments.value.map(c => c.author_login));
  return Array.from(set);
});

const filteredComments = computed(() => {
  return comments.value.filter(c => {
    if (filterAuthor.value && c.author_login !== filterAuthor.value) return false;
    if (filterStatus.value !== "all" && c.status !== filterStatus.value) return false;
    if (filterDate.value && c.created_at && !c.created_at.startsWith(filterDate.value)) return false;
    return true;
  });
});

const threadedComments = computed(() => {
  const all = filteredComments.value;
  const roots = all.filter(c => !c.parent_id);
  const map: Record<number, any> = {};
  all.forEach(c => { map[c.id] = { ...c, replies: [] }; });
  all.forEach(c => {
    if (c.parent_id && map[c.parent_id]) {
      map[c.parent_id].replies.push(map[c.id]);
    }
  });
  return roots.map(r => map[r.id]);
});

const isOwner = computed(() => auth.user?.id === meta.value.owner_id);

const statusLabel = computed(() => {
  return t("common.status." + meta.value.status);
});

const statusTag = computed(() => {
  const s = meta.value.status;
  if (s === "approved") return "success";
  if (s === "rejected") return "danger";
  return s === "in_approval" ? "warning" : "info";
});

const filteredUserOptions = computed(() => {
  if (!auth.user) return userOptions.value;
  return userOptions.value.filter((u) => u.id !== auth.user!.id);
});


const ydoc = new Y.Doc();
const awareness = new Awareness(ydoc);
const userColor = `#${Math.floor(Math.random() * 0xffffff).toString(16).padStart(6, "0")}`;

let collabDisconnect: (() => void) | null = null;
const staticCollabs = ref<Array<{ name: string; color: string }>>([]);

function refreshCollabList() {
  if (meta.value.status === 'approved') return;
  const states = awareness.getStates();
  const list: Array<{ name: string; color: string }> = [];
  states.forEach((s) => {
    const u = s.user as any;
    if (u?.name) list.push({ name: u.name, color: u.color || "#888" });
  });
  collabColors.value = list;
}

const editor = useEditor({
  extensions: [
    StarterKit.configure({ history: false }),
    Underline, TextStyle, Color, FontFamily, CustomImage, Dropcursor, Gapcursor, TableRow, TableHeader, TableCell,
    Highlight.configure({ multicolor: true }),
    TextAlign.configure({ types: ["heading", "paragraph", "image"] }),
    Collaboration.configure({ document: ydoc }),
    CollaborationCursor.configure({ provider: { awareness } as never }),
    Table.configure({ resizable: true }),
    FontSize, LineHeight, Indent, CommentMark, TableExit, SearchAndReplace,
  ],
  editable: true,
  onUpdate: () => scheduleSave(),
  onSelectionUpdate: ({ editor }) => {
    currentFontFamily.value = editor.getAttributes('textStyle').fontFamily || "Inter, sans-serif";
    currentFontSize.value = editor.getAttributes('textStyle').fontSize || "16px";
  }
});

let saveTimer = 0;
function scheduleSave() {
  if (!meta.value.can_edit) return;
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => saveNow(), 2000);
}

function updateSearch() { (editor.value as any)?.commands.setSearchTerm(searchTerm.value); }
function doReplace() {
  (editor.value as any)?.commands.setReplaceTerm(replaceTerm.value);
  (editor.value as any)?.commands.replace();
}
function doReplaceAll() {
  (editor.value as any)?.commands.setReplaceTerm(replaceTerm.value);
  (editor.value as any)?.commands.replaceAll();
}

async function savePageSettings() {
  try {
    await api.patch(`/documents/${docId.value}`, { page_settings_json: JSON.stringify(page.value) });
    pageSettingsVisible.value = false;
    ElMessage.success(t("editor.pageSettingsSaved"));
  } catch { ElMessage.error(t("common.failed", "Failed")); }
}

function fixPunc() {
  if (!editor.value) return;
  editor.value.commands.setContent(fixPunctuation(editor.value.getText())); 
  ElMessage.success(t("editor.messages.punctuationFixed"));
}

async function startApproval() {
  if (!approverIds.value.length) return ElMessage.warning(t("editor.selectApprovers"));
  try {
    await api.post(`/documents/${docId.value}/approvals`, { type: approvalType.value, approvers: approverIds.value });
    showApproval.value = false;
    ElMessage.success(t("editor.approvalStarted"));
    loadDoc();
  } catch { ElMessage.error(t("editor.approvalFailed")); }
}

async function newVersion() {
  try {
    await api.post(`/documents/${docId.value}/new-version`);
    ElMessage.success(t("editor.newVersionOk"));
    loadDoc();
  } catch { ElMessage.error(t("common.failed", "Failed")); }
}

async function loadStaticCollaborators() {
  try {
    const { data } = await api.get(`/documents/${docId.value}/collaborators`);
    staticCollabs.value = data.items.map((item: any) => ({ name: item.name, color: "#888" }));
    if (meta.value.status === 'approved') collabColors.value = staticCollabs.value;
  } catch {}
}

async function loadVersions() {
  const { data } = await api.get(`/documents/${docId.value}/versions`);
  versionList.value = data.items;
}

async function loadDoc() {
  loading.value = true;
  try {
    const { data } = await api.get(`/documents/${docId.value}`);
    title.value = data.title;
    meta.value = data;
    if (data.page_settings_json) {
        try {
            const ps = typeof data.page_settings_json === 'string' 
                ? JSON.parse(data.page_settings_json) 
                : data.page_settings_json;
            Object.assign(page.value, ps);
        } catch (e) {
            console.error("解析页面设置失败:", e);
        }
    }
    editor.value?.setEditable(data.can_edit);
    if (data.yjs_state_b64) Y.applyUpdate(ydoc, Uint8Array.from(atob(data.yjs_state_b64), (c) => c.charCodeAt(0)));
    else if (data.content_json) {
      const j = typeof data.content_json === "string" ? JSON.parse(data.content_json) : data.content_json;
      await nextTick();
      editor.value?.commands.setContent(j);
    }
    collabDisconnect?.();
    collabDisconnect = attachDocCollab(docId.value, ydoc, awareness, { name: auth.user?.display_name || auth.user?.login_name || "User", color: userColor });
    awareness.on("update", refreshCollabList);
    await loadStaticCollaborators();
    if (meta.value.status !== 'approved') refreshCollabList();
    await loadComments();
    await loadVersions();
    const us = await api.get("/users");

    userOptions.value = us.data.items;
  } finally { loading.value = false; }
}

async function saveNow() {
  if (!editor.value || !meta.value.can_edit) return;
  saving.value = true;
  try {
    const content_json = editor.value.getJSON();
    const update = Y.encodeStateAsUpdate(ydoc);
    await api.put(`/documents/${docId.value}/content`, { content_json, yjs_state_b64: btoa(String.fromCharCode(...update)) });
    saveHint.value = t("editor.savedAt", { time: new Date().toLocaleTimeString() });
  } catch { saveHint.value = t("editor.saveFailed"); }
  finally { saving.value = false; }
}

async function saveTitle() { await api.patch(`/documents/${docId.value}`, { title: title.value }); }

async function loadComments() {
  const { data } = await api.get(`/documents/${docId.value}/comments`, { params: { hide_resolved: 0 } });
  comments.value = data.items;
}

async function resolveComment(id: number) {
  await api.patch(`/comments/${id}`, { status: "resolved" });
  loadComments();
}

async function replyTo(parentId: number) {
  const body = (replyMap.value[parentId] || "").trim();
  if (!body) return;
  await api.post(`/documents/${docId.value}/comments`, { body, parent_id: parentId });
  replyMap.value[parentId] = "";
  loadComments();
}

async function importDocx() {
  const input = document.createElement("input");
  input.type = "file"; input.accept = ".docx";
  input.onchange = async (e: any) => {
    const file = e.target.files[0]; if (!file) return;
    try {
      const result = await mammoth.convertToHtml({ arrayBuffer: await file.arrayBuffer() });
      editor.value?.commands.setContent(result.value);
      ElMessage.success(t("editor.messages.importSuccess"));
    } catch { ElMessage.error(t("editor.messages.importFailed")); }
  };
  input.click();
}

function insertImage() {
  const input = document.createElement("input");
  input.type = "file"; 
  input.accept = "image/*";
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]; 
    if (!file) return;
    
    const formData = new FormData(); 
    formData.append("file", file); 
    
    try {
      // 💡 修改 1：补全蓝图前缀 `/documents`
      // 💡 修改 2：加上 multipart/form-data 请求头
      const { data } = await api.post(`/documents/upload-image`, formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });
      // 插入图片到编辑器
      (editor.value?.chain().focus() as any).setImage({ src: data.url }).run();
    } catch (err: any) { 
      console.error("上传图片报错详情:", err.response || err);
      ElMessage.error(`图片上传失败: ${err.response?.status === 404 ? '接口不存在' : '后端断开连接'}`); 
    }
  };
  input.click();
}

async function insertCustomTable() {
  try {
    const { value: rs } = await ElMessageBox.prompt(t("editor.messages.insertTableRows"), t("editor.messages.insertTableTitle"), { inputPattern: /^[1-9][0-9]?$/, inputValue: "3", confirmButtonText: t("common.ok"), cancelButtonText: t("common.cancel") });
    const { value: cs } = await ElMessageBox.prompt(t("editor.messages.insertTableCols"), t("editor.messages.insertTableTitle"), { inputPattern: /^[1-9][0-9]?$/, inputValue: "3", confirmButtonText: t("common.ok"), cancelButtonText: t("common.cancel") });
    editor.value?.chain().focus().insertTable({ rows: parseInt(rs), cols: parseInt(cs), withHeaderRow: true }).run();
  } catch {}
}

function setFontSize(val: string) { (editor.value?.chain().focus() as any).setFontSize(val).run(); }
function setFontFamily(val: string) { (editor.value?.chain().focus() as any).setFontFamily(val).run(); }
function setTextColor(e: Event) { (editor.value?.chain().focus() as any).setColor((e.target as HTMLInputElement).value).run(); }
function setHighlight(e: Event) { (editor.value?.chain().focus() as any).toggleHighlight({ color: (e.target as HTMLInputElement).value }).run(); }
function doIndent() { (editor.value?.chain().focus() as any).indent().run(); }
function doOutdent() { (editor.value?.chain().focus() as any).outdent().run(); }
function scrollToComment(id: number) {
  const el = document.querySelector(`.tiptap span[data-comment-id="${id}"]`);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}


async function downloadDocx() {
  try {
    const res = await api.get(`/documents/${docId.value}/export.docx`, { responseType: 'blob' });
    const a = document.createElement("a"); a.href = URL.createObjectURL(res.data); a.download = `doc_${docId.value}.docx`; a.click();
    ElMessage.success(t("editor.exportDocx"));
  } catch { ElMessage.error(t("editor.exportFailed")); }
}
async function downloadPdf() {
  try {
    const res = await api.get(`/documents/${docId.value}/export.pdf`, { responseType: 'blob' });
    const a = document.createElement("a"); a.href = URL.createObjectURL(res.data); a.download = `doc_${docId.value}.pdf`; a.click();
    ElMessage.success(t("editor.exportPdf"));
  } catch { ElMessage.error(t("editor.exportFailed")); }
}

async function addCommentOnSelection() {
  if (!editor.value || editor.value.state.selection.empty) return ElMessage.warning(t("editor.selectTextFirst"));
  try {
    const { value: body } = await ElMessageBox.prompt(t("editor.commentPrompt"), t("editor.newCommentTitle"), { confirmButtonText: t("common.ok"), cancelButtonText: t("common.cancel") });
    if (body) {
      const { from, to } = editor.value.state.selection;
      const { data } = await api.post(`/documents/${docId.value}/comments`, { body, anchor_json: JSON.stringify({ from, to }) });
      (editor.value.chain().focus() as any).setComment(data.id).run();
      loadComments();
    }
  } catch {}
}
function setImgWidth(width: string) {
  if (editor.value) {
    editor.value.chain().focus().updateAttributes('image', { width }).run();
  }
}
onMounted(() => loadDoc());
onBeforeUnmount(() => { collabDisconnect?.(); awareness.off("update", refreshCollabList); editor.value?.destroy(); });
watch(() => route.params.id, () => loadDoc());
</script>

<style scoped>
.editor-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  background-color: var(--el-bg-color-page, #f5f7fa);
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: white;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.status-tag { margin-left: 8px; }
.hint { font-size: 12px; color: var(--el-text-color-secondary); }

.collab-avatars {
  display: flex;
  margin-right: 16px;
}
.avatar-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  border: 2px solid white;
  margin-left: -8px;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.avatar-dot:first-child { margin-left: 0; }

.editor-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 8px 16px;
  background-color: white;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.toolbar-divider {
  width: 1px;
  height: 24px;
  background-color: var(--el-border-color-lighter);
  margin: 0 4px;
}
.toolbar-group .el-button {
  padding: 5px 8px;
}
.toolbar-group .el-button.is-active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
}

.body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.main-wrapper {
  flex: 1;
  overflow: auto; /* 保证出现滚动条 */
  padding: 32px;
  display: flex;
  justify-content: center;
  align-items: flex-start; /* 关键1：顶部对齐，允许底部无限生长 */
}

.main-paper {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  min-height: 800px; /* 纸张的初始最小高度 */
  height: auto !important; /* 关键2：强制高度由内部文字撑开，覆盖之前的限制 */
  flex-shrink: 0; /* 关键3（最核心）：禁止这块白纸在 flex 容器中被压缩！！ */
  box-sizing: border-box;
  padding: 40px;
  padding-bottom: 80px; 
  transition: width 0.3s ease;
}

/* 分页符在编辑器里的长相 */
/* 让分页符变成“两张纸中间的物理灰色缝隙” */
:deep(hr.page-break) {
  border: none;
  /* 用和网页背景一样的灰色，制造“纸张断层”的视觉假象 */
  background-color: var(--el-bg-color-page, #f5f7fa);
  height: 40px; /* 两张纸之间的灰色距离 */
  margin: 40px -40px; /* 撑满整个白纸的宽度，抵消 padding */
  page-break-after: always;
  position: relative;
  clear: both;
  cursor: default;
  z-index: 1;
}

/* 模拟上一张纸的底部边缘和阴影 */
:deep(hr.page-break::before) {
  content: '';
  position: absolute;
  top: -1px;
  left: 0;
  right: 0;
  border-top: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 -2px 6px rgba(0,0,0,0.05);
}

/* 模拟下一张纸的顶部边缘和阴影 */
:deep(hr.page-break::after) {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.main-paper.A4 { width: 794px; }
.main-paper.Letter { width: 816px; min-height: 1056px; }
.main-paper.Legal { width: 816px; min-height: 1344px; }

.side {
  width: 320px;
  background-color: white;
  border-left: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
}
.comments-header {
  padding: 8px 16px;
}
.comment-filters {
  padding: 8px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background-color: #fafafa;
}
.comments-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
}

.comment-group { margin-bottom: 12px; }
.comment {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 12px;
  background-color: white;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.comment:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.comment.resolved { opacity: 0.6; }
.meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}
.comment-body { margin-bottom: 8px; font-size: 14px; }

.replies {
  margin-left: 20px;
  border-left: 2px solid #f0f0f0;
  padding-left: 12px;
  margin-top: 4px;
}
.comment.reply {
  padding: 8px 10px;
  margin-top: 4px;
  font-size: 13px;
  background-color: #fafafa;
}
.comment.reply .comment-body { margin-bottom: 0; }

.version-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.version-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
}
.version-items {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}
.version-item {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: default;
}
.v-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}
.v-no { font-weight: bold; color: var(--el-color-primary); }
.v-user { font-size: 12px; color: var(--el-text-color-secondary); }
.v-time { font-size: 11px; color: var(--el-text-color-placeholder); }

.tiptap { outline: none; }
.tiptap :deep(.ProseMirror) {
  outline: none;
  min-height: 100%;
  height: auto !important; /* 关键4：确保 Tiptap 编辑器本身高度能自动增长 */
}
.tiptap :deep(table) {
  border-collapse: collapse;
  table-layout: fixed;
  width: 100%;
  margin: 0;
  overflow: hidden;
}
.tiptap :deep(table td), .tiptap :deep(table th) {
  min-width: 1em;
  border: 1px solid var(--el-border-color-darker);
  padding: 3px 5px;
  vertical-align: top;
  box-sizing: border-box;
  position: relative;
}
.tiptap :deep(.search-result) { background-color: #ffde5e; }

.search-bar {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  background-color: #f0f2f5;
  border-bottom: 1px solid var(--el-border-color-lighter);
  align-items: center;
}

.tiptap :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  display: block;
}
.tiptap :deep(img[style*="text-align: center"]) {
  margin-left: auto;
  margin-right: auto;
}
.tiptap :deep(img[style*="text-align: right"]) {
  margin-left: auto;
  margin-right: 0;
}
.tiptap :deep(img[style*="text-align: left"]) {
  margin-right: auto;
  margin-left: 0;
}
.tiptap :deep(img.ProseMirror-selectednode) {
  outline: 3px solid var(--el-color-primary);
}
</style>
